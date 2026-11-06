# Contract: Điều hướng và phím tắt của giao diện

## Đường dẫn (React Router)

| Đường dẫn | Màn hình |
|-----------|----------|
| `/` | chuyển tới `/cong-viec/hom-nay` (FR-012) |
| `/cong-viec/hom-nay` · `/ngay-mai` · `/7-ngay-toi` · `/tat-ca` · `/da-hoan-thanh` · `/thung-rac` | danh sách thông minh |
| `/cong-viec/danh-sach/:id` · `/cong-viec/nhan/:id` | danh sách người dùng, nhãn |
| `?task=:id` (thêm vào mọi đường dẫn Công việc) | mở bảng chi tiết task |
| `/lich?che-do=ngay\|tuan\|thang&ngay=YYYY-MM-DD&nhan=1,2` | Lịch |
| `/mon-hoc` (học kỳ, môn, thêm nhiều môn; `/mon-hoc/nhap-anh` khi có US6) | Môn học |
| `/lich-thi` | Lịch thi (hiện "Sắp có" khi US11 của feature 001 chưa xong) |
| `/cai-dat` | Cài đặt |

## Phím tắt (FR-034)

| Phím | Ở đâu | Hành vi |
|------|-------|---------|
| ⌘N | mọi nơi | về Công việc (giữ view hiện tại nếu đang ở Công việc) và đặt con trỏ vào ô "Thêm công việc" |
| ⌘F | mọi nơi | tìm kiếm (feature 003; xem [contracts/ui.md](../../003-backup-nl-recurring-search/contracts/ui.md)) |
| ⌘1 … ⌘5 | mọi nơi | Công việc, Lịch, Môn học, Lịch thi, Cài đặt |
| ⌘, | mọi nơi | Cài đặt |
| ⌘/ | mọi nơi | bảng phím tắt |
| Esc | mọi nơi | đóng hộp thoại → đóng bảng chi tiết → bỏ chọn ô nhập (theo thứ tự ưu tiên) |
| ↑ / ↓ | danh sách task | chọn task trước/sau (không mở bảng chi tiết) |
| ↩ | danh sách task | mở bảng chi tiết task đang chọn |
| ⌘↩ | danh sách task, bảng chi tiết | đánh dấu hoàn thành / bỏ hoàn thành task đang chọn |
| ⌘⌫ | danh sách task, bảng chi tiết | chuyển task đang chọn vào Thùng rác (có Hoàn tác) |
| ← / → | Lịch | khoảng trước / sau |
| T | Lịch | về Hôm nay |
| D / W / M | Lịch | chế độ Ngày / Tuần / Tháng |

Phím một ký tự (T, D, W, M, ↑, ↓, ↩, ←, →) bị bỏ qua khi con trỏ đang trong ô nhập; các phím có ⌘ và
Esc luôn hoạt động.
