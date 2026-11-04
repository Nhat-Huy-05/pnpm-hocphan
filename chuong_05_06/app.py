from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Flask, Response, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qlsv.db"
db.init_app(app)


class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"

with app.app_context():
    db.create_all()

@app.get("/them-bau")
@app.get("/them-mau")
def seed_students():
    total = db.session.scalar(
        db.select(func.count()).select_from(Student)
    )

    if total:
        return f"Bảng đã có {total} sinh viên, không thêm nữa."

    students = [
        Student(mssv="23T1020001", name="Nguyen Van An", gpa=8.2),
        Student(mssv="23T1020002", name="Tran Thi Binh", gpa=7.6),
        Student(mssv="23T1020003", name="Le Van Cuong", gpa=6.8),
        Student(mssv="23T1020004", name="Pham Thi Dung", gpa=9.0),
        Student(mssv="23T1020005", name="Hoang Thu Ha", gpa=7.4),
    ]

    db.session.add_all(students)
    db.session.commit()
    return f"Đã thêm {len(students)} sinh viên."

@app.get("/thu-truy-van")
def try_queries():
    count = db.session.scalar(db.select(func.count(Student.id)))
    if not count:
        return Response(
            "Chưa có dữ liệu, hãy mở /them-bau trước.",
            mimetype="text/plain",
        )

    lines = []
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")

    everyone = db.session.execute(
        db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")

    stmt = (db.select(Student)
            .where(Student.gpa >= 8)
            .order_by(Student.gpa.desc()))
    good = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 8: {good}")

    binh = db.session.scalar(db.select(Student)
                             .filter_by(mssv="23T1020002"))
    lines.append(f"5. MSSV 23T1020002: {binh}")

    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")

    return Response("\n".join(lines), mimetype="text/plain")


@app.get("/sinh-vien")
def student_list():
    students = db.session.execute(
        db.select(Student).order_by(Student.id)
    ).scalars().all()
    return render_template("students.html", students=students)


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
