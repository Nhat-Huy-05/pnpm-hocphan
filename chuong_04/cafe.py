from datetime import datetime
from flask import Flask, render_template, request
from menu import menu_bp

app = Flask(__name__)
app.register_blueprint(menu_bp)

SHOP = {"name":"Cà phê Sông hương", "address": "12 Lê Lợi, Huế", "open": 7, "close": 22}
PROMOTIONS = ["Giảm 10% cho sinh viên",
             "Mua 2 tặng 1 vào thứ Hai"]

@app.get("/")
def index():
    hour = request.args.get("gio",type = int)
    if hour is None:
        hour = datetime.now().hour
    is_open = SHOP["open"] <= hour < SHOP["close"]
    return render_template(
        "index.html",
        shop=SHOP,
        promotions=PROMOTIONS,
        hour=hour,
        is_open=is_open,
    )


@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    values = {
        "a": "",
        "op": "+",
        "b": "",
    }
    errors = {}
    result = None

    if request.method == "POST":
        values["a"] = request.form.get("a", "").strip()
        values["op"] = request.form.get("op", "")
        values["b"] = request.form.get("b", "").strip()

        numbers = {}
        for field in ("a", "b"):
            try:
                numbers[field] = float(values[field].replace(",", "."))
            except ValueError:
                errors[field] = "Vui lòng nhập một số."

        operations = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b,
        }
        operation = operations.get(values["op"])
        if operation is None:
            errors["op"] = "Phép toán không hợp lệ."
        elif not errors:
            if values["op"] == "/" and numbers["b"] == 0:
                errors["b"] = "Không thể chia cho 0."
            else:
                result = operation(numbers["a"], numbers["b"])

    return render_template(
        "calculator.html",
        values=values,
        errors=errors,
        result=result,
    )


@app.get("/contact")
def contact():
    return render_template("contact.html", shop=SHOP)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
