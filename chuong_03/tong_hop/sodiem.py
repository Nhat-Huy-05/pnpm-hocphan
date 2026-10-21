from flask import Flask, current_app, request
from markupsafe import escape
from werkzeug.exceptions import HTTPException

from api_routes import register_api_routes
from html_routes import layout, register_html_routes


def handle_http_error(error: HTTPException):
    response = error.get_response()
    titles = {
        400: "Dữ liệu không hợp lệ",
        404: "Không tìm thấy",
        405: "Phương thức không được hỗ trợ",
    }
    status = error.code
    if status not in titles:
        raise RuntimeError(f"Unexpected HTTP error status: {status}")
    title = titles[status]
    detail = error.description

    if request.path.startswith("/api/"):
        response.set_data(
            current_app.json.dumps({"error": title, "detail": detail})
        )
        response.content_type = "application/json; charset=utf-8"
        return response

    body = f"<p>{escape(detail)}</p>"
    response.set_data(layout(f"{status} - {title}", body))
    response.content_type = "text/html; charset=utf-8"
    return response


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    register_html_routes(app)
    register_api_routes(app)
    for status_code in (400, 404, 405):
        app.register_error_handler(status_code, handle_http_error)
    return app

app = create_app()

def main():
    app.run(debug=True, port=8000)

if __name__ == "__main__":
    main()
