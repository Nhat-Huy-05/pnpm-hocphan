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

## Phần 2: API JSON (Câu 7–8)

| Phương thức | Đường dẫn | Chức năng |
| --- | --- | --- |
| GET | `/api/students` | Danh sách sinh viên dạng JSON |
| GET | `/api/students?lop=K47A` | Lọc theo lớp, không phân biệt hoa thường |
| GET | `/api/students?min_avg=7` | Lọc điểm trung bình từ 7 trở lên |
| GET | `/api/students?lop=K47A&min_avg=7` | Kết hợp hai bộ lọc |
| GET | `/api/students/<mssv>` | Thông tin tổng hợp một sinh viên |
| GET | `/api/students/<mssv>/scores/<course>` | Đọc điểm học phần |
| PUT | `/api/students/<mssv>/scores/<course>?score=8.5` | Thêm hoặc cập nhật điểm |
| DELETE | `/api/students/<mssv>/scores/<course>` | Xóa điểm học phần |

`min_avg` sai kiểu hoặc không hữu hạn trả 400; khi lọc theo điểm, sinh viên
chưa có điểm trung bình không được đưa vào kết quả. Mã học phần không phân biệt
hoa thường. Điểm phải là số hữu hạn từ 0 đến 10, bao gồm cả 0. Thêm điểm trả
201 và `Location` trỏ về URL học phần; cập nhật trả 200; xóa thành công trả
204 với body rỗng. MSSV hoặc điểm học phần không tồn tại trả 404. Phương thức
không được hỗ trợ trả 405.

Ví dụ gọi API trong PowerShell:

```powershell
$B = "http://127.0.0.1:8000"
curl.exe -i "$B/api/students"
curl.exe -i "$B/api/students?lop=k47a&min_avg=7"
curl.exe -i "$B/api/students?min_avg=abc"
curl.exe -i "$B/api/students/23T1020001"
curl.exe -i "$B/api/students/23T1020001/scores/pmnm"
curl.exe -i -X PUT "$B/api/students/23T1020005/scores/web?score=8"
curl.exe -i -X PUT "$B/api/students/23T1020001/scores/PMNM?score=7.5"
curl.exe -i -X DELETE "$B/api/students/23T1020005/scores/WEB"
```

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
