from flask import Flask, request, abort, url_for
from markupsafe import escape

app = Flask(__name__)

# MỤC 1: Dữ liệu BOOKS
BOOKS = [
    {
        "id": 1,
        "title": "Lập trình Python",
        "author": "Nguyễn Văn A",
        "year": 2024,
        "category": "Lập trình",
        "available": True,
    },
    {
        "id": 2,
        "title": "Flask cơ bản",
        "author": "Nguyễn Văn B",
        "year": 2025,
        "category": "Lập trình",
        "available": True,
    },
    {
        "id": 3,
        "title": "Cơ sở dữ liệu",
        "author": "Trần Văn C",
        "year": 2023,
        "category": "Cơ sở dữ liệu",
        "available": False,
    },
    {
        "id": 4,
        "title": "Git và GitHub",
        "author": "Lê Văn D",
        "year": 2025,
        "category": "Công cụ",
        "available": True,
    },
]


def find_book(book_id):
    return next((book for book in BOOKS if book["id"] == book_id), None)


# MỤC 2: Trang chủ
@app.route("/")
def index():
    total_books = len(BOOKS)
    available_books = sum(book["available"] for book in BOOKS)

    return f"""
        <h1>LibraryMS</h1>
        <p>Tổng số đầu sách: {escape(total_books)}</p>
        <p>Số sách sẵn sàng cho mượn: {escape(available_books)}</p>
        <nav>
            <a href="{escape(url_for('books'))}">Danh sách sách</a> |
            <a href="{escape(url_for('api_books'))}">API sách</a>
        </nav>
    """

# MỤC 3: Danh sách sách
@app.route("/books")
def books():
    category = request.args.get("category")

    if category:
        filtered_books = [
            book for book in BOOKS
            if book["category"] == category
        ]
    else:
        filtered_books = BOOKS

    rows = [
        f"""
        <tr>
            <td>{escape(book["id"])}</td>
            <td><a href="{escape(url_for('book_detail', book_id=book['id']))}">{escape(book["title"])}</a></td>
            <td>{escape(book["author"])}</td>
            <td>{escape(book["year"])}</td>
            <td>{escape(book["category"])}</td>
            <td>{"Có" if book["available"] else "Không"}</td>
        </tr>
        """
        for book in filtered_books
    ]
    category_links = " | ".join(
        f'<a href="{escape(url_for("books", category=category))}">{escape(category)}</a>'
        for category in sorted({book["category"] for book in BOOKS})
    )

    return f"""
        <h1>Danh sách sách</h1>

        <p>
            <a href="{escape(url_for('books'))}">Tất cả</a> |
            {category_links}
        </p>

        <table border="1">
            <tr>
                <th>ID</th>
                <th>Tên sách</th>
                <th>Tác giả</th>
                <th>Năm</th>
                <th>Thể loại</th>
                <th>Có sẵn</th>
            </tr>
            {"".join(rows)}
        </table>
        <p><a href="{escape(url_for('index'))}">Trang chủ</a></p>
    """

# MỤC 4: Chi tiết sách
@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = find_book(book_id)

    if book is None:
        abort(404, description=f"Không có sách với ID = {book_id}")

    return f"""
        <h1>{escape(book["title"])}</h1>
        <p>ID: {escape(book["id"])}</p>
        <p>Tác giả: {escape(book["author"])}</p>
        <p>Năm: {escape(book["year"])}</p>
        <p>Thể loại: {escape(book["category"])}</p>
        <p>Sẵn sàng cho mượn: {"Có" if book["available"] else "Không"}</p>
        <nav>
            <a href="{escape(url_for('books'))}">Danh sách sách</a> |
            <a href="{escape(url_for('index'))}">Trang chủ</a>
        </nav>
    """

# MỤC 5: API
@app.route("/api/books")
def api_books():
    return BOOKS


@app.route("/api/books/<int:book_id>")
def api_book_detail(book_id):
    book = find_book(book_id)

    if book is None:
        return {"error": f"Không có sách với ID = {book_id}"}, 404

    return book

# MỤC 6: Trang 404 tùy biến
@app.errorhandler(404)
def page_not_found(error):
    return f"""
        <h1>404 - Không tìm thấy</h1>

        <nav>
            <a href="{escape(url_for('index'))}">Trang chủ</a> |
            <a href="{escape(url_for('books'))}">Danh sách sách</a> |
            <a href="{escape(url_for('api_books'))}">API sách</a>
        </nav>

        <p>Trang bạn tìm kiếm không tồn tại.</p>
    """, 404