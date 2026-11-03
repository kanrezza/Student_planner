# Quickstart & Validation: Lịch Học Cá Nhân

**Feature**: `001-task-class-scheduler` | **Plan**: [plan.md](plan.md)

Hướng dẫn chạy và các kịch bản kiểm chứng end-to-end. Chi tiết API xem
[contracts/rest-api.md](contracts/rest-api.md); chi tiết đồng bộ xem
[contracts/calendar-sync.md](contracts/calendar-sync.md).

## Yêu cầu

- macOS 14 trở lên, Apple Silicon hoặc Intel.
- OrbStack đã cài, có bật "Start at login".
- Python 3.12, chỉ cần để build `mac-agent`.
- Internet chỉ cần cho **lần build đầu** (tải image Docker, gói Python/Node và model EasyOCR). Sau
  đó ứng dụng chạy offline hoàn toàn.
- Để kiểm tra nhắc trên iPhone: iPhone cùng Apple ID, đã bật iCloud cho Lịch và Lời nhắc.

## Chạy ứng dụng

```bash
docker compose up -d --build      # lần đầu mất vài phút vì build image backend có PyTorch + EasyOCR
open http://127.0.0.1:8080        # trang "Hôm nay"
```

Cài agent nhắc lịch (một lần):

```bash
cd mac-agent && ./scripts/install.sh   # build LichHocAgent.app, cài LaunchAgent, chạy ngay
```

Vào **Cài đặt → Đồng bộ với Lịch và Lời nhắc → Bật**, rồi cho phép khi macOS hỏi quyền.

## Chạy test

```bash
docker compose run --rm backend pytest                 # unit + integration (không chạy OCR)
docker compose run --rm backend pytest -m ocr          # OCR với ảnh mẫu (chậm)
docker compose run --rm backend ruff check . && docker compose run --rm backend ruff format --check .
cd frontend && npm ci && npm test && npm run lint
cd mac-agent && python -m pytest
```

**Kỳ vọng**: tất cả đều pass. Bộ `-m ocr` in ra tỉ lệ buổi học đúng hoàn toàn cho mỗi ảnh mẫu,
và tỉ lệ này phải ≥ 80% (SC-011).

## Kịch bản kiểm chứng

| # | Kịch bản | Bước | Kết quả mong đợi | Liên quan |
|---|----------|------|------------------|-----------|
| V1 | Task cơ bản | Tạo task "Nộp bài Toán", hạn 10/11 17:00, Cao, Học tập; sửa; hoàn thành; xoá | Hiển thị đúng ở danh sách, Hôm nay, lịch | US1, SC-001 |
| V2 | Không mất dữ liệu | Tạo dữ liệu → `docker compose down` → `up -d` → khởi động lại Mac | Dữ liệu còn nguyên | FR-024, SC-008 |
| V3 | Học kỳ + nhiều môn | Tạo học kỳ "HK1 2026–2027" 07/09–20/12; nhập 6 môn một lần, chọn ca | Mỗi môn có đúng 15 buổi, đúng thứ, đúng giờ ca | US2, US8, SC-002, SC-003 |
| V4 | Ngoại lệ buổi học | Huỷ buổi 16/11, đổi phòng buổi 23/11, rồi đổi phòng chung của môn | Hai buổi ngoại lệ giữ nguyên, các buổi khác cập nhật | US4, FR-013 |
| V5 | Đổi giờ ca | Đổi Ca 2 thành 09:30–12:05, xác nhận | Môn dùng Ca 2 cập nhật, trừ buổi đã sửa giờ riêng | FR-040 |
| V6 | Lịch & nhãn | Tạo nhãn "Gấp" đỏ, gắn cho 2 task + 1 buổi; xem tuần/tháng; lọc "Gấp" | Đúng màu nhãn; lọc chỉ còn 3 mục, dưới 1 giây | US5, US9, SC-016 |
| V7 | Nhập ảnh | Kéo thả `backend/tests/fixtures/timetables/week-grid-01.png` | Bảng xem trước khớp `week-grid-01.expected.json`; ô sai được đánh dấu; giờ khớp ca hiện "Ca n" | US6, FR-041 |
| V8 | Không trùng | Lưu lần nhập V7, rồi nhập lại cùng ảnh | Mọi dòng "Đã có trong lịch", lưu tạo 0 buổi | SC-012 |
| V9 | Deadline tự tạo | Môn "Triết học" + nhãn E-Learning học Thứ Ba; môn "Giáo dục thể chất 2" Thứ Tư 20:30 | Mỗi buổi Triết học có task hạn 08:00 Chủ Nhật kế tiếp; GDTC không có | US10, SC-015 |
| V10 | Deadline phản ứng | Huỷ một buổi Triết học; xoá tay một task tự tạo khác; khôi phục buổi đã huỷ | Task của buổi huỷ biến mất rồi xuất hiện lại; task đã xoá tay không quay lại | FR-049 |
| V11 | Đồng bộ Mac | Bật đồng bộ; thêm buổi học bắt đầu sau 20 phút, nhắc 15 phút | Sự kiện xuất hiện trong Lịch "Lịch Học Cá Nhân" trong vài giây; nhắc hiện đúng giờ khi đã đóng tab | US7, SC-007, SC-018 |
| V12 | iPhone khi Mac gập | Như V11, chờ iPhone thấy sự kiện, gập Mac | iPhone nhắc đúng giờ (±1 phút) | SC-017 |
| V13 | Cập nhật & xoá | Huỷ buổi, hoàn thành task, xoá task | Mục tương ứng biến mất khỏi Lịch/Lời nhắc trên Mac và iPhone | FR-053 |
| V14 | Tắt đồng bộ | Tắt đồng bộ trong cài đặt | Lịch và danh sách "Lịch Học Cá Nhân" bị xoá; nhắc bằng trình duyệt hoạt động khi tab mở | FR-054, FR-021 |
| V15 | Offline | Tắt Wi-Fi rồi lặp lại V1, V7, V11 | Mọi thứ hoạt động; agent và backend không có kết nối ra ngoài | FR-025, SC-013 |
| V16 | Chỉ localhost | Từ máy khác cùng mạng LAN truy cập `http://<ip-mac>:8080` | Không kết nối được | Constitution IV |
| V17 | Hiệu năng | Seed 6 môn + 200 task (`docker compose run --rm backend flask seed-demo`); mở trang Hôm nay | Hiện trong dưới 2 giây; chuyển chế độ xem dưới 1 giây | SC-005, SC-006 |

## Sao lưu & khôi phục

```bash
./scripts/backup.sh                            # tạo backups/lichhoc-YYYYmmdd-HHMM.dump
./scripts/restore.sh backups/lichhoc-....dump  # khôi phục (ghi đè dữ liệu hiện tại, có hỏi xác nhận)
```

Kiểm chứng: sao lưu, xoá một môn, khôi phục, kiểm tra môn đã quay lại.

> ⚠️ `docker compose down -v` xoá volume dữ liệu. Chỉ dùng khi thật sự muốn xoá sạch.
