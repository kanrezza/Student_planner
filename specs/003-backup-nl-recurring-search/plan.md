# Implementation Plan: Sao lưu tự động, thêm nhanh bằng câu tiếng Việt, task lặp lại và tìm kiếm

**Branch**: `003-backup-nl-recurring-search` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-backup-nl-recurring-search/spec.md`

## Summary

Thêm bốn tính năng vào app hiện có mà không đổi kiến trúc: (1) sao lưu tự động hằng ngày + khôi phục, (2) thêm
nhanh bằng câu tiếng Việt, (3) tìm kiếm không dấu, (4) task lặp lại.

Cách làm:
- **Sao lưu**: agent Python trên Mac điều phối (vì container không ghi được vào iCloud Drive/SSD). Backend chạy
  `pg_dump` rồi trả file `.lhbackup` (ZIP gồm manifest + dump) qua localhost; agent ghi file nguyên tử vào thư
  mục đích, giữ N bản, sao lưu bù theo hàm thuần `backup_due`. Khôi phục: agent tạo bản "Trước khi khôi phục",
  gửi file lên backend, backend chạy `pg_restore --single-transaction` trong chế độ bảo trì. Giao diện ↔ agent
  đi qua bảng `backup_jobs`/`backup_status` và long-poll có sẵn. Thông báo macOS khi quá 3 ngày do agent gửi
  ([research R1–R11](research.md)).
- **Thêm nhanh**: bộ hiểu câu viết riêng bằng TypeScript, hàm thuần chạy ngay trong trình duyệt, bộ test ≥ 400
  ca; ô nhập có lớp tô sáng ([R12–R14](research.md), [ngữ pháp](contracts/quick-add-grammar.md)).
- **Tìm kiếm**: extension `unaccent` + hàm `vn_fold` IMMUTABLE trong PostgreSQL, một endpoint `/search`; tô sáng
  ở frontend bằng `foldVi` có test đối chiếu ([R15](research.md)).
- **Task lặp**: bảng `task_series` (quy tắc + mẫu), mô hình "một lần hiện tại"; chỉ lịch và bản tóm tắt cần thêm
  lần dự kiến, mọi chỗ khác dùng task thật như cũ ([R16–R18](research.md)).

Triển khai 4 đợt theo thứ tự: sao lưu & khôi phục → thêm nhanh → tìm kiếm → task lặp ([R19](research.md)).

## Technical Context

**Language/Version**: Python 3.12 (backend), Python 3.11 (agent), TypeScript 5 + React 18 (frontend), Rust
stable (app Tauri) — giữ nguyên.

**Primary Dependencies**:
- Backend: giữ nguyên (Flask 3, Flask-SQLAlchemy, Flask-Migrate, pydantic 2); image thêm
  `postgresql-client-16` (PGDG apt) cho `pg_dump`/`pg_restore`.
- Agent: thêm `pyobjc-framework-UserNotifications` (thông báo); dùng `Foundation` (đã có qua pyobjc) cho tải file
  iCloud.
- Frontend: không thêm thư viện (Radix popover, TanStack Query, React Router đã có).
- Desktop: thêm `tauri-plugin-dialog`, `tauri-plugin-deep-link`.
- PostgreSQL: extension `unaccent` (có sẵn trong `postgres:16-alpine`).

**Storage**: PostgreSQL 16 (volume `lichhoc_pgdata`); migration `0006_backup`, `0007_search`,
`0008_recurring_tasks`; file `.lhbackup` trong thư mục người dùng chọn (mặc định iCloud Drive › Lịch Học Cá
Nhân › Sao lưu); `state.json` của agent thêm vài khoá.

**Testing**: pytest (backend: API sao lưu/khôi phục với test DB, tìm kiếm, task lặp, digest/calendar có lần dự
kiến), pytest agent (hàm thuần sao lưu, thông báo, tên file, dọn bản), Vitest (bộ hiểu câu ≥ 400 ca, `foldVi`,
`describeRule`, tô sáng, ánh xạ lịch), `cargo test` (kiểm tra đường dẫn deep link và `reveal_in_finder`); tất
cả qua `./scripts/test.sh`. `test-persistence.sh` thêm vòng sao lưu → xoá → khôi phục.

**Target Platform**: macOS 14+ (Apple Silicon) trên Mac của chủ dự án.

**Project Type**: ứng dụng web cục bộ (backend + frontend trong Docker) + agent macOS + app Tauri.

**Performance Goals**: tô sáng/xem trước < 0,1 s mỗi phím (SC-005); tìm kiếm < 0,3 s mỗi phím trên 1.000 task
(SC-008); khôi phục một học kỳ < 1 phút (SC-002); bản bù < 5 phút sau khi Mac thức (SC-001).

**Constraints**: chỉ kết nối `127.0.0.1`; ghi file sao lưu theo ngoại lệ 2 của constitution IV (2.3.1: chỉ đọc file ngoài thư mục sao lưu khi người dùng chủ động chọn để khôi phục); không
AI/internet cho hiểu câu; tiếng Việt toàn bộ; không thêm thư viện UI.

**Scale/Scope**: 1 người dùng; ~200–1.000 task, 1 học kỳ ~100 buổi; bản sao lưu vài MB × 14; 4 đợt.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Áp dụng trong feature | Kết quả |
|------------|----------------------|---------|
| **I. Code dễ đọc** | Mọi quyết định khó là hàm thuần nhỏ có tên rõ: `backup_due`, `stale_notice_due`, `prune`, `parseQuickAdd` (tách `tokenize`/`resolve`/`buildTitle`), `foldVi`, `next_due`, `occurrences`, `shift_rule`, `describeRule` | PASS |
| **II. Test chức năng chính** | Sao lưu/khôi phục (pytest + persistence), bộ hiểu câu ≥ 400 ca, tìm kiếm, task lặp (hàm thuần + API), test hồi quy cho lịch/tóm tắt; một lệnh `./scripts/test.sh` | PASS |
| **III. Giao diện đơn giản** | Một mục Sao lưu trong Cài đặt; cảnh báo nhẹ không chặn; ô tìm và xem trước gọn; trình chỉnh lặp trong popover; không thư viện UI mới | PASS |
| **IV. Offline trên Mac** | Mọi kết nối vẫn là localhost; file sao lưu ghi vào thư mục trên máy, iCloud do macOS đồng bộ — đúng **ngoại lệ 2** (constitution 2.3.1); "Chọn bản sao lưu khác…" chỉ ĐỌC đúng file người dùng chọn qua hộp chọn file, không đụng file nào khác ngoài thư mục sao lưu; hiểu câu chạy trong trình duyệt; tìm kiếm trong CSDL cục bộ; thông báo là thông báo cục bộ của macOS | PASS |
| **V. Dữ liệu bền vững** | Sao lưu tự động là chính mục tiêu của nguyên tắc này; ghi file tạm + `os.replace`; khôi phục `--single-transaction` (trọn vẹn hoặc giữ nguyên) và luôn có bản "Trước khi khôi phục"; README cập nhật vị trí bản sao lưu | PASS |
| **VI. Tiếng Việt** | Mọi chữ qua `i18n/vi.ts`; thông báo macOS, lỗi agent, nội dung hộp thoại bằng tiếng Việt; ngày giờ định dạng Việt Nam; tìm kiếm và hiểu câu đúng với chữ có/không dấu | PASS |
| Ràng buộc bổ sung: YAGNI, ít phụ thuộc | Không thư viện hiểu ngày giờ, không RRULE; 3 phụ thuộc mới có lý do ở Complexity Tracking | PASS |

**Re-check sau Phase 1**: data-model thêm 4 bảng (3 cho sao lưu, 1 cho task lặp) và 4 cột ở `tasks`; contracts
không mở kênh kết nối nào ngoài localhost; ba lệnh Tauri mới chỉ cấp cho origin `127.0.0.1:8080` và có kiểm tra
đầu vào; agent chỉ đọc/ghi/xoá file khớp mẫu tên của nó (đúng điều kiện của ngoại lệ 2). Vẫn PASS.

## Project Structure

### Documentation (this feature)

```text
specs/003-backup-nl-recurring-search/
├── plan.md                      # File này
├── research.md                  # Phase 0 (R1–R19)
├── data-model.md                # Phase 1
├── quickstart.md                # Phase 1 — kịch bản B1–B10, N1–N7, S1–S5, R1–R7
├── contracts/
│   ├── rest-api.md              # /backup/*, /search, mở rộng /tasks, /calendar, /sync/changes
│   ├── agent-backup.md          # luồng và hàm thuần của agent
│   ├── quick-add-grammar.md     # ngữ pháp câu tiếng Việt
│   └── ui.md                    # Cài đặt → Sao lưu, tìm kiếm, task lặp, phím tắt, lệnh Tauri
├── checklists/requirements.md
└── tasks.md                     # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── Dockerfile                          # + postgresql-client-16 (PGDG)
├── app/
│   ├── models/backup.py                # MỚI: BackupConfig, BackupStatus, BackupJob
│   ├── models/task_series.py           # MỚI (đợt 4)
│   ├── models/task.py                  # + series_id, occurrence_no, spawned_from_task_id, trash_scope
│   ├── services/backup.py              # MỚI: dump (pg_dump + manifest + zip), restore (bảo trì, pg_restore, upgrade, giữ bảng cấu hình)
│   ├── services/backup_jobs.py         # MỚI: tạo/nhận/cập nhật việc, hết hạn việc treo
│   ├── services/search.py              # MỚI (đợt 3)
│   ├── services/task_recurrence.py     # MỚI (đợt 4): hàm thuần quy tắc lặp
│   ├── services/task_series.py         # MỚI (đợt 4): hoàn thành/bỏ hoàn thành/sửa/xoá theo phạm vi
│   ├── services/tasks.py               # + tag_names; gọi task_series khi task có chuỗi
│   ├── services/calendar.py, digest.py # + lần dự kiến (đợt 4)
│   ├── api/backup.py                   # MỚI
│   ├── api/search.py                   # MỚI
│   ├── api/maintenance.py              # MỚI: before_request trả 503 khi đang khôi phục
│   └── api/tasks.py, sync.py           # scope, recurrence; backup_jobs_pending
├── migrations/versions/0006_backup.py, 0007_search.py, 0008_recurring_tasks.py
└── tests/unit (task_recurrence, backup manifest) + tests/integration (backup_api, restore_api, search_api, task_series_api, calendar/digest projected)

mac-agent/lichhoc_agent/
├── main.py                             # luồng chính Cocoa + luồng nền; RETRY_MAX 120 s; gọi backup_tick
├── backup.py                           # MỚI: backup_due, run_backup, run_restore, prune, tên file, resolve_destination
├── icloud.py                           # MỚI: nhận diện/tải file chỉ có trên iCloud
├── notify.py                           # MỚI: stale_notice_due, gửi thông báo, xử lý click
├── backend_client.py                   # + các endpoint /backup/*
└── state.py                            # + khoá sao lưu/thông báo
mac-agent/tests/test_backup_schedule.py, test_backup_files.py, test_notify.py

frontend/src/
├── api/backup.ts, search.ts            # MỚI; tasks.ts + tag_names, scope, recurrence
├── lib/foldVi.ts                       # MỚI: gập dấu + bảng ánh xạ vị trí (dùng chung hiểu câu và tô sáng tìm kiếm)
├── features/settings/BackupSettings.tsx, RestoreDialog.tsx, RestoreOverlay.tsx   # đợt 1
├── features/tasks/quickParse/          # đợt 2: lexicon.ts, tokenize.ts, resolve.ts, title.ts, index.ts, quickParse.cases.ts, *.test.ts
├── features/tasks/QuickAdd.tsx         # lớp tô sáng, xem trước, gợi ý # ~
├── features/search/                    # đợt 3: SearchBox.tsx, SearchResults.tsx, highlight.ts
├── features/tasks/recurrence/          # đợt 4: RecurrenceEditor.tsx, ScopeDialog.tsx, describeRule.ts
├── features/calendar/toCalendarEvents.ts  # + projected_task
├── app/IconRail.tsx                    # chấm cảnh báo trên Cài đặt
├── app/desktopBridge.ts                # + pickBackupFolder, pickBackupFile, revealInFinder
└── app/shortcutsTable.ts, i18n/vi.ts   # ⌘F; chữ mới

desktop/src-tauri/
├── Cargo.toml                          # + tauri-plugin-dialog, tauri-plugin-deep-link
├── capabilities/backup.json            # MỚI: 3 lệnh cho origin 127.0.0.1:8080
├── tauri.conf.json                     # deep link scheme `lichhoc`
└── src/backup_cmds.rs, deep_link.rs    # MỚI (+ test cho kiểm tra đường dẫn)

scripts/test-persistence.sh, validate.sh   # + vòng sao lưu/khôi phục; backup-stale; search-perf
README.md                                   # sao lưu tự động, vị trí bản, khôi phục, quyền macOS
```

**Structure Decision**: Giữ cấu trúc 5 thành phần của feature 002 (backend, frontend, mac-agent, desktop,
scripts). Mã mới đặt theo feature (`features/search`, `features/tasks/quickParse`, `features/tasks/recurrence`)
và theo vai trò ở backend (`services/backup*.py`, `services/task_*.py`). Không có thành phần mới.

## Đợt triển khai (đầu vào cho /speckit-tasks)

1. **Đợt 1 — Sao lưu và khôi phục** (US1, US2; FR-001…FR-014):
   spike agent hai luồng + thông báo (R10) → Dockerfile `postgresql-client-16` → migration `0006_backup` →
   `services/backup.py` (dump/restore, chế độ bảo trì, giữ bảng cấu hình) + API → agent `backup.py`, `icloud.py`,
   `notify.py`, sửa `main.py` → Tauri: dialog, deep link, 3 lệnh, capability → giao diện Cài đặt → Sao lưu,
   khôi phục, lớp phủ, chấm cảnh báo → `test-persistence.sh`, README.
2. **Đợt 2 — Thêm nhanh tự nhiên** (US4 trừ phần lặp; FR-026…FR-035):
   `foldVi` → `quickParse` + bộ test ≥ 400 ca (gồm cả ca lặp, chạy với `recurrence: true`) → `tag_names` ở
   backend → QuickAdd: lớp tô sáng, xem trước, huỷ hiểu, gợi ý `#`/`~`, IME. Giao diện chạy với
   `recurrence: false`.
3. **Đợt 3 — Tìm kiếm** (US5; FR-036…FR-043):
   migration `0007_search` (`unaccent`, `vn_fold`) + test đối chiếu với `foldVi` → `services/search.py` +
   `/search` → SearchBox (⌘F), SearchResults (nhóm, tô sáng, Xem thêm, Gồm cả đã hoàn thành), điều hướng tới
   chi tiết/danh sách/nhãn → `validate.sh search-perf`.
4. **Đợt 4 — Task lặp** (US3; FR-015…FR-025 + cụm lặp của US4):
   `task_recurrence.py` (hàm thuần, test trước) → migration `0008_recurring_tasks` → `task_series.py`
   (hoàn thành, bỏ hoàn thành, scope, FR-020a, Thùng rác) + API → calendar/digest lần dự kiến → giao diện:
   RecurrenceEditor, ScopeDialog, biểu tượng ↻, khối dự kiến, kéo thả có scope → bật `recurrence: true` trong
   QuickAdd → kiểm tra sao lưu/khôi phục có chuỗi lặp.

Mỗi đợt: `./scripts/test.sh` pass → commit → hướng dẫn thử bằng tiếng Việt (theo quickstart).

## Rủi ro chính

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Agent chuyển sang hai luồng (Cocoa + nền) làm hỏng đồng bộ EventKit | Spike đầu đợt 1; nếu thất bại dùng `osascript` cho thông báo (không mở được Cài đặt khi bấm) và ghi lệch vào bảng dưới |
| macOS (TCC) chặn agent ghi iCloud Drive/ổ rời, hỏi lại quyền sau mỗi lần build lại (ký ad-hoc) | Trạng thái `no_permission` với hướng dẫn cụ thể; README ghi bước cấp quyền |
| Nâng cấp schema của bản cũ lỗi sau khi `pg_restore` đã xong | Agent tự khôi phục lại bản "Trước khi khôi phục" (research R8); test ở T039/T041 |
| `pg_restore --clean` bị khoá bởi kết nối khác | Chế độ bảo trì + `engine.dispose()` trước khi khôi phục; test tích hợp khôi phục trong lúc có kết nối mở |
| `unaccent` (SQL) và `foldVi` (TS) gập khác nhau → tô sáng lệch | Test đối chiếu đủ 134 ký tự có dấu + `đ/Đ` |

## Complexity Tracking

| Thêm vào | Vì sao cần | Phương án đơn giản hơn bị loại vì |
|----------|------------|-----------------------------------|
| 3 bảng sao lưu (`backup_config`, `backup_status`, `backup_jobs`) | Giao diện và agent không nói chuyện trực tiếp; cấu hình/trạng thái phải sống qua khôi phục | Gộp vào `settings`: bị ghi đè khi khôi phục bản cũ (đổi thư mục, giờ sao lưu) |
| Agent chạy hai luồng | Nhận click thông báo để mở Cài đặt → Sao lưu (FR-008) | `osascript` không xử lý được click; app Tauri không chạy khi đã thoát |
| `postgresql-client-16` từ PGDG | `pg_dump` phải ≥ phiên bản server | Client 15 của Debian không dump được server 16; dump tự viết dễ thiếu bảng |
| `tauri-plugin-dialog`, `tauri-plugin-deep-link` + 3 lệnh IPC hẹp | Chọn thư mục/ổ SSD bằng hộp chọn của macOS; bấm thông báo mở đúng trang | Chỉ ô nhập đường dẫn (khó với người dùng, dễ gõ sai đường dẫn iCloud) |
| Bộ hiểu câu tự viết (~600 dòng TS) | Tiếng Việt, chạy tức thì, không AI/internet | Thư viện hiểu ngày giờ không hỗ trợ tiếng Việt |
| `task_series` với mẫu JSONB | "Chỉ lần này" không được lan sang lần sau | Sinh lần sau từ lần vừa xong: sai FR-020 |
