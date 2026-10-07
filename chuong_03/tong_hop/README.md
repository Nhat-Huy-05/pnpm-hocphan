# Bài tập tổng hợp Chương 3 — Sổ điểm

## Phần 0: Khởi tạo dự án

Ứng dụng Flask dùng dữ liệu mẫu `STUDENTS` trong `sodiem.py`. Phần này khai
báo dữ liệu, cấu hình JSON tiếng Việt, các hàm tính điểm trung bình/xếp loại,
hàm tạo thông tin tổng hợp sinh viên và khung HTML dùng chung.

## Phần 1: Giao diện web (Câu 1–6)

- `/`: tổng số sinh viên và số lớp không trùng nhau.
- `/students`: danh sách sinh viên; hỗ trợ lọc theo lớp bằng `?lop=K47A`.
- `/students/<mssv>`: chi tiết sinh viên, điểm học phần và link tải CSV.
- `/sv/<mssv>`: URL rút gọn, chuyển hướng 301 đến trang chi tiết.
- `/students/<mssv>/export`: xuất bảng điểm CSV để tải xuống.
- `/search?q=<từ_khóa>`: tìm tên hoặc MSSV, giữ lại từ khóa và escape nội dung.

Liên kết HTML được tạo bằng `url_for`; dữ liệu động hiển thị trong HTML được
escape. MSSV không tồn tại ở trang chi tiết hoặc đường dẫn xuất CSV trả 404.

## Cài đặt và chạy

Chạy trong PowerShell tại thư mục `chuong_03/tong_hop`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
flask --app sodiem run --debug --port 8000
```

Mở `http://127.0.0.1:8000/` sau khi Flask khởi động. Môi trường ảo `.venv/`
và `__pycache__/` đã được bỏ qua bởi `.gitignore`.
