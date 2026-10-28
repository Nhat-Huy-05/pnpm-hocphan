from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Flask, render_template, request

app = Flask(__name__)


def parse_decimal(value):
    try:
        number = Decimal(value.strip().replace(",", "."))
    except InvalidOperation:
        return None

    if not number.is_finite():
        return None
    return number


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    values = {"a": "", "op": "+", "b": ""}
    errors = {}
    result = None

    if request.method == "POST":
        values["a"] = request.form.get("a", "").strip()
        values["op"] = request.form.get("op", "")
        values["b"] = request.form.get("b", "").strip()

        numbers = {}
        for field in ("a", "b"):
            numbers[field] = parse_decimal(values[field])
            if numbers[field] is None:
                errors[field] = "Vui lòng nhập một số hợp lệ."

        if values["op"] not in {"+", "-", "*", "/"}:
            errors["op"] = "Phép toán không hợp lệ."
        elif not errors:
            if values["op"] == "/" and numbers["b"] == 0:
                errors["b"] = "Không thể chia cho 0."
            elif values["op"] == "+":
                result = numbers["a"] + numbers["b"]
            elif values["op"] == "-":
                result = numbers["a"] - numbers["b"]
            elif values["op"] == "*":
                result = numbers["a"] * numbers["b"]
            else:
                result = numbers["a"] / numbers["b"]

    return render_template(
        "calculator.html",
        values=values,
        errors=errors,
        result=result,
    )


def validate_score(value):
    score = parse_decimal(value)
    if score is None:
        return None, "Vui lòng nhập một số hợp lệ."
    if not Decimal("0") <= score <= Decimal("10"):
        return None, "Điểm phải nằm trong khoảng từ 0 đến 10."
    return score, None


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


@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    values = {"height": "", "weight": ""}
    errors = {}
    bmi_value = None
    category = None
    category_color = None
    weight_range = None

    if request.method == "POST":
        values["height"] = request.form.get("height", "").strip()
        values["weight"] = request.form.get("weight", "").strip()
        numbers = {}

        for field, minimum, maximum in (
            ("height", Decimal("50"), Decimal("250")),
            ("weight", Decimal("10"), Decimal("300")),
        ):
            number = parse_decimal(values[field])
            if number is None:
                errors[field] = "Vui lòng nhập một số hợp lệ."
            elif not minimum <= number <= maximum:
                if field == "height":
                    errors[field] = "Chiều cao phải từ 50 đến 250 cm."
                else:
                    errors[field] = "Cân nặng phải từ 10 đến 300 kg."
            else:
                numbers[field] = number

        if not errors:
            height_m = numbers["height"] / Decimal("100")
            raw_bmi = numbers["weight"] / (height_m * height_m)
            bmi_value = raw_bmi.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

            if raw_bmi < Decimal("18.5"):
                category, category_color = "Thiếu cân", "warning"
            elif raw_bmi < Decimal("23"):
                category, category_color = "Bình thường", "success"
            elif raw_bmi < Decimal("25"):
                category, category_color = "Thừa cân", "warning"
            else:
                category, category_color = "Béo phì", "danger"

            weight_range = (
                (Decimal("18.5") * height_m * height_m).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                ),
                (Decimal("22.9") * height_m * height_m).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                ),
            )

    return render_template(
        "bmi.html",
        values=values,
        errors=errors,
        bmi_value=bmi_value,
        category=category,
        category_color=category_color,
        weight_range=weight_range,
    )


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
