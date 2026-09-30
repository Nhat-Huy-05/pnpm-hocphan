# LibraryMS v0.1

Bài tập Flask cơ bản của Chương 3. Ứng dụng dùng dữ liệu mẫu lưu trong `BOOKS` ở `app.py`.

## Chức năng

- Trang chủ hiển thị tổng số sách và số sách có thể cho mượn.
- Danh sách sách có lọc theo thể loại và liên kết tới trang chi tiết.
- Trang chi tiết và API trả về thông báo 404 khi không tìm thấy sách.
- Trang lỗi HTML có menu điều hướng; API trả lỗi ở định dạng JSON.
- Các liên kết HTML được tạo bằng `url_for`; dữ liệu động trong HTML được escape.

## Cài đặt và chạy

Chạy các lệnh sau trong thư mục `chuong3/libraryms`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
flask --app app run --debug
```

Set-Location chuong3/libraryms
..\..\venv\Scripts\python.exe -m flask --app app run --debug

Mở `http://127.0.0.1:5000/` sau khi Flask khởi động.

## Các route

| Route                  | Mô tả                                        |
| ---------------------- | -------------------------------------------- |
| `/`                    | Thống kê thư viện                            |
| `/books`               | Danh sách sách; nhận query `category` để lọc |
| `/books/<book_id>`     | Chi tiết sách                                |
| `/api/books`           | Danh sách sách dạng JSON                     |
| `/api/books/<book_id>` | Chi tiết sách dạng JSON                      |

## Nộp bài

Từ thư mục gốc repository môn học, thêm thư mục bài tập, tạo commit và gắn tag theo yêu cầu:

```powershell
git add chuong3/libraryms
git commit -m "Complete LibraryMS v0.1 exercise"
git tag v0.1
```
