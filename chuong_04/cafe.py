from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Flask, render_template, request
from menu import menu_bp

app = Flask(__name__)
app.register_blueprint(menu_bp)

SHOP = {"name":"Cà phê Sông hương", "address": "12 Lê Lợi, Huế", "open": 7, "close": 22}
PROMOTIONS = ["Giảm 10% cho sinh viên",
             "Mua 2 tặng 1 vào thứ Hai"]


def validate_score(value):
    try:
        score = Decimal(value.replace(",", "."))
    except InvalidOperation:
        return None, "Vui lòng nhập một số."

    if not score.is_finite() or not Decimal("0") <= score <= Decimal("10"):
        return None, "Điểm phải nằm trong khoảng từ 0 đến 10."

    return score, None


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


@app.route("/course-grade", methods=["GET", "POST"])
def course_grade():
    fields = ("cc", "gk", "ck")
    values = {field: "" for field in fields}
    errors = {}
    final_score = None
    letter_grade = None

    if request.method == "POST":
        scores = {}
        for field in fields:
            values[field] = request.form.get(field, "").strip()
            scores[field], error = validate_score(values[field])
            if error:
                errors[field] = error

        if not errors:
            weighted_score = (
                scores["cc"] * Decimal("0.10")
                + scores["gk"] * Decimal("0.30")
                + scores["ck"] * Decimal("0.60")
            )
            final_score = weighted_score.quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )

            if scores["ck"] < Decimal("1"):
                letter_grade = "F (điểm liệt)"
            elif final_score >= Decimal("8.5"):
                letter_grade = "A"
            elif final_score >= Decimal("7.0"):
                letter_grade = "B"
            elif final_score >= Decimal("5.5"):
                letter_grade = "C"
            elif final_score >= Decimal("4.0"):
                letter_grade = "D"
            else:
                letter_grade = "F"

    return render_template(
        "course_grade.html",
        values=values,
        errors=errors,
        final_score=final_score,
        letter_grade=letter_grade,
    )


@app.get("/contact")
def contact():
    return render_template("contact.html", shop=SHOP)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
