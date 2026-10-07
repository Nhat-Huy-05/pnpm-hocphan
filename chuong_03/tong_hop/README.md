# Bài tập tổng hợp Chương 3 — Sổ điểm

## Phần 0: Khởi tạo dự án

Ứng dụng Flask dùng dữ liệu mẫu `STUDENTS` trong `sodiem.py`. Phần này khai
báo dữ liệu, cấu hình JSON tiếng Việt, các hàm tính điểm trung bình/xếp loại,
hàm tạo thông tin tổng hợp sinh viên và khung HTML dùng chung.

## Cài đặt và chạy

Chạy trong PowerShell tại thư mục `chuong_03/tong_hop`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
flask --app sodiem run --debug --port 8000
```

Mở `http://127.0.0.1:8000/` khi hoàn thành các route ở phần tiếp theo.
Môi trường ảo `.venv/` và `__pycache__/` đã được bỏ qua bởi `.gitignore`.
