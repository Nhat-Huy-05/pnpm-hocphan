import math

from flask import abort, request, url_for

from student_data import STUDENTS
from student_service import average, student_summary


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


def api_student_detail(mssv):
    student = student_summary(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    return student


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


def register_api_routes(app):
    app.add_url_rule(
        "/api/students", endpoint="api_students", view_func=api_students
    )
    app.add_url_rule(
        "/api/students/<mssv>",
        endpoint="api_student_detail",
        view_func=api_student_detail,
    )
    app.add_url_rule(
        "/api/students/<mssv>/scores/<course>",
        endpoint="api_student_score",
        view_func=api_student_score,
        methods=["GET", "PUT", "DELETE"],
    )
