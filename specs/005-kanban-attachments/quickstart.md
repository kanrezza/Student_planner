# Quickstart: kiểm chứng feature 005 — Kanban và đính kèm file

Hình dạng dữ liệu ở [data-model.md](data-model.md); API ở [contracts/rest-api.md](contracts/rest-api.md); giao diện ở
[contracts/ui.md](contracts/ui.md); lệnh app macOS ở [contracts/desktop-commands.md](contracts/desktop-commands.md).

## Chuẩn bị

```sh
cd "/Volumes/BIWIN/MySelf/Lịch Học Cá Nhân"
./scripts/backup.sh                                    # sao lưu trước migration 0012
docker compose build backend web && docker compose up -d   # tạo volume lichhoc_attachments, chạy migration
docker volume inspect lichhoc_attachments              # volume có, không bind mount vào thư mục dự án
./scripts/test.sh
```

File thử: dùng file bất kỳ trên máy hoặc file giả lập trong `backend/tests/fixtures/attachments/` (ảnh PNG nhỏ, PDF 2
trang, file .docx/.xlsx rỗng, file 0 byte, file `.command`) — không dùng tài liệu cá nhân thật trong test.

## Kịch bản tự động (chạy trong `./scripts/test.sh`)

| # | Kịch bản | Kết quả mong đợi |
|---|----------|------------------|
| K1 | Migration 0012 trên dữ liệu có task xong/chưa xong | `in_progress=false`, `board_rank` theo thứ tự cũ, `status` đúng |
| K2 | `PATCH /tasks/{id}/board` todo→doing→done, done→todo | trạng thái đúng; done giống `complete` (thời điểm, nhắc, feed đồng bộ) (SC-004) |
| K3 | Task lặp kéo sang Xong | lần kế tiếp ở đầu cột Chưa làm; Hoàn tác gỡ lần kế tiếp chưa sửa |
| K4 | Đổi chỗ giữa hai thẻ nhiều lần (khoảng < 1e-6) | cột được sắp lại, thứ tự giữ đúng (SC-003) |
| K5 | `GET /tasks/board` với lọc danh sách + nhãn + môn (gồm deadline tự tạo) và `done_window` | đúng tập thẻ, `done_hidden_count` đúng; 300 task < 1 giây (SC-002) |
| K6 | Upload 1 file vào task, môn, buổi học, buổi thi | file trong volume tên = sha256; `GET content` đúng byte |
| K7 | Cùng nội dung gắn 5 nơi | 1 blob, 5 mục; `stats.total_bytes` tăng 1 lần (SC-006) |
| K8 | File vượt giới hạn (đặt giới hạn 1 MB trong test) | 413 `file_too_large`, không còn file trong `.incoming` |
| K9 | Lỗi giữa chừng khi ghi (giả lập) | không có blob/mục, `.incoming` được dọn |
| K10 | Task có file → Thùng rác → khôi phục → xoá hẳn | file ẩn rồi hiện lại; xoá hẳn thì blob bị dọn nếu không ai dùng (SC-008) |
| K11 | Xoá môn có file không `confirm` / có `confirm` | 409 kèm số file / xoá và dọn |
| K12 | Sửa lịch môn làm mất buổi có file | file chuyển sang môn, cảnh báo `attachments_moved` |
| K13 | Sao lưu format 2 rồi khôi phục vào DB và volume trống | mọi file mở được, SHA-256 khớp (SC-007); khôi phục bản format 1 vẫn chạy |
| K14 | Bản sao lưu có blob bị sửa | khôi phục từ chối `backup_corrupt`, dữ liệu và file hiện tại nguyên vẹn |
| K15 | `GET /search?q=de cuong` | nhóm `files` có "Đề cương NLP.pdf"; file của task trong Thùng rác không có; 1.000 file < 1 giây (SC-009) |
| K16 | `content` với SVG/HTML, file `.command` | luôn `attachment`; `is_executable=true` |
| K17 | Vitest: bảng, kéo thả bằng bàn phím, lọc, thẻ, mục File đính kèm, xem trước, Cài đặt | đúng hành vi ở contracts/ui.md |
| K18 | Lưu trữ qua khởi động lại (`test-persistence.sh`) | trạng thái/thứ tự task và file còn nguyên sau `down/up` và `kill` (SC-003, constitution V) |

## Kiểm tra tay trên app macOS

1. Công việc → "Bảng": kéo một task sang Đang làm, một task sang Xong (thấy "Hoàn tác"), đổi thứ tự; ⌘R tải lại → giữ nguyên.
2. Chỉ dùng bàn phím: chọn thẻ, ⌘→ hai lần → Xong; ⌘↑ đổi chỗ; Enter mở chi tiết.
3. Lọc theo môn "Xử lý ngôn ngữ tự nhiên" → chỉ còn deadline tự tạo của môn đó và task gắn môn.
4. Mở chi tiết một môn, kéo vào một PDF và một .docx; chụp màn hình rồi ⌘V vào một task; trong Finder chép một file rồi ⌘V
   vào một buổi thi.
5. Bấm PDF → xem trong app; bấm .docx → mở bằng Pages/Word; Tải về → có trong Tải về.
6. ⌘F gõ tên file không dấu → mở đúng nơi gắn, dòng file nháy sáng.
7. Cài đặt → File đính kèm: tổng dung lượng, 10 file lớn nhất; đổi giới hạn 1 MB → gắn file 2 MB bị từ chối.
8. Tháo ổ SSD chứa mã nguồn → app vẫn mở và xem được file (SC-010).
9. Sao lưu ngay → bản sao lưu có dung lượng gồm cả file; Cài đặt → Sao lưu không cảnh báo khi < 1 GB.

Ghi kết quả vào `validation.md`.
