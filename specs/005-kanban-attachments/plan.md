# Implementation Plan: Bảng Kanban cho công việc và đính kèm file

**Branch**: `005-kanban-attachments` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-kanban-attachments/spec.md`

## Summary

Thêm dạng xem Bảng (Kanban) cho trang Công việc và đính kèm file cho task, môn học, buổi học, buổi thi; giữ nguyên kiến
trúc (Flask + PostgreSQL trong Docker, React, app Tauri, agent macOS).

- **Kanban**: `tasks.completed_at` vẫn là nguồn của "Xong"; thêm `tasks.in_progress` và `tasks.board_rank` (thứ tự kiểu
  phân số, sắp lại khi quá sát) cùng `tasks.subject_id` để lọc theo môn ([R2, R3](research.md)). API `GET /tasks/board`,
  `PATCH /tasks/{id}/board` dùng lại đúng `complete_task` / `uncomplete_task` nên kéo sang Xong = tick ([R13](research.md)).
  Giao diện kéo thả bằng `@dnd-kit` (nhẹ, có bàn phím và thông báo cho trình đọc màn hình) ([R1](research.md)).
- **Đính kèm**: nội dung lưu trong **Docker named volume `lichhoc_attachments`** (không bind mount), tên theo **SHA-256**, ghi
  file tạm → `fsync` → đổi tên; bảng `attachment_blobs` (một bản mỗi nội dung) + `attachments` (một lần gắn, đúng một nơi gắn,
  CASCADE theo chủ) và dọn blob hết tham chiếu sau commit + quét định kỳ ([R4, R6](research.md)). Upload luồng qua nginx
  (510 MB) có tiến trình; xem trước ảnh/PDF bằng trình xem sẵn có của WebView, chỉ `inline` cho MIME an toàn ([R5, R8](research.md)).
  App macOS có lệnh mở bằng ứng dụng mặc định, lưu về Tải về và dán file từ Finder ([R9, R10](research.md)).
- **Sao lưu**: `.lhbackup` format 2 gộp `data.dump` + `attachments/<sha256>`; khôi phục nhận format 1 và 2, kiểm tra hash,
  giải nén vào vùng tạm trước khi đụng CSDL; cảnh báo khi file đính kèm vượt ngưỡng (mặc định 1 GB) ([R7](research.md)).
- **Tìm kiếm** nhóm "File" theo tên đã gập dấu ([R11](research.md)); **Cài đặt** mục "File đính kèm".

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5 + React 18 (frontend), Python 3.11 (agent), Rust stable (Tauri 2)
— giữ nguyên.

**Primary Dependencies**:
- Frontend: thêm `@dnd-kit/core` 6.3.1, `@dnd-kit/sortable` 10.0.0, `@dnd-kit/utilities` 3.2.2 (MIT).
- Backend, agent, desktop: không thêm thư viện (desktop dùng `/usr/bin/curl`, `/usr/bin/open`, `osascript` có sẵn của macOS).

**Storage**: PostgreSQL 16 (migration `0012_kanban_attachments`: cột mới của `tasks`, `settings`; bảng `attachment_blobs`,
`attachments`) + Docker named volume `lichhoc_attachments` gắn vào backend tại `/var/lib/lichhoc/attachments`.

**Testing**: pytest (chuyển trạng thái, `board_rank` và sắp lại, API bảng + lọc, upload/dedupe/giới hạn/lỗi giữa chừng, Thùng
rác và dọn blob, chuyển file khi xoá buổi, xoá môn/buổi thi có xác nhận, sao lưu format 2 + khôi phục + bản hỏng, tìm kiếm,
an toàn `content`); Vitest (bảng, kéo thả bằng bàn phím, lọc, thẻ, mục File đính kèm, xem trước, Cài đặt); `cargo test` (đặt
tên file trùng, chặn file thực thi, phân tích đường dẫn clipboard); `test-persistence.sh` thêm kiểm tra file sau khởi động lại.
Tất cả qua `./scripts/test.sh`.

**Target Platform**: macOS 14+ (Apple Silicon), app Tauri + Docker cục bộ (OrbStack).

**Project Type**: ứng dụng web cục bộ (backend + frontend trong Docker) + app Tauri + agent macOS.

**Performance Goals**: bảng 300 task + lọc < 1 giây (SC-002); upload 50 MB < 5 giây, xem trước ảnh/PDF < 10 MB < 2 giây
(SC-005); tìm tên trong 1.000 file < 1 giây (SC-009).

**Constraints**: chỉ `127.0.0.1`; không đọc nội dung file để tìm kiếm; không gửi file ra ngoài; file thực thi không mở trực
tiếp; giới hạn mỗi file 1–500 MB (mặc định 50); tiếng Việt toàn bộ.

**Scale/Scope**: 1 người dùng; vài trăm task; vài trăm–vài nghìn file, tổng vài GB; 7 user story, 30 FR.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Áp dụng trong feature | Kết quả |
|------------|----------------------|---------|
| **I. Code dễ đọc** | Hàm thuần nhỏ: `task_status`, `rank_between`, `needs_rebalance`, `board_filter`, `done_window_start`, `unique_display_name`, `detect_mime`, `is_executable`, `blob_path`; service tách `attachments_store` (đĩa) và `attachments` (CSDL) | PASS |
| **II. Test chức năng chính** | Mỗi hàm thuần + mỗi API có test thành công và lỗi; test lỗi giữa chừng khi ghi file, bản sao lưu hỏng; Vitest cho kéo thả bàn phím; một lệnh `./scripts/test.sh` | PASS |
| **III. Giao diện đơn giản** | Nút chuyển "Danh sách / Bảng" trên trang có sẵn; một thành phần "File đính kèm" dùng chung ở 4 nơi; Cài đặt thêm một mục; một thư viện UI nhỏ | PASS |
| **IV. Offline trên Mac** | File chỉ ở volume cục bộ; xem trước bằng WebView, mở bằng ứng dụng macOS; lệnh Tauri chỉ gọi `127.0.0.1`; không gửi gì ra ngoài | PASS |
| **V. Dữ liệu bền vững** | Ghi file tạm + `fsync` + `os.replace`, dòng CSDL sau khi file đã bền; dọn sau commit; sao lưu gồm cả file, khôi phục kiểm tra hash và chỉ thay khi hợp lệ; vị trí cố định (volume `lichhoc_attachments`) ghi vào README; test lưu trữ qua khởi động lại mở rộng cho file | PASS |
| **VI. Tiếng Việt** | Mọi nhãn, thông báo, lỗi upload, thông báo trình đọc màn hình qua `i18n/vi.ts`; ngày DD/MM/YYYY; dung lượng "2,4 MB"; tên file có dấu (NFC) hiển thị/tìm/tải về đúng | PASS |
| Ràng buộc bổ sung: ít phụ thuộc | 3 gói `@dnd-kit` (một thư viện), không thêm gì ở backend/agent/desktop | PASS |

**Re-check sau Phase 1**: data-model thêm 2 bảng, 5 cột, 1 volume; contracts chỉ thêm endpoint localhost và 4 lệnh Tauri
trong capability riêng giới hạn cho trang `127.0.0.1:8080`; định dạng sao lưu tương thích ngược. Vẫn PASS.

## Project Structure

### Documentation (this feature)

```text
specs/005-kanban-attachments/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── rest-api.md
│   ├── ui.md
│   └── desktop-commands.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/{task.py, settings.py, attachment.py}          # cột mới + AttachmentBlob, Attachment
│   ├── services/
│   │   ├── board.py              # trạng thái, rank, lọc, done window, chuyển cột (gọi tasks.complete/uncomplete)
│   │   ├── attachments_store.py  # đĩa: ghi tạm, hash, fsync, đổi tên, đọc, xoá, quét
│   │   ├── attachments.py        # CSDL: tạo/đổi tên/xoá mục, đếm, stats, collect_garbage, chuyển khi xoá buổi
│   │   ├── backup.py             # format 2: thêm/kiểm tra/giải nén blob
│   │   ├── search.py             # nhóm files
│   │   ├── tasks.py, subjects.py, exams.py  # rank khi tạo task, confirm khi xoá, chuyển file khi xoá buổi
│   ├── api/{board.py, attachments.py}
│   └── schemas/{board.py, attachments.py}
├── migrations/versions/0012_kanban_attachments.py
└── tests/{unit,integration}/…, tests/fixtures/attachments/
frontend/
├── nginx.conf                                   # location /api/attachments
├── src/api/{board.ts, attachments.ts}
├── src/features/tasks/board/{BoardView.tsx, BoardColumn.tsx, BoardCard.tsx, BoardFilters.tsx, boardState.ts, useBoardKeys.ts}
├── src/features/attachments/{AttachmentsSection.tsx, AttachmentRow.tsx, AttachmentPreview.tsx, useAttachmentDrop.ts, upload.ts, attachmentFormat.ts, desktop.ts}
├── src/features/settings/AttachmentsSettings.tsx
└── tests/{board*.test.tsx, attachments*.test.tsx}
desktop/src-tauri/
├── src/attachments.rs                           # open_attachment, save_attachment, clipboard_file_paths, upload_paths
└── capabilities/attachments.json
mac-agent/lichhoc_agent/backup.py                # thông báo khi file đính kèm vượt ngưỡng
docker-compose.yml                               # volume lichhoc_attachments cho backend
scripts/test-persistence.sh, scripts/persistence_check.py   # thêm kiểm tra file
```

**Structure Decision**: giữ cấu trúc web app + desktop + agent hiện có; mã mới nằm trong các module riêng (`board`,
`attachments*`) để Kanban và đính kèm làm song song được sau phần nền.

## Complexity Tracking

| Mục | Vì sao cần | Phương án đơn giản hơn bị loại vì |
|-----|-----------|-----------------------------------|
| Thư viện `@dnd-kit` | Kéo thả nhiều cột có bàn phím + thông báo trình đọc màn hình (FR-013) | Kéo thả HTML5 thuần không có bàn phím, không có bóng thẻ ổn định trong WKWebView |
| Volume thứ hai + đếm tham chiếu blob | Một bản mỗi nội dung (FR-020), Thùng rác giữ file, xoá hẳn mới dọn | Lưu file trong PostgreSQL làm dump/sao lưu phình và chậm; không gộp bản trùng thì vi phạm FR-020 |
| Định dạng sao lưu format 2 | Sao lưu phải gồm file (FR-025) và giữ được một file `.lhbackup` duy nhất cho agent | Sao lưu file riêng cần đổi agent và quy trình khôi phục hai phần |
| 4 lệnh Tauri | Mở bằng ứng dụng mặc định, lưu Tải về, dán file từ Finder (FR-016, FR-021, FR-022) không làm được từ trang web | Plugin `shell`/`fs` cấp quyền rộng hơn nhiều so với 4 lệnh cố định |
