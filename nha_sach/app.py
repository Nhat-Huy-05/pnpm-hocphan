import os
import uuid
from datetime import datetime, date

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.csrf import CSRFProtect, generate_csrf
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey, func, case
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from wtforms import (
    StringField, IntegerField, DecimalField, TextAreaField,
    SelectField, RadioField, validators
)
from wtforms.validators import DataRequired, Optional, NumberRange, Email, Regexp, Length, ValidationError
from PIL import Image


# ── Base & DB ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nha_sach.db"
app.config["SECRET_KEY"] = "nha-sach-song-huong-secret-key-2024"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads", "covers")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB
app.config["WTF_CSRF_ENABLED"] = True

db.init_app(app)
csrf = CSRFProtect(app)


# ── Models ───────────────────────────────────────────────────────────────────

class Category(db.Model):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    books: Mapped[list["Book"]] = relationship("Book", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Book(db.Model):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # VND, int
    stock: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    cover_image: Mapped[str | None] = mapped_column(String(300))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    category: Mapped["Category | None"] = relationship("Category", back_populates="books")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="book")

    @property
    def cover_url(self):
        if self.cover_image:
            return url_for("static", filename=f"uploads/covers/{self.cover_image}")
        return url_for("static", filename="img/no_cover.png")

    def __repr__(self):
        return f"<Book {self.title}>"


ORDER_STATUSES = ["Chờ xác nhận", "Đang giao", "Hoàn tất", "Đã huỷ"]
STATUS_COLORS = {
    "Chờ xác nhận": "warning",
    "Đang giao": "info",
    "Hoàn tất": "success",
    "Đã huỷ": "danger",
}
VALID_TRANSITIONS = {
    "Chờ xác nhận": ["Đang giao", "Đã huỷ"],
    "Đang giao": ["Hoàn tất", "Đã huỷ"],
    "Hoàn tất": [],
    "Đã huỷ": [],
}


class Order(db.Model):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Chờ xác nhận")
    shipping_fee: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    history: Mapped[list["OrderHistory"]] = relationship(
        "OrderHistory", back_populates="order", cascade="all, delete-orphan",
        order_by="OrderHistory.changed_at"
    )

    @property
    def subtotal(self):
        return sum(item.unit_price * item.quantity for item in self.items)

    @property
    def total(self):
        return self.subtotal + self.shipping_fee

    @property
    def status_color(self):
        return STATUS_COLORS.get(self.status, "secondary")

    def __repr__(self):
        return f"<Order #{self.id}>"


class OrderItem(db.Model):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    book: Mapped["Book"] = relationship("Book", back_populates="order_items")

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class OrderHistory(db.Model):
    __tablename__ = "order_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    order: Mapped["Order"] = relationship("Order", back_populates="history")


# ── Forms ────────────────────────────────────────────────────────────────────

class CheckoutForm(FlaskForm):
    customer_name = StringField("Họ tên", validators=[DataRequired("Vui lòng nhập họ tên.")])
    phone = StringField("Số điện thoại", validators=[
        DataRequired("Vui lòng nhập số điện thoại."),
        Regexp(r"^0\d{9}$", message="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")
    ])
    email = StringField("Email", validators=[Optional(), Email("Email không hợp lệ.")])
    address = StringField("Địa chỉ giao hàng", validators=[DataRequired("Vui lòng nhập địa chỉ.")])
    note = TextAreaField("Ghi chú", validators=[Optional()])
    payment_method = RadioField(
        "Thanh toán",
        choices=[("Tiền mặt khi nhận hàng", "Tiền mặt khi nhận hàng"),
                 ("Chuyển khoản", "Chuyển khoản")],
        default="Tiền mặt khi nhận hàng",
        validators=[DataRequired()]
    )


class BookForm(FlaskForm):
    title = StringField("Tên sách", validators=[DataRequired("Vui lòng nhập tên sách."), Length(max=200)])
    author = StringField("Tác giả", validators=[DataRequired("Vui lòng nhập tác giả."), Length(max=200)])
    publisher = StringField("NXB", validators=[Optional(), Length(max=200)])
    year = IntegerField("Năm xuất bản", validators=[
        Optional(),
        NumberRange(min=1900, max=date.today().year, message=f"Năm từ 1900 đến {date.today().year}.")
    ])
    price = IntegerField("Giá (đồng)", validators=[
        DataRequired("Vui lòng nhập giá."),
        NumberRange(min=1000, message="Giá phải từ 1.000 đồng trở lên.")
    ])
    stock = IntegerField("Tồn kho", validators=[
        DataRequired("Vui lòng nhập tồn kho."),
        NumberRange(min=0, message="Tồn kho không âm.")
    ])
    description = TextAreaField("Mô tả", validators=[Optional()])
    category_id = SelectField("Danh mục", coerce=int, validators=[Optional()])
    cover = FileField("Ảnh bìa", validators=[
        Optional(),
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Chỉ chấp nhận JPG, PNG, WEBP.")
    ])

    def validate_title(self, field):
        book_id = getattr(self, '_book_id', None)
        q = db.select(Book).where(func.lower(Book.title) == field.data.lower().strip())
        if book_id:
            q = q.where(Book.id != book_id)
        existing = db.session.scalar(q)
        if existing:
            raise ValidationError("Tên sách đã tồn tại.")


class CategoryForm(FlaskForm):
    name = StringField("Tên danh mục", validators=[DataRequired("Vui lòng nhập tên."), Length(max=100)])
    description = TextAreaField("Mô tả", validators=[Optional()])

    def validate_name(self, field):
        cat_id = getattr(self, '_cat_id', None)
        q = db.select(Category).where(func.lower(Category.name) == field.data.lower().strip())
        if cat_id:
            q = q.where(Category.id != cat_id)
        existing = db.session.scalar(q)
        if existing:
            raise ValidationError("Danh mục đã tồn tại.")


class OrderStatusForm(FlaskForm):
    new_status = SelectField("Trạng thái mới", choices=[])


class DeleteForm(FlaskForm):
    """Empty form chỉ để có CSRF token."""
    pass


# ── Helpers ──────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
FREE_SHIPPING_THRESHOLD = 200_000
SHIPPING_FEE = 20_000


def save_cover(file_storage, old_filename=None):
    """Lưu ảnh bìa, trả về filename mới. Xoá ảnh cũ nếu có."""
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_name)
    img = Image.open(file_storage)
    img.save(save_path, optimize=True)
    if old_filename:
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)
    return new_name


def get_cart():
    """Trả về {book_id: quantity} từ session."""
    return session.get("cart", {})


def set_cart(cart):
    session["cart"] = cart
    session.modified = True


def cart_total_qty():
    return sum(get_cart().values())


def get_cart_items():
    """Trả về list dict với thông tin đầy đủ từ CSDL."""
    cart = get_cart()
    if not cart:
        return []
    book_ids = [int(k) for k in cart.keys()]
    books = db.session.execute(
        db.select(Book).where(Book.id.in_(book_ids))
    ).scalars().all()
    book_map = {b.id: b for b in books}
    items = []
    for bid_str, qty in cart.items():
        bid = int(bid_str)
        book = book_map.get(bid)
        if book:
            items.append({"book": book, "quantity": qty, "subtotal": book.price * qty})
    return items


def calc_shipping(subtotal):
    return 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE


app.jinja_env.globals["cart_total_qty"] = cart_total_qty
app.jinja_env.globals["STATUS_COLORS"] = STATUS_COLORS
app.jinja_env.globals["csrf_token"] = generate_csrf


# ── Context processor ─────────────────────────────────────────────────────────

@app.context_processor
def inject_pending_count():
    try:
        count = db.session.scalar(
            db.select(func.count(Order.id)).where(Order.status == "Chờ xác nhận")
        )
    except Exception:
        count = 0
    return {"pending_order_count": count or 0}


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN A — TRANG BÁN HÀNG
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def index():
    return redirect(url_for("books"))


@app.get("/books")
def books():
    q = request.args.get("q", "").strip()
    cat_id = request.args.get("cat", "")
    categories = db.session.execute(db.select(Category).order_by(Category.name)).scalars().all()

    stmt = db.select(Book)
    if q:
        stmt = stmt.where(
            (Book.title.ilike(f"%{q}%")) | (Book.author.ilike(f"%{q}%"))
        )
    if cat_id:
        stmt = stmt.where(Book.category_id == int(cat_id))
    stmt = stmt.order_by(Book.id)

    all_books = db.session.execute(stmt).scalars().all()
    return render_template("books.html", books=all_books, categories=categories, q=q, cat_id=cat_id)


@app.get("/books/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    cart = get_cart()
    in_cart = cart.get(str(book_id), 0)
    max_qty = book.stock - in_cart
    return render_template("book_detail.html", book=book, in_cart=in_cart, max_qty=max_qty)


@app.post("/cart/add/<int:book_id>")
def add_to_cart(book_id):
    book = db.get_or_404(Book, book_id)
    try:
        qty = int(request.form.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1

    cart = get_cart()
    current_qty = cart.get(str(book_id), 0)
    max_allowed = book.stock - current_qty

    if book.stock == 0:
        flash("Sách đã hết hàng.", "danger")
    elif qty < 1 or qty > max_allowed:
        flash(f"Số lượng không hợp lệ (tối đa có thể thêm {max_allowed}).", "danger")
    else:
        cart[str(book_id)] = current_qty + qty
        set_cart(cart)
        flash(f"✓ Đã thêm {qty} × {book.title} vào giỏ hàng.", "success")

    next_url = request.form.get("next") or url_for("books")
    return redirect(next_url)


@app.get("/cart")
def cart():
    items = get_cart_items()
    subtotal = sum(i["subtotal"] for i in items)
    shipping = calc_shipping(subtotal)
    delete_form = DeleteForm()
    return render_template("cart.html", items=items, subtotal=subtotal,
                           shipping=shipping, total=subtotal + shipping,
                           delete_form=delete_form)


@app.post("/cart/update/<int:book_id>")
def update_cart(book_id):
    book = db.get_or_404(Book, book_id)
    action = request.form.get("action")
    cart = get_cart()
    key = str(book_id)
    qty = cart.get(key, 0)

    if action == "increase":
        if qty < book.stock:
            cart[key] = qty + 1
    elif action == "decrease":
        if qty > 1:
            cart[key] = qty - 1
        else:
            cart.pop(key, None)
    elif action == "remove":
        cart.pop(key, None)

    set_cart(cart)
    return redirect(url_for("cart"))


@app.post("/cart/clear")
def clear_cart():
    set_cart({})
    flash("Đã xoá toàn bộ giỏ hàng.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart_data = get_cart()
    if not cart_data:
        flash("Giỏ hàng trống, vui lòng thêm sách trước.", "warning")
        return redirect(url_for("cart"))

    items = get_cart_items()
    subtotal = sum(i["subtotal"] for i in items)
    shipping = calc_shipping(subtotal)
    form = CheckoutForm()

    if form.validate_on_submit():
        # Kiểm tra lại tồn kho
        for item in items:
            if item["book"].stock < item["quantity"]:
                flash(
                    f"Sách \"{item['book'].title}\" không đủ hàng "
                    f"(còn {item['book'].stock}, yêu cầu {item['quantity']}).",
                    "danger"
                )
                return redirect(url_for("cart"))

        order = Order(
            customer_name=form.customer_name.data,
            phone=form.phone.data,
            email=form.email.data or None,
            address=form.address.data,
            note=form.note.data or None,
            payment_method=form.payment_method.data,
            status="Chờ xác nhận",
            shipping_fee=shipping,
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        for item in items:
            oi = OrderItem(
                order_id=order.id,
                book_id=item["book"].id,
                unit_price=item["book"].price,
                quantity=item["quantity"],
            )
            db.session.add(oi)
            item["book"].stock -= item["quantity"]

        hist = OrderHistory(order_id=order.id, status="Chờ xác nhận")
        db.session.add(hist)
        db.session.commit()

        set_cart({})
        flash(f"✓ Đặt hàng thành công! Mã đơn #{order.id}.", "success")
        return redirect(url_for("order_success", order_id=order.id))

    return render_template("checkout.html", form=form, items=items,
                           subtotal=subtotal, shipping=shipping,
                           total=subtotal + shipping)


@app.get("/orders/<int:order_id>")
def order_success(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("order_success.html", order=order)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN B — TRANG QUẢN TRỊ
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/admin")
def admin_index():
    book_count = db.session.scalar(db.select(func.count(Book.id))) or 0
    pending_count = db.session.scalar(
        db.select(func.count(Order.id)).where(Order.status == "Chờ xác nhận")
    ) or 0
    now = datetime.utcnow()
    monthly_revenue = db.session.scalar(
        db.select(func.sum(Order.shipping_fee + 0)).where(  # placeholder; computed below
            Order.status == "Hoàn tất"
        )
    )
    # Doanh thu tháng = tổng (subtotal + shipping) đơn Hoàn tất trong tháng
    completed_orders_month = db.session.execute(
        db.select(Order).where(
            Order.status == "Hoàn tất",
            func.strftime("%Y-%m", Order.created_at) == now.strftime("%Y-%m")
        )
    ).scalars().all()
    monthly_revenue = sum(o.total for o in completed_orders_month)

    low_stock_count = db.session.scalar(
        db.select(func.count(Book.id)).where(Book.stock <= 5)
    ) or 0

    recent_orders = db.session.execute(
        db.select(Order).order_by(Order.id.desc()).limit(5)
    ).scalars().all()

    low_stock_books = db.session.execute(
        db.select(Book).where(Book.stock <= 5).order_by(Book.stock)
    ).scalars().all()

    # Doanh thu 7 ngày (tổng đơn Hoàn tất)
    from datetime import timedelta
    today = date.today()
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        label = d.strftime("%d/%m")
        total_day = db.session.scalar(
            db.select(func.count(Order.id)).where(
                Order.status == "Hoàn tất",
                func.date(Order.created_at) == d.isoformat()
            )
        ) or 0
        chart_labels.append(label)
        chart_data.append(total_day)

    return render_template("admin/index.html",
                           book_count=book_count,
                           pending_count=pending_count,
                           monthly_revenue=monthly_revenue,
                           low_stock_count=low_stock_count,
                           recent_orders=recent_orders,
                           low_stock_books=low_stock_books,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           STATUS_COLORS=STATUS_COLORS)


# ── Admin: Books ─────────────────────────────────────────────────────────────

@app.get("/admin/books")
def admin_books():
    q = request.args.get("q", "").strip()
    cat_id = request.args.get("cat", "")
    stock_filter = request.args.get("stock", "")
    page = request.args.get("page", 1, type=int)

    stmt = db.select(Book).order_by(Book.id.desc())
    if q:
        stmt = stmt.where(
            (Book.title.ilike(f"%{q}%")) | (Book.author.ilike(f"%{q}%"))
        )
    if cat_id:
        stmt = stmt.where(Book.category_id == int(cat_id))
    if stock_filter == "available":
        stmt = stmt.where(Book.stock > 5)
    elif stock_filter == "low":
        stmt = stmt.where(Book.stock > 0, Book.stock <= 5)
    elif stock_filter == "out":
        stmt = stmt.where(Book.stock == 0)

    all_books = db.session.execute(stmt).scalars().all()
    per_page = 5
    total = len(all_books)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    paged_books = all_books[(page - 1) * per_page: page * per_page]

    categories = db.session.execute(db.select(Category).order_by(Category.name)).scalars().all()
    delete_form = DeleteForm()

    # Sách đã có trong đơn hàng (không xoá được)
    booked_ids = set(
        row[0] for row in db.session.execute(
            db.select(OrderItem.book_id).distinct()
        ).all()
    )

    return render_template("admin/books.html",
                           books=paged_books, categories=categories,
                           q=q, cat_id=cat_id, stock_filter=stock_filter,
                           page=page, total_pages=total_pages, total=total,
                           delete_form=delete_form, booked_ids=booked_ids)


@app.route("/admin/books/new", methods=["GET", "POST"])
def admin_book_new():
    form = BookForm()
    _load_category_choices(form)
    if form.validate_on_submit():
        cover_name = None
        if form.cover.data:
            cover_name = save_cover(form.cover.data)
        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            publisher=form.publisher.data.strip() or None,
            year=form.year.data,
            price=form.price.data,
            stock=form.stock.data,
            description=form.description.data or None,
            category_id=form.category_id.data or None,
            cover_image=cover_name,
        )
        db.session.add(book)
        db.session.commit()
        flash(f"✓ Đã thêm sách \"{book.title}\".", "success")
        return redirect(url_for("admin_books"))
    return render_template("admin/book_form.html", form=form, book=None)


@app.route("/admin/books/<int:book_id>/edit", methods=["GET", "POST"])
def admin_book_edit(book_id):
    book = db.get_or_404(Book, book_id)
    form = BookForm(obj=book)
    form._book_id = book_id
    _load_category_choices(form)

    if form.validate_on_submit():
        old_cover = book.cover_image
        if form.cover.data:
            book.cover_image = save_cover(form.cover.data, old_filename=old_cover)
        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.publisher = form.publisher.data.strip() or None
        book.year = form.year.data
        book.price = form.price.data
        book.stock = form.stock.data
        book.description = form.description.data or None
        book.category_id = form.category_id.data or None
        db.session.commit()
        flash(f"✓ Đã cập nhật \"{book.title}\".", "success")
        return redirect(url_for("admin_books"))
    return render_template("admin/book_form.html", form=form, book=book)


@app.post("/admin/books/<int:book_id>/delete")
def admin_book_delete(book_id):
    book = db.get_or_404(Book, book_id)
    has_order = db.session.scalar(
        db.select(func.count(OrderItem.id)).where(OrderItem.book_id == book_id)
    )
    if has_order:
        flash(f"Không thể xoá \"{book.title}\": sách đã có trong đơn hàng.", "danger")
        return redirect(url_for("admin_books"))
    if book.cover_image:
        p = os.path.join(app.config["UPLOAD_FOLDER"], book.cover_image)
        if os.path.exists(p):
            os.remove(p)
    db.session.delete(book)
    db.session.commit()
    flash(f"Đã xoá sách \"{book.title}\".", "info")
    return redirect(url_for("admin_books"))


def _load_category_choices(form):
    cats = db.session.execute(db.select(Category).order_by(Category.name)).scalars().all()
    form.category_id.choices = [(0, "— Không có —")] + [(c.id, c.name) for c in cats]


# ── Admin: Categories ─────────────────────────────────────────────────────────

@app.route("/admin/categories", methods=["GET", "POST"])
def admin_categories():
    form = CategoryForm()
    edit_id = request.args.get("edit", type=int)
    edit_cat = db.session.get(Category, edit_id) if edit_id else None

    if edit_cat:
        form._cat_id = edit_cat.id
        if request.method == "GET":
            form.name.data = edit_cat.name
            form.description.data = edit_cat.description

    if form.validate_on_submit():
        if edit_cat:
            edit_cat.name = form.name.data.strip()
            edit_cat.description = form.description.data or None
            db.session.commit()
            flash(f"✓ Đã cập nhật danh mục \"{edit_cat.name}\".", "success")
        else:
            cat = Category(name=form.name.data.strip(), description=form.description.data or None)
            db.session.add(cat)
            db.session.commit()
            flash(f"✓ Đã thêm danh mục \"{cat.name}\".", "success")
        return redirect(url_for("admin_categories"))

    # Danh sách kèm số sách
    rows = db.session.execute(
        db.select(Category, func.count(Book.id).label("book_count"))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.name)
    ).all()
    delete_form = DeleteForm()
    return render_template("admin/categories.html",
                           rows=rows, form=form, edit_cat=edit_cat,
                           delete_form=delete_form)


@app.post("/admin/categories/<int:cat_id>/delete")
def admin_category_delete(cat_id):
    cat = db.get_or_404(Category, cat_id)
    book_count = db.session.scalar(
        db.select(func.count(Book.id)).where(Book.category_id == cat_id)
    )
    if book_count:
        flash(f"Không thể xoá \"{cat.name}\": còn {book_count} sách.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash(f"Đã xoá danh mục \"{cat.name}\".", "info")
    return redirect(url_for("admin_categories"))


# ── Admin: Orders ─────────────────────────────────────────────────────────────

@app.get("/admin/orders")
def admin_orders():
    status_filter = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    # Đếm theo trạng thái
    status_counts = {row[0]: row[1] for row in db.session.execute(
        db.select(Order.status, func.count(Order.id)).group_by(Order.status)
    ).all()}
    total_count = sum(status_counts.values())

    stmt = db.select(Order).order_by(Order.id.desc())
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    if q:
        stmt = stmt.where(
            (Order.customer_name.ilike(f"%{q}%")) |
            (Order.phone.ilike(f"%{q}%")) |
            (func.cast(Order.id, String).like(f"%{q}%"))
        )

    all_orders = db.session.execute(stmt).scalars().all()
    per_page = 10
    total = len(all_orders)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    paged = all_orders[(page - 1) * per_page: page * per_page]

    # Tổng giá trị bộ lọc hiện tại
    filter_total = sum(o.total for o in all_orders)

    return render_template("admin/orders.html",
                           orders=paged,
                           status_filter=status_filter, q=q,
                           page=page, total_pages=total_pages, total=total,
                           status_counts=status_counts, total_count=total_count,
                           filter_total=filter_total,
                           ORDER_STATUSES=ORDER_STATUSES,
                           STATUS_COLORS=STATUS_COLORS)


@app.route("/admin/orders/<int:order_id>", methods=["GET", "POST"])
def admin_order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    allowed_next = VALID_TRANSITIONS.get(order.status, [])

    form = OrderStatusForm()
    form.new_status.choices = [(s, s) for s in allowed_next]
    cancel_form = DeleteForm()

    if form.validate_on_submit() and allowed_next:
        new_status = form.new_status.data
        if new_status in allowed_next:
            order.status = new_status
            hist = OrderHistory(order_id=order.id, status=new_status)
            db.session.add(hist)
            db.session.commit()
            flash(f"✓ Đã cập nhật trạng thái sang \"{new_status}\".", "success")
        else:
            flash("Chuyển trạng thái không hợp lệ.", "danger")
        return redirect(url_for("admin_order_detail", order_id=order_id))

    return render_template("admin/order_detail.html",
                           order=order, form=form,
                           cancel_form=cancel_form,
                           allowed_next=allowed_next,
                           STATUS_COLORS=STATUS_COLORS)


@app.post("/admin/orders/<int:order_id>/cancel")
def admin_order_cancel(order_id):
    order = db.get_or_404(Order, order_id)
    if order.status not in ("Chờ xác nhận", "Đang giao"):
        flash("Không thể huỷ đơn này.", "danger")
        return redirect(url_for("admin_order_detail", order_id=order_id))
    # Hoàn tồn kho
    for item in order.items:
        item.book.stock += item.quantity
    order.status = "Đã huỷ"
    hist = OrderHistory(order_id=order.id, status="Đã huỷ")
    db.session.add(hist)
    db.session.commit()
    flash(f"Đã huỷ đơn #{order.id} và hoàn tồn kho.", "info")
    return redirect(url_for("admin_order_detail", order_id=order_id))


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(413)
def file_too_large(e):
    flash("Ảnh quá lớn (tối đa 2 MB).", "danger")
    return redirect(request.referrer or url_for("admin_books"))


# ── Seed data ─────────────────────────────────────────────────────────────────

@app.get("/seed")
def seed():
    if db.session.scalar(db.select(func.count(Book.id))):
        return "Dữ liệu đã có, không seed lại."

    cats = [
        Category(name="Lập trình", description="Sách về lập trình"),
        Category(name="Cơ sở dữ liệu", description="Sách về CSDL"),
        Category(name="Công cụ", description="Công cụ phát triển phần mềm"),
        Category(name="Mạng", description="Mạng máy tính"),
        Category(name="Kỹ năng lập trình", description="Clean code, design patterns"),
        Category(name="Thiết kế", description="Thiết kế phần mềm"),
    ]
    db.session.add_all(cats)
    db.session.flush()

    cat_map = {c.name: c.id for c in cats}
    books = [
        Book(title="Lập trình Python cơ bản", author="Nguyễn Văn A",
             publisher="NXB Đại học Huế", year=2024,
             price=95000, stock=30, category_id=cat_map["Lập trình"],
             description="Giới thiệu Python từ cơ bản đến nâng cao."),
        Book(title="Giáo trình Flask", author="Miguel Grinberg",
             publisher="O'Reilly", year=2018,
             price=120000, stock=20, category_id=cat_map["Lập trình"],
             description="Phát triển ứng dụng web với Flask."),
        Book(title="Cơ sở dữ liệu", author="Trần Văn B",
             publisher="NXB Giáo dục", year=2020,
             price=85000, stock=0, category_id=cat_map["Cơ sở dữ liệu"],
             description="Lý thuyết và thực hành CSDL quan hệ."),
        Book(title="Pro Git", author="Scott Chacon",
             publisher="Apress", year=2014,
             price=150000, stock=15, category_id=cat_map["Công cụ"],
             description="Toàn tập về Git."),
        Book(title="Mạng máy tính", author="Lê Văn C",
             publisher="NXB Khoa học", year=2019,
             price=110000, stock=12, category_id=cat_map["Mạng"],
             description="Các nguyên lý mạng máy tính."),
        Book(title="Clean Code", author="Robert C. Martin",
             publisher="Prentice Hall", year=2008,
             price=180000, stock=5, category_id=cat_map["Kỹ năng lập trình"],
             description="Viết code sạch và dễ bảo trì."),
    ]
    db.session.add_all(books)
    db.session.commit()
    return f"Đã seed {len(cats)} danh mục và {len(books)} sách."


with app.app_context():
    db.create_all()
