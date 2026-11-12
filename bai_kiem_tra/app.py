import os
from datetime import date

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, UniqueConstraint, func, or_, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    books: Mapped[list["Book"]] = relationship(back_populates="category")


class Book(db.Model):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("isbn", name="uq_books_isbn"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(120), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    published_year: Mapped[int | None] = mapped_column(nullable=True)
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    category_id: Mapped[int] = mapped_column(
        db.ForeignKey("categories.id"), nullable=False
    )
    category: Mapped[Category] = relationship(back_populates="books")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-library-app-key"),
        SQLALCHEMY_DATABASE_URI="sqlite:///library.sqlite3",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    @app.get("/")
    def dashboard():
        category_count = db.session.scalar(
            select(func.count()).select_from(Category)
        )
        book_count = db.session.scalar(select(func.count()).select_from(Book))
        total_copies = db.session.scalar(
            select(func.coalesce(func.sum(Book.quantity), 0))
        )
        recent_books = db.session.scalars(
            select(Book)
            .options(selectinload(Book.category))
            .order_by(Book.id.desc())
            .limit(5)
        ).all()
        return render_template(
            "dashboard.html",
            category_count=category_count,
            book_count=book_count,
            total_copies=total_copies,
            recent_books=recent_books,
        )

    @app.get("/categories")
    def category_list():
        categories = db.session.scalars(
            select(Category).order_by(Category.name)
        ).all()
        return render_template("categories.html", categories=categories)

    @app.route("/categories/new", methods=["GET", "POST"])
    def category_create():
        return save_category()

    @app.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
    def category_edit(category_id):
        category = db.get_or_404(Category, category_id)
        return save_category(category)

    def save_category(category=None):
        values = {
            "name": category.name if category else "",
            "description": category.description if category else "",
        }
        if request.method == "POST":
            values = {
                "name": request.form.get("name", "").strip(),
                "description": request.form.get("description", "").strip(),
            }
            if not values["name"]:
                flash("Vui lòng nhập tên danh mục.", "danger")
            else:
                conditions = [
                    func.lower(Category.name) == values["name"].lower()
                ]
                if category:
                    conditions.append(Category.id != category.id)
                duplicate = db.session.scalar(
                    select(Category).where(*conditions)
                )
                if duplicate:
                    flash("Tên danh mục này đã tồn tại.", "danger")
                else:
                    if category is None:
                        category = Category()
                        db.session.add(category)
                    category.name = values["name"]
                    category.description = values["description"]
                    db.session.commit()
                    flash("Đã lưu danh mục.", "success")
                    return redirect(url_for("category_list"))

        return render_template(
            "category_form.html",
            category=category,
            values=values,
        ), 400 if request.method == "POST" else 200

    @app.post("/categories/<int:category_id>/delete")
    def category_delete(category_id):
        category = db.get_or_404(Category, category_id)
        if category.books:
            flash("Danh mục đang có sách, hãy chuyển hoặc xóa sách trước.", "warning")
        else:
            db.session.delete(category)
            db.session.commit()
            flash("Đã xóa danh mục.", "success")
        return redirect(url_for("category_list"))

    @app.get("/books")
    def book_list():
        search_text = request.args.get("q", "").strip()
        selected_category = request.args.get("category", type=int)
        statement = select(Book).join(Book.category).options(selectinload(Book.category))
        if search_text:
            pattern = f"%{search_text}%"
            statement = statement.where(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.isbn.ilike(pattern),
                )
            )
        if selected_category:
            statement = statement.where(Book.category_id == selected_category)
        books = db.session.scalars(statement.order_by(Book.id.desc())).all()
        categories = db.session.scalars(
            select(Category).order_by(Category.name)
        ).all()
        return render_template(
            "books.html",
            books=books,
            categories=categories,
            search_text=search_text,
            selected_category=selected_category,
        )

    @app.route("/books/new", methods=["GET", "POST"])
    def book_create():
        return save_book()

    @app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
    def book_edit(book_id):
        book = db.get_or_404(Book, book_id)
        return save_book(book)

    def save_book(book=None):
        categories = db.session.scalars(
            select(Category).order_by(Category.name)
        ).all()
        if not categories:
            flash("Hãy tạo ít nhất một danh mục trước khi thêm sách.", "warning")
            return redirect(url_for("category_create"))

        values = {
            "title": book.title if book else "",
            "author": book.author if book else "",
            "isbn": book.isbn or "" if book else "",
            "published_year": str(book.published_year or "") if book else "",
            "quantity": str(book.quantity) if book else "0",
            "category_id": str(book.category_id) if book else "",
        }
        if request.method == "POST":
            values = {
                "title": request.form.get("title", "").strip(),
                "author": request.form.get("author", "").strip(),
                "isbn": request.form.get("isbn", "").strip(),
                "published_year": request.form.get("published_year", "").strip(),
                "quantity": request.form.get("quantity", "").strip(),
                "category_id": request.form.get("category_id", "").strip(),
            }
            year = None
            quantity = None
            category_id = None
            error = None
            if not values["title"] or not values["author"]:
                error = "Vui lòng nhập tên sách và tác giả."
            elif values["published_year"]:
                try:
                    year = int(values["published_year"])
                    if not 1000 <= year <= date.today().year:
                        error = f"Năm xuất bản phải từ 1000 đến {date.today().year}."
                except ValueError:
                    error = "Năm xuất bản phải là số nguyên."
            if error is None:
                try:
                    quantity = int(values["quantity"])
                    if quantity < 0:
                        error = "Số lượng không được âm."
                except ValueError:
                    error = "Số lượng phải là số nguyên không âm."
            if error is None:
                try:
                    category_id = int(values["category_id"])
                except ValueError:
                    error = "Vui lòng chọn danh mục."
            if error is None and not any(
                category.id == category_id for category in categories
            ):
                error = "Danh mục đã chọn không tồn tại."
            if error is None and values["isbn"]:
                isbn_conditions = [
                    func.lower(Book.isbn) == values["isbn"].lower()
                ]
                if book:
                    isbn_conditions.append(Book.id != book.id)
                duplicate_isbn = db.session.scalar(
                    select(Book).where(*isbn_conditions)
                )
                if duplicate_isbn:
                    error = "ISBN này đã được sử dụng."

            if error:
                flash(error, "danger")
            else:
                if book is None:
                    book = Book()
                    db.session.add(book)
                book.title = values["title"]
                book.author = values["author"]
                book.isbn = values["isbn"] or None
                book.published_year = year
                book.quantity = quantity
                book.category_id = category_id
                db.session.commit()
                flash("Đã lưu thông tin sách.", "success")
                return redirect(url_for("book_list"))

        return render_template(
            "book_form.html",
            book=book,
            categories=categories,
            values=values,
            current_year=date.today().year,
        ), 400 if request.method == "POST" else 200

    @app.post("/books/<int:book_id>/delete")
    def book_delete(book_id):
        book = db.get_or_404(Book, book_id)
        db.session.delete(book)
        db.session.commit()
        flash("Đã xóa sách.", "success")
        return redirect(url_for("book_list"))

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    with app.app_context():
        db.create_all()

    return app


app = create_app()
