import csv
import math
from io import StringIO

from flask import Flask, abort, make_response, redirect, request, url_for
from markupsafe import escape
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.json.ensure_ascii = False

STUDENTS = {
    "23T1020001": {
        "name": "Nguyễn Văn An",
        "lop": "K47A",
        "scores": {"PMNM": 8.5, "CSDL": 7.0, "MMT": 9.0},
    },
    "23T1020002": {
        "name": "Trần Thị Bình",
        "lop": "K47A",
        "scores": {"PMNM": 6.0, "CSDL": 5.5, "MMT": 7.0},
    },
    "23T1020003": {
        "name": "Lê Hoàng Cường",
        "lop": "K47B",
        "scores": {"PMNM": 9.5, "CSDL": 9.0},
    },
    "23T1020004": {
        "name": "Phạm Minh Dũng",
        "lop": "K47B",
        "scores": {"PMNM": 4.0, "CSDL": 3.5, "MMT": 5.0},
    },
    "23T1020005": {
        "name": "Hoàng Thu Hà",
        "lop": "K47A",
        "scores": {},
    },
    "23T1020006": {
        "name": "Võ Quốc Khánh",
        "lop": "K47C",
        "scores": {"PMNM": 7.5, "MMT": 8.0},
    },
}


def average(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7:
        return "Khá"
    if avg >= 5:
        return "Trung bình"
    return "Yếu"


def student_summary(mssv):
    student = STUDENTS.get(mssv)
    if student is None:
        return None

    avg = average(student["scores"])
    return {
        "mssv": mssv,
        "name": student["name"],
        "lop": student["lop"],
        "scores": student["scores"],
        "average": avg,
        "rank": rank(avg),
    }


def layout(title, body):
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Sổ điểm</title>
</head>
<body>
  <header>
    <h1>{escape(title)}</h1>
    <nav>
      <a href="{escape(url_for('index'))}">Trang chủ</a> ·
      <a href="{escape(url_for('student_list'))}">Sinh viên</a> ·
      <a href="{escape(url_for('search'))}">Tìm kiếm sinh viên</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>"""


@app.route("/")
def index():
    class_count = len({student["lop"] for student in STUDENTS.values()})
    body = f"""
    <p>Tổng số sinh viên: <strong>{len(STUDENTS)}</strong></p>
    <p>Số lớp: <strong>{class_count}</strong></p>
    <p><a href="{escape(url_for('student_list'))}">Xem danh sách sinh viên</a></p>
    """
    return layout("Sổ điểm lớp học", body)


@app.route("/students")
def student_list():
    class_filter = request.args.get("lop", "")
    classes = sorted({student["lop"] for student in STUDENTS.values()})
    students = [
        student_summary(mssv)
        for mssv, student in sorted(STUDENTS.items())
        if not class_filter or student["lop"].casefold() == class_filter.casefold()
    ]

    options = ['<option value="">Tất cả</option>']
    for class_name in classes:
        selected = (
            " selected"
            if class_name.casefold() == class_filter.casefold()
            else ""
        )
        options.append(
            f'<option value="{escape(class_name)}"{selected}>'
            f"{escape(class_name)}</option>"
        )

    rows = []
    for student in students:
        avg = "—" if student["average"] is None else f'{student["average"]:.2f}'
        detail_url = url_for("student_detail", mssv=student["mssv"])
        rows.append(
            f"""<tr>
              <td><a href="{escape(detail_url)}">{escape(student["mssv"])}</a></td>
              <td>{escape(student["name"])}</td>
              <td>{escape(student["lop"])}</td>
              <td>{escape(avg)}</td>
              <td>{escape(student["rank"])}</td>
            </tr>"""
        )

    table = (
        "<p>Không có sinh viên phù hợp.</p>"
        if not rows
        else f"""<table>
          <thead>
            <tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>"""
    )
    body = f"""
    <form action="{escape(url_for('student_list'))}" method="get">
      <label for="lop">Lọc theo lớp:</label>
      <select id="lop" name="lop">{"".join(options)}</select>
      <button type="submit">Lọc</button>
    </form>
    {table}
    """
    return layout("Danh sách sinh viên", body)


@app.route("/students/<mssv>")
def student_detail(mssv):
    student = student_summary(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    avg = "—" if student["average"] is None else f'{student["average"]:.2f}'
    score_rows = "".join(
        f"<tr><td>{escape(course)}</td><td>{escape(score)}</td></tr>"
        for course, score in student["scores"].items()
    )
    scores = (
        "<p>Sinh viên chưa có điểm.</p>"
        if not score_rows
        else f"""<table>
          <thead><tr><th>Học phần</th><th>Điểm</th></tr></thead>
          <tbody>{score_rows}</tbody>
        </table>"""
    )
    class_url = url_for("student_list", lop=student["lop"])
    export_url = url_for("export_scores", mssv=mssv)
    body = f"""
    <p>MSSV: {escape(student["mssv"])}</p>
    <p>Họ tên: {escape(student["name"])}</p>
    <p>Lớp: <a href="{escape(class_url)}">{escape(student["lop"])}</a></p>
    <p>Điểm trung bình: {escape(avg)}</p>
    <p>Xếp loại: {escape(student["rank"])}</p>
    <h2>Bảng điểm từng học phần</h2>
    {scores}
    <p><a href="{escape(export_url)}">Tải bảng điểm (CSV)</a></p>
    """
    return layout(f"Sinh viên {mssv}", body)


@app.route("/sv/<mssv>")
def short_student_url(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)


@app.route("/students/<mssv>/export")
def export_scores(mssv):
    student = STUDENTS.get(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["hoc_phan", "diem"])
    for course, score in student["scores"].items():
        writer.writerow([course, score])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=diem_{mssv}.csv"
    )
    return response


@app.route("/search")
def search():
    keyword = request.args.get("q", "")
    needle = keyword.casefold()
    matches = [
        student_summary(mssv)
        for mssv, student in sorted(STUDENTS.items())
        if needle
        and (
            needle in student["name"].casefold()
            or needle in mssv.casefold()
        )
    ]
    results = "".join(
        f"""<li>
          <a href="{escape(url_for('student_detail', mssv=student["mssv"]))}">
            {escape(student["name"])} — {escape(student["mssv"])} ({escape(student["lop"])})
          </a>
        </li>"""
        for student in matches
    )
    results_html = (
        "<p>Không có sinh viên phù hợp.</p>"
        if not results
        else f"<ul>{results}</ul>"
    )
    body = f"""
    <form action="{escape(url_for('search'))}" method="get">
      <label for="q">Họ tên hoặc MSSV:</label>
      <input id="q" name="q" type="search" value="{escape(keyword)}">
      <button type="submit">Tìm</button>
    </form>
    {results_html}
    """
    return layout("Tìm kiếm sinh viên", body)


@app.route("/api/students")
def api_students():
    class_filter = request.args.get("lop", "")
    raw_min_avg = request.args.get("min_avg")
    minimum_average = None

    if raw_min_avg is not None:
        try:
            minimum_average = float(raw_min_avg)
        except ValueError:
            abort(400, description="Tham số min_avg phải là một số hợp lệ.")
        if not math.isfinite(minimum_average):
            abort(400, description="Tham số min_avg phải là một số hữu hạn.")

    students = [
        student_summary(mssv)
        for mssv, student in sorted(STUDENTS.items())
        if not class_filter or student["lop"].casefold() == class_filter.casefold()
    ]
    if minimum_average is not None:
        students = [
            student
            for student in students
            if student["average"] is not None
            and student["average"] >= minimum_average
        ]
    return students


@app.route("/api/students/<mssv>")
def api_student_detail(mssv):
    student = student_summary(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    return student


@app.route(
    "/api/students/<mssv>/scores/<course>",
    methods=["GET", "PUT", "DELETE"],
)
def api_student_score(mssv, course):
    student = STUDENTS.get(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    normalized_course = course.upper()
    scores = student["scores"]

    if request.method == "GET":
        if normalized_course not in scores:
            abort(
                404,
                description=(
                    f"Sinh viên {mssv} chưa có điểm học phần {normalized_course}."
                ),
            )
        return {
            "mssv": mssv,
            "course": normalized_course,
            "score": scores[normalized_course],
        }

    if request.method == "DELETE":
        if normalized_course not in scores:
            abort(
                404,
                description=(
                    f"Sinh viên {mssv} chưa có điểm học phần {normalized_course}."
                ),
            )
        del scores[normalized_course]
        return "", 204

    raw_score = request.args.get("score")
    if raw_score is None:
        abort(400, description="Thiếu tham số score.")
    try:
        score = float(raw_score)
    except ValueError:
        abort(400, description="Điểm phải là một số từ 0 đến 10.")
    if not math.isfinite(score) or not 0 <= score <= 10:
        abort(400, description="Điểm phải là một số từ 0 đến 10.")

    is_new_score = normalized_course not in scores
    scores[normalized_course] = score
    headers = (
        {"Location": url_for(
            "api_student_score",
            mssv=mssv,
            course=normalized_course,
        )}
        if is_new_score
        else {}
    )
    return {
        "mssv": mssv,
        "course": normalized_course,
        "score": score,
        "average": average(scores),
    }, 201 if is_new_score else 200, headers


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
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
            app.json.dumps({"error": title, "detail": detail})
        )
        response.content_type = "application/json; charset=utf-8"
        return response

    body = f"<p>{escape(detail)}</p>"
    response.set_data(layout(f"{status} - {title}", body))
    response.content_type = "text/html; charset=utf-8"
    return response
