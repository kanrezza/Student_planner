# Kết quả kiểm chứng feature 005

Ngày: 2026-11-11.

## Tự động (`./scripts/test.sh --ocr`, chạy trên app đã build lại)

- Backend: ruff, ruff format, pytest (673 test), pytest `-m ocr` — xanh.
- Frontend: lint, Vitest (1.365 test). Agent (pytest, ruff), scripts, `cargo test` — xanh.
- Test lưu trữ qua khởi động lại và kill đột ngột: task "Đang làm" giữ trạng thái và thứ tự trên bảng; file đính
  kèm giữ tên, dung lượng, nội dung (SHA-256 khớp); bản sao lưu `.lhbackup` format 2 chứa đúng file đó. Dữ liệu
  thử được dọn xong (0 mục đính kèm, 0 nội dung còn lại).
- Hiệu năng: bảng 300 task + lọc < 1 giây (SC-002); tải lên 50 MB < 5 giây (SC-005); tìm tên trong 1.000 file < 1
  giây (SC-009).
- Test không bao giờ chạm volume `lichhoc_attachments` thật (thư mục tạm riêng, `ATTACHMENTS_DIR` ép ra `/tmp`).

## Docker

- Sao lưu DB trước khi build (`~/Library/Application Support/LichHocAgent/backups/lichhoc-20261111-1556.dump`).
- `docker compose build backend web && docker compose up -d`: migration 0012 chạy trên DB thật (28 task còn nguyên),
  volume `lichhoc_attachments` gắn vào backend tại `/var/lib/lichhoc/attachments`, không bind mount.

## Điểm khác so với kế hoạch

- Ô thêm nhanh của bảng nằm trên đầu bảng (task mới vào đầu cột Chưa làm), không có ô riêng ở đầu cột Đang làm.
- Vùng thả file là mục *File đính kèm* (không phải cả bảng chi tiết).
- Sắp xếp phím: chuyển cột bằng ⌘←/⌘→ giữ vị trí gần nhất trong cột đích.

## Chưa kiểm tra tay (cần bạn thử trên app macOS)

- ⌘V file chép từ Finder (lệnh Tauri `clipboard_file_paths` + `upload_paths`), mở bằng ứng dụng mặc định, lưu vào
  Tải về, PDF trong `<iframe>` của WKWebView, thử khi tháo ổ SSD (SC-010), cuộn 200+ thẻ, hai cửa sổ cùng mở.
- App Tauri cần build/cài lại để có 4 lệnh mới: `desktop/scripts/install.sh`.
