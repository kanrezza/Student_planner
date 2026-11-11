# Kết quả kiểm chứng feature 004

Ngày: 2026-11-11.

## Tự động (`./scripts/test.sh --ocr`)

- Backend: ruff, ruff format, pytest 563 test, pytest `-m ocr` (2 test) — xanh.
- Frontend: lint, Vitest — xanh. Agent, scripts, cargo test, test lưu trữ qua khởi động lại — xanh.
- Kịch bản A1–A15 của quickstart đều có test; SC-002: đọc PDF 2 trang < 3 giây (test hiệu năng).
- Lỗi gặp và đã sửa: file đáp án PDF đặt tên `*.expected.json` bị test OCR quét nhầm → đổi thành
  `tkb-synthetic-01.answer.json`.

## File thật `samples/tkb-hk2-2026.pdf` (chạy bộ đọc trong container, không in dữ liệu cá nhân)

- Học kỳ đề xuất "HK2 2026–2027", 8 môn, 17 lịch, 16 hàng bảng, không có vấn đề nào ở bản xem trước.
- Khoảng ngày 30/11/2026–28/02/2027; môn "Tích hợp… (COUR01)" đề xuất nhãn E-Learning.

## Docker

- `docker compose build backend web && docker compose up -d`: migration 0010/0011 chạy thành công trên DB
  thật (đang chưa có môn nào); bảng tiết có 15 tiết (1–12, 16–18). Đã sao lưu trước khi build.

## Chưa kiểm tra tay trên giao diện

- ⌘V file PDF trong app Tauri/WKWebView, kéo thả trên trình duyệt thật: cần người dùng thử
  (xem quickstart "Kiểm tra tay"). Kéo thả lên trang Môn học (không qua màn Nhập lịch) chưa làm; ⌘V ở
  trang Môn học thì có.
