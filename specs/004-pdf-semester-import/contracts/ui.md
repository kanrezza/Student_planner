# Contract: giao diện — thay đổi của feature 004

Theo phong cách của feature 002 (thành phần trong `frontend/src/ui`, chữ qua `i18n/vi.ts`, không thư viện UI mới).

## Màn "Nhập lịch" (đổi từ "Nhập từ ảnh") — FR-001, FR-016 đến FR-019

- Tiêu đề "Nhập lịch"; phụ đề: "Dán (⌘V), kéo thả hoặc chọn ảnh chụp lịch học, lịch thi, hoặc file PDF thời khoá
  biểu chính thức. File chỉ được xử lý trên máy, không được lưu."
- Vùng thả nhận `image/png`, `image/jpeg`, `image/heic`, `application/pdf`; định dạng ghi "PNG, JPEG, HEIC hoặc PDF,
  tối đa 20 MB". Ảnh → luồng nhận diện ảnh hiện có (không đổi). PDF → `POST /imports/timetable-pdf/preview`, trạng
  thái "Đang đọc file PDF…".
- Bảng xem trước PDF (`TimetablePreview`):
  - Dải học kỳ trên cùng: "Học kỳ: HK2 2026–2027 (tạo mới) · 30/11/2026 – 28/02/2027" kèm nút "Đổi" (chọn học kỳ
    đã có chứa trọn khoảng, hoặc tạo mới, hoặc mở rộng học kỳ chồng một phần); trạng thái `conflict` hiện lỗi đỏ.
  - Mỗi môn là một khối: ô chọn, tên (sửa được), mã HP, mã lớp, số tín chỉ, nhãn (E-Learning chọn sẵn nếu đề xuất),
    huy hiệu trạng thái "Mới" / "Đã có" (mặc định bỏ chọn, chữ mờ) / "Thay đổi" (liệt kê khác biệt "Phòng: A6-501
    (PC) → A6-203 (PC)").
  - Dưới mỗi môn là bảng quy tắc: ô chọn · Thứ · Từ ngày – Đến ngày · Tiết · Ca/Giờ · Phòng · Số buổi. Mọi ô sửa
    được (thứ bằng chọn, ngày bằng ô ngày DD/MM/YYYY, giờ bằng `ShiftPicker` hiện có). Ô lỗi tô đỏ, ô cần xem tô vàng,
    kèm lý do khi rê chuột (như bảng xem trước ảnh). Tiết chưa có giờ: ô giờ vàng "Chưa có giờ cho tiết 13–15" + ô
    nhập giờ + ô chọn "Lưu giờ này vào bảng tiết".
  - Thanh dưới: "Huỷ" · "Lưu N môn" (tắt khi còn lỗi ở phần được chọn). Sau khi lưu: thông báo "Đã tạo X môn, cập
    nhật Y môn (Z buổi học), bỏ qua W buổi đã có." cùng các cảnh báo.
- Không hiển thị bất kỳ dữ liệu nào ngoài bảng (không có họ tên, mã sinh viên…).

## Trang Môn học — FR-001

- Thả file PDF vào trang hoặc ⌘V khi clipboard có file PDF → chuyển sang màn "Nhập lịch" với file đó (giống ảnh hiện
  nay, dùng `pendingFile`). Nút "Nhập lịch" (đổi tên từ "Nhập từ ảnh").
- Dòng môn hiện tóm tắt lịch từ các quy tắc: một quy tắc → như hiện nay ("T2 · Ca 2 · Sân bóng đá"); nhiều quy tắc →
  "3 lịch · 30/11/2026 – 28/02/2027" và mở ra xem chi tiết.

## Form thêm/sửa môn — FR-020a

- Phần "Lịch học" là danh sách quy tắc; mỗi quy tắc một hàng: thứ (`WeekdayPicker`), từ ngày – đến ngày, ca/giờ
  (`ShiftPicker` hoặc giờ tuỳ chỉnh), phòng, nút xoá (ẩn khi chỉ còn 1). Nút "Thêm lịch" thêm hàng mới chép từ hàng
  cuối. Thêm mã HP và số tín chỉ (tuỳ chọn).
- Lỗi theo hàng (`schedules[i].…`) hiện ngay dưới hàng đó.
- Form nhập nhiều môn (`BulkSubjectForm`): giữ một quy tắc mỗi dòng như hiện nay.

## Cài đặt → Ca học — FR-011 đến FR-015

- Dưới bảng ca có mục "Bảng tiết": danh sách tiết (Tiết · Bắt đầu · Kết thúc · Thuộc ca), tiết sửa tay có dấu
  "đã chỉnh" và nút "Về mặc định"; nút "Thêm tiết" (cho tiết 13–30). Ghi chú: "Dùng để đổi tiết trong file PDF sang
  giờ."

## Cài đặt → mục mới "Tên môn chuẩn" — FR-028

- Danh sách tên đã lấy từ PDF (tên · mã HP · ngày thêm), nút "Xoá danh sách" (hỏi xác nhận). Ghi chú: "Dùng để tự
  sửa tên môn khi nhập lịch từ ảnh."
