# Contract: định dạng PDF "Thời khóa biểu chính thức" được hỗ trợ

Mô tả đầu vào mà bộ đọc PDF chấp nhận. Mọi điểm ở đây có test trên file PDF giả lập
(`backend/tests/fixtures/timetables/tkb-synthetic-*.pdf`, sinh bằng `samples/synthetic/make_timetable_pdf.py`).

## Điều kiện để nhận là thời khoá biểu

- PDF có lớp chữ (ký tự thật), ≤ 20 trang, không mật khẩu.
- Có hàng tiêu đề chứa (sau khi bỏ dấu, không phân biệt hoa thường, chấp nhận chữ ngắt dòng): `Mã HP`,
  `Lớp học phần`, `Thứ 2`, `Thứ 3`, `Thứ 4`, `Thứ 5`, `Thứ 6`, `Thứ 7`, `CN`, `Thời gian`. `STT`, `Số TC`,
  `Học phí` là tuỳ chọn.
- Bảng có thể tràn sang trang sau; hàng tiêu đề ở trang sau có thể có hoặc không (không có thì dùng cột của trang
  trước).

## Vùng được đọc và vùng bị bỏ

| Vùng | Xử lý |
|------|-------|
| Dòng `Học kỳ <n> Năm học <yyyy> - <yyyy>` (phía trên bảng) | Đọc để đề xuất tên học kỳ |
| Phần còn lại phía trên bảng (tên trường, họ tên, mã sinh viên, khoá/lớp, ngành, "Số:") | **Bỏ ngay**, không vào kết quả |
| Bảng, cột `STT`, `Học phí` | Bỏ |
| Bảng, các cột còn lại, từ hàng sau tiêu đề tới trước hàng `Tổng cộng` | Đọc |
| Từ `Tổng cộng` trở xuống (viết bằng chữ, ngày lập, chữ ký) | **Bỏ** |

## Một hàng dữ liệu

| Cột | Ví dụ (có thể ngắt dòng) | Kết quả |
|-----|--------------------------|---------|
| Mã HP | `FFS7010` / `69` | `course_code = "FFS701069"` (nối liền) |
| Lớp học phần | `Tích hợp và phân tích dữ` / `liệu` / `lớn-2-2-26(COUR01.LT2)` | `name = "Tích hợp và phân tích dữ liệu lớn"`, `class_code = "2-2-26(COUR01.LT2)"` |
| Số TC | `3` | `credits = 3` |
| Thứ k (0, 1 hoặc nhiều ô có nội dung) | `4 - 6 (A6-203` / `(PC))` | quy tắc: thứ k, tiết 4–6, `room = "A6-203 (PC)"` |
| | `1 - 3` / `(A6-1` / `03` / `(PC))` | tiết 1–3, `room = "A6-103 (PC)"` |
| | `4 - 6 (Sân` / `bóng đá)` | tiết 4–6, `room = "Sân bóng đá"` |
| | `16 - 18` / `(ONLINE-` / `Elearning)` | tiết 16–18, `room = "ONLINE-Elearning"`, đề xuất nhãn E-Learning |
| Thời gian | `30/11/2026` / `24/01/2027` | `start_date = 2026-11-30`, `end_date = 2027-01-24` |

Luật ghép dòng trong ô thứ: nối **không** dấu cách khi dòng trước kết thúc bằng chữ số, `.` hoặc `-`, hoặc dòng sau
bắt đầu bằng chữ số hay `.`; ngược lại nối bằng dấu cách; sau đó chuẩn hoá `(PC)` thành ` (PC)`.

Mỗi ô thứ có nội dung = 1 quy tắc. Các hàng cùng (`course_code`, `class_code`) gộp thành 1 môn, quy tắc giữ thứ tự
xuất hiện.

## Đáp án của file giả lập chính (`tkb-synthetic-01.pdf`, cùng nội dung lịch với file thật)

8 môn, 18 quy tắc; ví dụ kiểm tra:

| Môn (mã lớp) | Quy tắc |
|--------------|---------|
| Bóng đá (2-2-26(N01)) | T2 tiết 4–6 Sân bóng đá 30/11/2026–24/01/2027; T2 tiết 4–6 Sân bóng đá 15/02/2027–28/02/2027 |
| Xử lý ngôn ngữ tự nhiên (2-2-26(N01)) | T6 tiết 4–6 A6-501 (PC) 30/11–20/12/2026; T3 tiết 4–6 A6-203 (PC) và T6 tiết 4–6 A6-702 (PC) 21/12/2026–24/01/2027; T3 tiết 4–6 A6-103 (PC) 15/02–28/02/2027 |
| Trực quan hoá dữ liệu (2-2-26(N01)) | T2 tiết 1–3 A8-104 30/11/2026–17/01/2027; T2 tiết 1–2 A8-104 18/01–24/01/2027 |
| Tích hợp và phân tích dữ liệu lớn (2-2-26(COUR01)) | T3 tiết 16–18 ONLINE-Elearning, hai khoảng ngày; đề xuất nhãn E-Learning |
| Giao diện người máy (2-2-26(N02)) và (2-2-26(N02.TH1)) | hai môn riêng |

Họ tên, mã sinh viên, lớp trong file giả lập là giá trị bịa và nằm trong danh sách `must_not_appear` của test.
