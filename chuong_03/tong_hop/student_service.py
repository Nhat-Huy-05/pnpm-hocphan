from student_data import STUDENTS


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
