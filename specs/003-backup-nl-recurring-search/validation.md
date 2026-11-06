# Kết quả kiểm chứng — feature 003

Ngày chạy: 2026-11-06. Chỉ ghi phần **tự động được**; phần cần thao tác thật trên máy được liệt kê ở cuối.

## Chạy tự động

| Kịch bản | Cách chạy | Kết quả |
|----------|-----------|---------|
| N1 (bộ hiểu câu) | `npx vitest run quickParse` | 852 ca pass (yêu cầu ≥ 400) |
| N2–N6 (tô sáng, huỷ hiểu, ghép ngày, gợi ý, nhãn mới) | `tests/quickAdd.test.tsx`, `test_tasks_api.py` | pass |
| S1–S4 (tìm kiếm) | `test_search_api.py`, `tests/search.test.tsx`, `test_vn_fold.py` | pass |
| S5 (tốc độ) | `./scripts/validate.sh search-perf` | pass, mỗi truy vấn < 0,3 giây |
| R1–R6 (task lặp) | `test_task_series_api.py`, `test_task_series_views.py`, `test_task_recurrence.py`, `tests/recurrence.test.tsx`, `tests/quickAdd.test.tsx` | pass |
| R7 (sao lưu có task lặp) | `test_restore_api.py::test_khoi_phuc_giu_du_chuoi_task_lap_va_quy_tac` | pass |
| B3, B6, B7, B10 (giữ N bản, khôi phục, bản hỏng/quá mới, ghi file) | `test_backup_*`, `test_restore_*` (kể cả khôi phục bản schema cũ) | pass |
| B5 (thông báo quá 3 ngày) | `mac-agent` pytest (78 test) | pass phần logic; thông báo thật xem mục bên dưới |
| Feature 001 + 002 (V1–V19, D4/D6/D10) | `./scripts/validate.sh` (OCR ảnh thật) | 20/20 đạt |
| Tương phản (T095) | `tests/contrast.test.ts` thêm: chữ trên nền tô sáng, thẻ cảnh báo, khối lần dự kiến | 95 pass |
| Toàn bộ lint + test | `./scripts/test.sh` | xem T098 |

### Phát hiện khi kiểm tra tương phản

Khối lần dự kiến trên lịch ban đầu mờ 50% làm chữ không đạt 4.5:1. Mức mờ thấp nhất giữ được ≥ 4.5:1 với cả
12 màu ở hai chế độ là 0.9, nên `.is-projected` dùng `opacity: 0.9`; phân biệt với task thật bằng viền nét đứt
và biểu tượng ↻ (test `contrast.test.ts` khoá giá trị này).

## Cần thao tác thật (chưa chạy tự động được)

B1, B2, B4, B5 (thông báo macOS), B8, B9 (iCloud, ổ rời, gập máy, Lời nhắc của Apple), N7 (bộ gõ Telex thật),
R5 (Lời nhắc/Lịch của Apple chuyển sang lần kế tiếp trong 1 phút), cùng quyền macOS cho LichHocAgent. Các
hướng dẫn thử từng bước nằm trong `quickstart.md`.
