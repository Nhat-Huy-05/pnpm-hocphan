# Phân tích trường hợp rẽ nhánh: MySQL và MariaDB

## Bối cảnh

MySQL là hệ quản trị cơ sở dữ liệu quan hệ mã nguồn mở ra đời năm 1995, do
công ty MySQL AB (Thụy Điển) phát triển và nhanh chóng trở thành lựa chọn phổ
biến cho các ứng dụng web nhờ tốc độ, tính miễn phí và cộng đồng lớn. MySQL
được phát hành theo mô hình cấp phép kép (dual-licensing): GPL cho người dùng
mã nguồn mở, và giấy phép thương mại cho doanh nghiệp muốn tích hợp vào sản
phẩm đóng. Đến năm 2008, Sun Microsystems mua lại MySQL AB, và năm 2010,
Oracle Corporation mua lại Sun, qua đó nắm quyền kiểm soát MySQL.

## Nguyên nhân dẫn đến rẽ nhánh

Việc Oracle — một công ty nổi tiếng với các sản phẩm cơ sở dữ liệu thương mại
cạnh tranh trực tiếp với MySQL — trở thành chủ sở hữu đã gây lo ngại lớn
trong cộng đồng. Nhiều lập trình viên và tổ chức lo sợ Oracle sẽ làm chậm
tốc độ phát triển MySQL mã nguồn mở để bảo vệ các sản phẩm thương mại của
mình, hoặc thậm chí "đóng" dần dự án. Một số vấn đề cụ thể được cộng đồng
nêu ra gồm: Oracle giảm tính minh bạch trong quy trình phát triển, không còn
công khai đầy đủ bộ test suite như trước, và chậm trễ trong việc xử lý các
lỗi bảo mật được cộng đồng báo cáo. Ngoài ra, việc Oracle có toàn quyền quyết
định hướng đi của MySQL khiến nhiều bên đóng góp cảm thấy mất tiếng nói, dù
họ vẫn tham gia phát triển mã nguồn.

Trước bối cảnh đó, Michael "Monty" Widenius — người đồng sáng lập MySQL AB và
là tác giả chính của MySQL — quyết định tạo ra một nhánh (fork) độc lập mang
tên MariaDB ngay từ năm 2009, trước cả khi thương vụ Oracle hoàn tất, nhằm
đảm bảo một phiên bản MySQL luôn ở dạng hoàn toàn mã nguồn mở, không phụ
thuộc vào quyết định của một công ty duy nhất.

## Diễn biến

MariaDB được xây dựng dựa trên mã nguồn MySQL, giữ khả năng tương thích cao
để người dùng có thể chuyển đổi dễ dàng, đồng thời phát triển thêm các tính
năng mới nhanh hơn MySQL bản gốc như engine lưu trữ Aria, cải tiến tối ưu hóa
truy vấn, và các tính năng bảo mật bổ sung. MariaDB được quản lý bởi MariaDB
Foundation, một tổ chức phi lợi nhuận, đảm bảo mã nguồn luôn công khai theo
GPL và quy trình phát triển minh bạch với cộng đồng.

Sự kiện này còn tạo hiệu ứng dây chuyền: nhiều bản phân phối Linux lớn như
Red Hat Enterprise Linux, Fedora, và Debian lần lượt chuyển sang dùng
MariaDB làm cơ sở dữ liệu mặc định thay vì MySQL, xem đây là lựa chọn an toàn
hơn về mặt lâu dài.

## Kết quả và bài học

Đến nay, cả MySQL và MariaDB đều tiếp tục phát triển song song, phục vụ các
nhóm người dùng khác nhau: MySQL vẫn mạnh nhờ hệ sinh thái Oracle và tích hợp
đám mây (Oracle Cloud, AWS RDS), trong khi MariaDB thu hút cộng đồng ưu tiên
tính mở tuyệt đối và không phụ thuộc vào một công ty thương mại.

Bài học rút ra là quyền kiểm soát tập trung vào một doanh nghiệp — dù dự án
là mã nguồn mở — vẫn tạo rủi ro cho tính bền vững lâu dài của dự án đó. Việc
một dự án có cơ chế quản trị minh bạch, không phụ thuộc vào lợi ích thương
mại của một chủ sở hữu duy nhất, là yếu tố quan trọng giúp cộng đồng tin
tưởng và tiếp tục đóng góp. Đây cũng là lý do vì sao nhiều tổ chức lớn sau
này ưu tiên xây dựng quản trị dự án qua các foundation trung lập (Apache
Software Foundation, Linux Foundation...) thay vì để một công ty duy nhất
nắm toàn quyền kiểm soát.
