# Ảnh thời khoá biểu GIẢ LẬP

> ⚠️ **Đây là ảnh giả lập, không phải ảnh chụp thật.** Kết quả spike nhận diện ảnh (T010) dựa trên các
> ảnh này **phải được kiểm chứng lại bằng ảnh chụp màn hình thật** từ cổng thông tin sinh viên trước
> khi làm User Story 6 (nhập lịch học từ ảnh).

Ba ảnh mô phỏng bố cục trang "Lịch học" của cổng thông tin sinh viên, đặt trong một ảnh chụp toàn
màn hình macOS (thanh menu, Safari, Dock):

- Lịch tuần, mỗi cột một ngày, tiêu đề cột gồm số ngày và Thứ.
- Ô môn học nền xanh đậm ghi tên môn và giờ dạng `06:45 - 09:25 (Tiết 1-3)`; bên dưới là mã lớp,
  phòng và giảng viên.
- Lịch tháng thu nhỏ ở bên phải.

Tên miền (`sinhvien.example.edu.vn`), tên môn, mã lớp, phòng và giảng viên đều là dữ liệu bịa. Ảnh
không dùng logo hay nhận diện thương hiệu của trường nào. Mỗi ảnh có dòng chữ nhỏ "ẢNH GIẢ LẬP" ở góc
dưới.

| Ảnh | Kích thước | Đặc điểm cần thử |
|-----|-----------|------------------|
| `sample-01.png` | 2880×1800 (Retina), PNG | 9 buổi, đều theo tiết chuẩn; tháng/năm lấy từ lịch thu nhỏ |
| `sample-02.png` | 1440×900 (màn hình thường), PNG | Chữ nhỏ; 2 môn E-Learning; buổi tối 20:00–21:30 không theo tiết; buổi 07:00–09:00 lệch ca |
| `sample-03.jpg` | 2880×1800, JPEG chất lượng 70 | Tuần vắt qua năm mới (28/12/2026–03/01/2027); một môn kéo dài 2 ca (Tiết 1-6) |

Mỗi ảnh có file `*.expected.json` ghi kết quả mong đợi: các buổi học với tên môn, ngày, thứ, giờ, tiết,
mã lớp, phòng, giảng viên, cờ E-Learning; cùng dòng chữ ở thanh menu và tiêu đề lịch thu nhỏ.

**Tạo lại ảnh**: `uv run --python 3.12 --with pillow samples/synthetic/make_samples.py`

**Hạn chế của ảnh giả lập** (lý do bắt buộc kiểm chứng lại bằng ảnh thật):

- Chữ vẽ bằng font Arial, khử răng cưa của Pillow, nền phẳng. Trình duyệt thật có font, độ đậm và
  khử răng cưa khác.
- Bố cục và khoảng cách lý tưởng: không có quảng cáo, banner, thanh cuộn, popup, chế độ tối.
- Chưa có ảnh dạng danh sách (bảng) và chưa có ảnh chụp một phần màn hình.


## Ảnh lịch thi giả lập (US11)

`exam-01.png` (2880×1800) và `exam-02.png` (1440×900) mô phỏng bảng "Lịch thi cá nhân": 6 dòng gồm 2
dòng đã qua, 1 dòng phòng trống, 1 dòng chỉ ghi giờ bắt đầu ("Trắc nghiệm trên máy 60p"), 1 dòng lần thi
2. Cột "Thông tin sinh viên" chứa giá trị **bịa** (`Nguyễn Văn Test - 21010999 -`) để kiểm tra chúng không
bao giờ xuất hiện trong kết quả nhận diện (FR-061). Tạo lại bằng `make_samples.py` (cùng lệnh ở trên;
sẽ vẽ lại cả ảnh lịch tuần nên dùng font hiện có trên máy, ảnh có thể khác chút so với bản đã commit).
