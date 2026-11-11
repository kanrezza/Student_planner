# Contract: giao diện — thay đổi của feature 005

Theo phong cách hiện có (thành phần `frontend/src/ui`, chữ qua `i18n/vi.ts`). Thư viện mới duy nhất: `@dnd-kit`.

## Trang Công việc — FR-007 đến FR-015

- Thanh đầu trang: nút phân đoạn "Danh sách | Bảng" (nhớ trên máy). Dạng Bảng có thanh lọc: "Danh sách", "Nhãn", "Môn
  học" (menu chọn nhiều, giống bộ lọc nhãn hiện có), nút "Bỏ lọc".
- 3 cột cùng rộng, cuộn dọc riêng từng cột; tiêu đề cột: tên + số thẻ ("Đang làm · 3"). Cột Xong có nút "Hiện tất cả (12
  ẩn)" / "Chỉ 7 ngày gần nhất". Cột rỗng: "Kéo thẻ vào đây".
- Ô "+ Thêm" ở đầu cột Chưa làm và Đang làm, dùng cùng ô gõ nhanh (QuickAdd) hiện có.
- **Thẻ**: tiêu đề (2 dòng, cắt "…"), dòng phụ: hạn chót ("Hôm nay 17:00" đỏ khi quá hạn, cam khi hôm nay), chấm màu nhãn
  (tối đa 3 + "+2"), sao Quan trọng, biểu tượng lặp, kẹp giấy + số file. Thẻ Xong mờ, tiêu đề gạch ngang.
- Kéo: thẻ nâng lên có bóng, vạch chèn ở vị trí thả; thả lỗi thì thẻ trượt về chỗ cũ + thông báo.
- Bàn phím (FR-013): Tab vào bảng, mũi tên chọn thẻ (viền nhấn), ⌘←/⌘→ đổi cột, ⌘↑/⌘↓ đổi chỗ, Enter mở chi tiết, X Xong/
  bỏ Xong, Space nhấc/thả (dnd-kit). Thêm các phím vào bảng phím tắt (`?`). Trình đọc màn hình: "Đã chuyển “Làm báo cáo”
  sang Đang làm, vị trí 2 trên 5".
- Sau khi chuyển sang Xong: thông báo "Đã hoàn thành “…”" + "Hoàn tác" (6 giây).
- Dạng Danh sách: task đang làm có nhãn nhỏ "Đang làm"; dòng task có kẹp giấy + số file.

## Bảng chi tiết task — FR-004, FR-030

- Ô "Trạng thái" (Chưa làm / Đang làm / Xong), ô "Môn học" (tuỳ chọn; deadline tự tạo hiện môn của buổi, chỉ đọc).
- Mục "File đính kèm" (dưới Ghi chú).

## Mục "File đính kèm" (dùng chung: task, môn học, buổi học, buổi thi) — FR-016 đến FR-023

- Tiêu đề "File đính kèm · 3" + nút "Thêm file" (chọn nhiều). Cả bảng chi tiết là vùng thả: khi kéo file vào hiện lớp phủ
  "Thả để đính kèm vào …". ⌘V khi bảng chi tiết đang mở (và không gõ trong ô chữ) gắn file/ảnh trong clipboard.
- Mỗi dòng: biểu tượng theo loại (PDF, ảnh — ảnh nhỏ thu gọn, Word, PowerPoint, Excel, nén, khác), tên, "2,4 MB · 11/11/2026",
  menu ⋯: Xem (ảnh/PDF) hoặc Mở (loại khác, trong app macOS), Tải về, Đổi tên, Xoá. File thực thi: không có Mở, biểu tượng
  cảnh báo + tooltip "File có thể chạy chương trình, chỉ tải về khi bạn tin nguồn".
- Đang tải lên: dòng tạm có thanh tiến trình + nút Huỷ; lỗi: dòng đỏ nêu lý do (vượt giới hạn, là thư mục, ổ đầy) + "Bỏ qua".
- Xoá: hộp xác nhận "Xoá file “…” khỏi …?".

## Xem trước — FR-021

- Lớp phủ toàn cửa sổ (Dialog lớn): ảnh (vừa khung, nút +/−/1:1, kéo để di chuyển khi phóng to) hoặc PDF (`<iframe>`);
  thanh trên: tên, "‹ ›" sang file trước/sau cùng nơi gắn, Tải về, Mở bằng ứng dụng khác (app macOS), Đóng (Esc).
- Không xem được: "Không xem trước được file này" + Tải về / Mở.

## Trang Môn học, Lịch thi, Lịch

- Dòng môn, dòng buổi thi hiện kẹp giấy + số file; bảng chi tiết môn (form sửa môn có thêm mục File đính kèm, chỉ khi môn đã
  lưu), chi tiết buổi thi, `SessionDetail` của buổi học có mục File đính kèm.
- Xoá môn/buổi thi có file: hộp xác nhận thêm câu "và 3 file đính kèm".

## Tìm kiếm ⌘F — FR-027

- Nhóm "File" (biểu tượng kẹp giấy): tên file tô phần khớp, dòng phụ "Môn: Xử lý ngôn ngữ tự nhiên" / "Công việc: …" / "Buổi
  học: T3 01/12" / "Buổi thi: …". Chọn → mở nơi gắn, cuộn tới và nháy sáng dòng file 2 giây.

## Cài đặt → mục mới "File đính kèm" — FR-028

- "Tổng dung lượng: 1,2 GB · 86 file" ; "Giới hạn mỗi file: [50] MB" ; "Cảnh báo khi sao lưu lớn hơn: [1024] MB" ; bảng "10
  file lớn nhất" (tên · dung lượng · nơi gắn, bấm để mở). Ghi chú: "File lưu trên máy, trong dữ liệu của app (không nằm
  trong thư mục dự án) và có trong bản sao lưu."
- Cài đặt → Sao lưu: khi vượt ngưỡng hiện dòng cảnh báo vàng "File đính kèm đang chiếm 1,2 GB; mỗi bản sao lưu khoảng 1,3
  GB."
