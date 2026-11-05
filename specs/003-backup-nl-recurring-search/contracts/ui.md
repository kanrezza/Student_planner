# Giao diện, phím tắt và app Tauri — phần thêm của feature 003

Phong cách theo feature 002 (`ui/`, token màu sáng/tối, chữ qua `i18n/vi.ts`).

## Đường dẫn

| Đường dẫn | Màn hình |
|-----------|----------|
| `/cai-dat/sao-luu` | Cài đặt → Sao lưu (đợt 1) |
| `/cong-viec/tim-kiem?q=…&done=1` | Kết quả tìm kiếm trong khu vực chính (đợt 3) |

## Phím tắt (thêm vào `shortcutsTable.ts` và bảng ⌘/)

| Phím | Phạm vi | Hành động |
|------|---------|-----------|
| ⌘F | mọi nơi | về Công việc, đặt con trỏ vào ô tìm kiếm ở đầu cột danh sách |
| Esc | ô tìm kiếm | xoá từ khoá, về màn hình trước khi tìm |
| ↑ / ↓, ↩ | kết quả tìm kiếm | chọn, mở kết quả |
| ↑ / ↓, ↩ / Tab, Esc | gợi ý `#` `~` trong Thêm công việc | chọn / nhận gợi ý / đóng gợi ý |

## Cài đặt → Sao lưu

Thứ tự trên trang: trạng thái (thẻ trên cùng: "Lần gần nhất: 21:00 Thứ Năm, 05/11/2026 — 2,4 MB — Thành công",
hoặc thẻ cảnh báo vàng nhạt) · nút chính "Sao lưu ngay" · công tắc "Tự động sao lưu mỗi ngày" + giờ · "Thư
mục" (đường dẫn dễ đọc, "Chọn thư mục…", "Dùng thư mục mặc định", "Mở trong Finder") · "Giữ lại [14] bản gần
nhất" · danh sách bản (ngày giờ, dung lượng, loại, "Trên iCloud" nếu có, nút "Khôi phục") · "Chọn bản sao lưu
khác…". Chấm cảnh báo trên biểu tượng Cài đặt ở thanh biểu tượng khi `stale` hoặc thư mục không có.

Khôi phục: `ConfirmDialog` với nội dung ở US2 kịch bản 2 → trong lúc chạy, lớp phủ toàn app "Đang khôi phục
dữ liệu…" kèm bước hiện tại → xong: toast "Đã khôi phục dữ liệu về …" và làm mới toàn bộ cache truy vấn.

## Thêm nhanh

Ô "Thêm công việc" có lớp tô sáng (research R13); dòng xem trước bên dưới (chữ nhỏ, màu phụ): các chip "Hạn: …",
"Lặp: …", "Danh sách: …", "Nhãn: …"/"Nhãn mới: …", "★ Quan trọng", "Ưu tiên: …"; hạn đã qua màu đỏ "đã qua";
"Thiếu tên công việc" khi tiêu đề rỗng. Rê chuột trên vùng tô sáng: tooltip "Bấm để giữ làm chữ".

## Tìm kiếm

Ô tìm ở đầu cột danh sách (biểu tượng kính lúp, chữ gợi ý "Tìm kiếm"). Gõ → khu vực chính chuyển sang kết quả
(debounce 120 ms), công tắc "Gồm cả đã hoàn thành", các nhóm có tên + số, "Xem thêm (n)". Không kết quả:
"Không tìm thấy kết quả cho “…”".

## Task lặp

Bảng chi tiết task: hàng "Lặp lại" mở popover chỉnh quy tắc (kiểu, N, chọn thứ dạng 7 nút T2…CN, ngày trong
tháng, kết thúc). Hộp thoại phạm vi: "Sửa task lặp lại" / "Chỉ lần này" · "Lần này và các lần sau" · "Huỷ" (xoá:
tiêu đề "Xoá task lặp lại"). Dòng task: biểu tượng ↻ cạnh giờ hạn, tooltip `describeRule`. Lịch: khối dự kiến
mờ 50%, viền nét đứt, biểu tượng ↻.

## App Tauri (đợt 1)

- Lệnh mới (Rust), chỉ cấp cho origin `http://127.0.0.1:8080` qua capability `backup.json`:
  `pick_backup_folder`, `pick_backup_file`, `reveal_in_finder` (research R11).
- Plugin `tauri-plugin-dialog` (dùng từ Rust) và `tauri-plugin-deep-link` (scheme `lichhoc`).
  `lichhoc://cai-dat/sao-luu` → hiện cửa sổ, điều hướng tới `http://127.0.0.1:8080/cai-dat/sao-luu`. Chỉ nhận
  đường dẫn trong danh sách cho phép (`cai-dat/sao-luu`).
- `desktopBridge.ts`: `isDesktop()`, `pickBackupFolder()`, `pickBackupFile()`, `revealInFinder(path)`; ngoài
  Tauri thì trả `null`/ẩn nút và hiện ô nhập đường dẫn.
