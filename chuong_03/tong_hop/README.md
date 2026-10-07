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

## Phần 3: Xử lý lỗi (Câu 9)

Các lỗi 400, 404 và 405 được xử lý chung:

- URL bắt đầu bằng `/api/` trả JSON theo dạng
  `{"error": "<tiêu đề>", "detail": "<mô tả>"}`.
- URL còn lại trả trang lỗi HTML theo khung `layout()`.
- Phản hồi luôn giữ mã lỗi gốc; lỗi 405 cũng giữ header `Allow` do Flask tạo.

`request` dùng được trong hàm xử lý lỗi dù hàm đó không phải view vì Flask giữ
request context trong suốt quá trình xử lý một yêu cầu. `request` là một
`LocalProxy` trỏ đến yêu cầu hiện tại trong context đó; Flask gọi error handler
trước khi kết thúc context.

## Phần 4: Kiểm thử và nộp bài

Khi server đang chạy tại cổng 8000, có thể chạy các lệnh sau trong PowerShell
để kiểm tra status, body và header quan trọng:

```powershell
$B = "http://127.0.0.1:8000"
$S = "$B/api/students/23T1020005/scores/WEB"
curl.exe -i "$B/sv/23T1020001"
curl.exe -i "$B/students/23T1020001/export"
curl.exe -i "$B/api/students?lop=k47a&min_avg=7"
curl.exe -i "$B/api/students?min_avg=abc"
curl.exe -i "$B/api/students/999"
curl.exe -i -X PUT "$S?score=9"
curl.exe -i -X PUT "$S?score=7.5"
curl.exe -i -X PUT "$S?score=11"
curl.exe -i -X DELETE "$S"
curl.exe -i -X POST "$B/api/students/23T1020001/scores/PMNM"
curl.exe -i -X POST "$B/students"
```

Đối chiếu kết quả:

| Lệnh | Status mong đợi | Nội dung cần kiểm tra |
| --- | --- | --- |
| `/sv/23T1020001` | 301 | `Location: /students/23T1020001` |
| Tải CSV | 200 | `Content-Type: text/csv; charset=utf-8`; file tải tên `diem_23T1020001.csv` |
| Lọc sinh viên qua API | 200 | JSON chỉ gồm sinh viên K47A có điểm trung bình từ 7 |
| `min_avg=abc` | 400 | JSON có `error` và `detail` |
| MSSV API không tồn tại | 404 | JSON có `error` và `detail` |
| PUT điểm WEB lần đầu | 201 | JSON điểm mới và `Location: /api/students/23T1020005/scores/WEB` |
| PUT điểm WEB lần tiếp theo | 200 | JSON phản hồi điểm sau cập nhật |
| PUT điểm 11 | 400 | JSON báo điểm phải từ 0 đến 10 |
| DELETE điểm WEB | 204 | Body rỗng |
| POST tới API điểm | 405 | JSON lỗi và header `Allow` |
| POST tới `/students` | 405 | Trang lỗi HTML, vẫn là status 405 |

Đề yêu cầu ít nhất 4 commit, tương ứng các mốc Phần 0, Phần 1, Phần 2 và
Phần 3–4. Hãy tự tạo từng commit sau khi kiểm tra xong mốc tương ứng; không
đưa `.venv/` hoặc `__pycache__/` vào Git.

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
