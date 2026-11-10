# Quickstart & Validation: Sao lưu, thêm nhanh tự nhiên, tìm kiếm, task lặp

**Feature**: `003-backup-nl-recurring-search` | **Plan**: [plan.md](plan.md)

## Yêu cầu

Như feature 002 ([quickstart 002](../002-redesign-macos-app/quickstart.md)): OrbStack, Node 22, Python 3.11
cho agent, Rust cho app Tauri. Đợt 1 cần build lại image backend (thêm `postgresql-client-16`, cần internet lúc
build), cài lại agent và app:

```bash
docker compose up -d --build           # backend + giao diện
mac-agent/scripts/install.sh           # agent mới (sao lưu, thông báo)
desktop/scripts/install.sh             # app mới (chọn thư mục, deep link)
./scripts/test.sh                      # toàn bộ lint + test
./scripts/test-persistence.sh          # + vòng sao lưu → xoá → khôi phục
```

Lần sao lưu đầu tiên vào iCloud Drive hoặc ổ rời: macOS hỏi quyền cho LichHocAgent — chọn "Cho phép". Lần đầu
cần gửi thông báo: macOS hỏi quyền thông báo — chọn "Cho phép".

Kiểm tra nhanh thời gian: các kịch bản B1–B4 đặt giờ sao lưu = giờ hiện tại + 2 phút.

## Kịch bản kiểm chứng

### Đợt 1 — Sao lưu và khôi phục

| # | Kịch bản | Bước | Kết quả mong đợi | Liên quan |
|---|----------|------|------------------|-----------|
| B1 | Sao lưu đúng giờ | Cài đặt → Sao lưu, thư mục mặc định, giờ = bây giờ + 2 phút; chờ | Trong 5 phút: có `LichHoc-…-tu-dong.lhbackup` trong iCloud Drive › Lịch Học Cá Nhân › Sao lưu; thẻ trạng thái hiện giờ, dung lượng, "Thành công"; log agent có dòng "Sao lưu xong" | US1-1, FR-001, FR-010a |
| B2 | Sao lưu bù sau khi ngủ | Đặt giờ = bây giờ + 2 phút; gập Mac 10 phút; mở lại | Trong 5 phút sau khi thức có đúng một bản mới | US1-2, FR-003, SC-001 |
| B3 | Giữ N bản | Đặt giữ lại 3; bấm "Sao lưu ngay" 5 lần | Còn đúng 3 bản mới nhất; một file `ghi-chu.txt` tự đặt vào thư mục vẫn còn | US1-4/5, FR-006, SC-004 |
| B4 | SSD tháo | Chọn thư mục trên ổ rời; tháo ổ; "Sao lưu ngay" và chờ tới giờ tự động; cắm lại | App không treo, không hộp thoại chặn; cảnh báo nhẹ + chấm trên biểu tượng Cài đặt; cắm lại → bản bù trong 5 phút | US1-6, FR-007, SC-003 |
| B5 | Quá 3 ngày | Chỉnh `backup_status.last_success_at` lùi 4 ngày (`scripts/validate.sh backup-stale`), thư mục đang tháo | Đúng một thông báo macOS; bấm → app mở Cài đặt → Sao lưu; không có thông báo thứ hai | FR-008, US1-10 |
| B6 | Khôi phục | Tạo task "Kiểm tra khôi phục"; "Sao lưu ngay"; xoá hẳn task (Thùng rác → Dọn sạch); bấm "Khôi phục" bản vừa tạo, xác nhận | Hộp xác nhận đúng nội dung; lớp phủ "Đang khôi phục…"; task trở lại; danh sách có thêm bản "Trước khi khôi phục"; cấu hình sao lưu (giờ, thư mục) không đổi | US2-2/3, FR-012, SC-002 |
| B7 | Bản hỏng / quá mới | Khôi phục một file `.lhbackup` đã sửa vài byte; rồi một file có manifest `schema_revision` lạ | "Bản sao lưu bị hỏng…" / "…phiên bản app mới hơn…"; dữ liệu giữ nguyên | US2-5, FR-012 |
| B8 | Đồng bộ sau khôi phục | Bật đồng bộ; khôi phục một bản cũ hơn có ít task hơn | Trong 1 phút Lời nhắc của Apple khớp dữ liệu đã khôi phục | US2-6, FR-013 |
| B9 | Bản trên iCloud | Finder: "Xoá bản tải về" một bản; khôi phục bản đó | Danh sách ghi "Trên iCloud"; khôi phục hiện "Đang tải bản sao lưu từ iCloud…" rồi thành công | Edge case iCloud |
| B10 | Tắt mạng | Tắt Wi-Fi; "Sao lưu ngay" | Vẫn ghi file vào thư mục iCloud Drive trên máy | SC-010 |

### Đợt 2 — Thêm nhanh bằng câu

| # | Kịch bản | Bước | Kết quả mong đợi | Liên quan |
|---|----------|------|------------------|-----------|
| N1 | Bộ test lớn | `cd frontend && npx vitest run quickParse` | ≥ 400 ca pass, gồm toàn bộ bảng FR-030 (các dòng có cụm lặp pass ở mức bộ hiểu câu với `recurrence: true`; trên giao diện chỉ đúng từ đợt 4) | SC-005 |
| N2 | Tô sáng khi gõ | Ở "Tất cả", gõ chậm "Nộp bài QTDA thứ 6 9h #Gấp" | Tô sáng xuất hiện ngay ở từng cụm; xem trước "Hạn: 09:00 Thứ Sáu, 06/11 · Nhãn: Gấp"; Enter → task "Nộp bài QTDA" | US4-1 |
| N3 | Huỷ hiểu | Gõ "Gọi chị Mai"; bấm vào "Mai" | Hết tô sáng, xem trước không còn hạn; Enter → tiêu đề "Gọi chị Mai" | US4-9, FR-031 |
| N4 | Giờ chiều, ưu tiên | Gõ "Học nhóm 3h !cao" | Hạn 15:00 hôm nay (hoặc ngày mai nếu đã qua 15:00), ưu tiên Cao | US4-14/15 |
| N5 | Ghép ngày danh sách | Ở "Ngày mai", gõ "Họp nhóm 9h" | Hạn 09:00 ngày mai | US4-13, FR-028 |
| N6 | Gợi ý, nhãn mới | Gõ "~ho" → chọn "Học tập"; gõ "#ThoiQuenMoi" | Gợi ý lọc không dấu; nhãn mới được tạo cùng task | US4-10/11, FR-034/035 |
| N7 | Bộ gõ tiếng Việt | Gõ bằng Telex "thuws 6 tuaanf sau" | Không nhảy tô sáng giữa lúc soạn; sau khi xong chữ "thứ 6 tuần sau" được hiểu | R13 |

### Đợt 3 — Tìm kiếm

| # | Kịch bản | Bước | Kết quả mong đợi | Liên quan |
|---|----------|------|------------------|-----------|
| S1 | Không dấu | ⌘F, gõ "nop bai", "NỘP BÀI", "do an" | Task "Nộp bài QTDA" và "Đồ án" xuất hiện, chữ khớp tô sáng | US5-1, FR-038 |
| S2 | Ghi chú | Gõ "email thay" | Task hiện đoạn ghi chú có "email thầy" tô sáng | US5-2 |
| S3 | Các nhóm | Gõ "quan tri", "gap", "hoc tap" | Nhóm Môn học / Buổi học (sắp tới trước) / Buổi thi; Nhãn "Gấp"; Danh sách "Học tập"; bấm nhãn → danh sách task lọc theo nhãn | US5-3/9, FR-042 |
| S4 | Đã hoàn thành, Thùng rác | Bật "Gồm cả đã hoàn thành" | Task đã xong hiện mờ; task trong Thùng rác không bao giờ hiện | US5-4/8 |
| S5 | Tốc độ | `./scripts/validate.sh search-perf` (seed 1.000 task + 1 học kỳ) | Mỗi truy vấn < 0,3 giây | SC-008 |

### Đợt 4 — Task lặp

| # | Kịch bản | Bước | Kết quả mong đợi | Liên quan |
|---|----------|------|------------------|-----------|
| R1 | Hằng tuần nhiều thứ | Tạo "Nộp báo cáo tuần" hạn 17:00 T5, lặp T2+T5; hoàn thành | Lần kế tiếp 17:00 T2; lần cũ ở Đã hoàn thành; giữ nhãn, nhắc, khung giờ làm | US3-1, FR-017 |
| R2 | Ngày 31, sau N lần | Lặp hằng tháng ngày 31, kết thúc sau 3 lần; hoàn thành 3 lần | 31/12 → 31/1 → 28/2 (hoặc 29/2); sau lần 3 không còn lần mới, "Đã kết thúc lặp" | US3-3/4, FR-018 |
| R3 | Bỏ hoàn thành | Hoàn thành rồi bỏ hoàn thành ngay | Lần kế tiếp biến mất, lần cũ trở lại | US3-6, FR-019 |
| R4 | Phạm vi sửa/xoá | Sửa tiêu đề "Chỉ lần này", hoàn thành, kiểm tra lần sau; kéo lần T2 sang T3 "Lần này và các lần sau" | Lần sau giữ tiêu đề cũ; quy tắc thành T3+T5 | US3-7/8, FR-020/020a |
| R5 | Lịch, tóm tắt, Lời nhắc | Task lặp hằng ngày 20:00; mở lịch tuần; xem Lịch của Apple các ngày tới; hoàn thành | Khối dự kiến mờ các ngày sau; bản tóm tắt mỗi ngày có task; Lời nhắc chuyển sang lần kế tiếp trong 1 phút | US3-9/10/11, SC-007 |
| R6 | Thêm nhanh có lặp | Gõ "Họp lớp thứ 2 hàng tuần 7h" | Task lặp hằng tuần T2, hạn 07:00 09/11 | US4-8 |
| R7 | Sao lưu có task lặp | Sao lưu → xoá chuỗi → khôi phục | Chuỗi và quy tắc trở lại đầy đủ | SC-002 |

### Kiểm tra không kết nối ra ngoài (SC-010, constitution IV)

Ngày 2026-11-06, khi app đang chạy bình thường:

- `lsof -nP -i -c LichHocAgent`: chỉ một kết nối `127.0.0.1 → 127.0.0.1:8080`.
- Ba container (`backend`, `web`, `db`): mọi kết nối TCP đang mở đều trong mạng cầu `192.168.147.0/24` của
  Docker (backend ↔ db, web ↔ backend, web ← máy chủ); không có địa chỉ ngoài.
- Mã nguồn (`frontend/src`, `desktop/src-tauri`, `mac-agent`, `backend/app`) không chứa URL `http(s)://` nào
  ngoài `127.0.0.1`/`localhost` (trừ `$schema` của `tauri.conf.json`, không phải kết nối).
- Chưa thử tắt hẳn Wi-Fi: các kết quả trên cho thấy tính năng mới không cần mạng; B10 nên bấm thử thật.

### Hồi quy

`./scripts/test.sh` và các kịch bản kiểm chứng của feature 001 và 002 vẫn pass (SC-009).
