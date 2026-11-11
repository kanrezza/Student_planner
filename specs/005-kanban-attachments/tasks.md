---

description: "Task list — Bảng Kanban cho công việc và đính kèm file"
---

# Tasks: Bảng Kanban cho công việc và đính kèm file

**Input**: Design documents from `specs/005-kanban-attachments/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Bắt buộc theo constitution Nguyên tắc II và Nguyên tắc V (lưu trữ phải có test). Viết test trước, chạy thấy
đỏ, rồi mới cài đặt.

**Organization**: Theo user story của spec. Thứ tự phase theo độ ưu tiên: US1, US2, US4, US5 (P1) → US3, US6 (P2) → US7
(P3).

- Mọi lệnh test chạy qua `./scripts/test.sh`. Backend chạy trong Docker, mount code hiện tại.
- Không chạy `ruff format` ghi file trong container: format trên máy bằng `mac-agent/.venv/bin/ruff format`.
- Cuối mỗi phase: `./scripts/test.sh` xanh rồi commit. Commit không thêm dòng Co-Authored-By hay "Generated with Claude
  Code" (xem `CLAUDE.md`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: chạy song song được (khác file, không phụ thuộc task chưa xong)
- **[Story]**: US1…US7 theo spec
- Đường dẫn tính từ gốc repo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Phụ thuộc mới, volume, nginx, fixture.

- [X] T001 Thêm `"@dnd-kit/core": "6.3.1"`, `"@dnd-kit/sortable": "10.0.0"`, `"@dnd-kit/utilities": "3.2.2"` vào `dependencies` trong `frontend/package.json`, chạy `npm install` để cập nhật `frontend/package-lock.json`
- [X] T002 Thêm named volume `lichhoc_attachments` (khối `volumes:` có `name: lichhoc_attachments` và ghi chú như `lichhoc_pgdata`) và gắn vào service `backend` tại `/var/lib/lichhoc/attachments` trong `docker-compose.yml`. Không bind mount thư mục dự án. Thêm biến `ATTACHMENTS_DIR=/var/lib/lichhoc/attachments` và `ATTACHMENTS_DIR` mặc định trong `backend/app/config.py`. Trong `docker-compose.dev.yml` (nếu có service backend) dùng cùng volume
- [X] T003 [P] Thêm `location /api/attachments` trong `frontend/nginx.conf` với các giá trị sau (R5):
  - `client_max_body_size 510m`
  - `proxy_request_buffering off`
  - `proxy_read_timeout 300s`
  - cùng `proxy_pass`/header như `location /api/`
- [X] T004 [P] Tạo fixture giả lập trong `backend/tests/fixtures/attachments/` (không dùng tài liệu thật):
  - `anh-nho.png` (PNG 8×8)
  - `de-cuong.pdf` (PDF 2 trang, sinh bằng reportlab hoặc commit file nhỏ)
  - `bai-tap.docx` và `bang-diem.xlsx` (file Office rỗng hợp lệ)
  - `rong.txt` (0 byte)
  - `chay-thu.command` (script shell 1 dòng)
  - `gia-mao.png` (nội dung là HTML)
  - `ve.svg`

  Thêm `load_attachment(name)` vào `backend/tests/ocr_helpers.py`. Nếu dùng script để sinh file thì đặt ở `samples/synthetic/make_attachment_fixtures.py`

**Checkpoint**: `docker compose config` có volume `lichhoc_attachments`; `npm ls @dnd-kit/core` có phiên bản đã ghim.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cột/bảng mới (migration 0012), hàm thuần trạng thái + thứ tự, kho file trên đĩa. Mọi user story phụ thuộc
phase này.

### Tests (viết trước)

- [X] T005 [P] Test hàm thuần trong `backend/tests/unit/test_board_rank.py`:
  - `task_status(completed_at, in_progress)` cho cả 3 trạng thái.
  - `rank_between(before, after)`: hai đầu `None` → 0; chỉ có trên → `before + 1`; chỉ có dưới → `after − 1`; ở giữa →
    trung bình.
  - `needs_rebalance` khi khoảng `< 1e-6`.
  - `rebalance(ranks)` → 1, 2, 3… giữ thứ tự.
  - `done_window_start(now)` = 00:00 ngày (hôm nay − 6) giờ Việt Nam, kể cả quanh nửa đêm.
- [X] T006 [P] Test kho file trong `backend/tests/unit/test_attachments_store.py` (dùng `tmp_path` làm gốc):
  - `blob_path(sha)` = `<sha[0:2]>/<sha>`.
  - `store_stream(stream, max_bytes)`:
    - trả `(sha256, size)` đúng;
    - ghi qua `.incoming/` rồi `os.replace`;
    - nội dung trùng không tạo file thứ hai;
    - vượt `max_bytes` → `FileTooLarge` và `.incoming` rỗng;
    - lỗi đọc giữa chừng (stream ném lỗi) → không còn file tạm.
  - `delete_blob` xoá file.
  - `sweep(known_shas)`: xoá file lạ và file trong `.incoming` cũ hơn 1 giờ, giữ file đang dùng.
  - `detect_mime(name, head)`: PNG/JPEG/GIF/WebP/HEIC/PDF theo chữ ký; `gia-mao.png` (HTML) → không phải ảnh; SVG → `image/svg+xml`, không xem trước.
  - `is_executable(name, head)`: true với `.command .app .sh .exe .pkg .dmg` và chữ ký Mach-O/ELF/PE; false với `.pdf`.
  - `unique_display_name(name, existing)`:
    - `"a.pdf"` khi chưa có;
    - `"a (2).pdf"` khi đã có `"A.pdf"`;
    - `"a (3).pdf"` khi đã có cả `"a (2).pdf"`. Thêm test: `sweep` không xoá file mồ côi có thời gian sửa mới hơn 1 giờ (file vừa đổi tên vào chỗ nhưng dòng CSDL chưa commit).
- [X] T007 [P] Test migration trong `backend/tests/integration/test_migration_0012.py`:
  - Dựng dữ liệu ở revision `0011_periods_canonical_names`: 3 task chưa xong ở 2 danh sách, 2 task đã xong, 1 task trong
    Thùng rác.
  - `upgrade` → `in_progress = false` mọi dòng; `board_rank` tăng dần theo `sort_key` cũ trong mỗi nhóm trạng thái;
    `subject_id` NULL; có bảng `attachment_blobs`, `attachments`; `settings.attachment_max_mb = 50`,
    `backup_attachments_warn_mb = 1024`.
  - `downgrade` chạy không lỗi.

### Implementation

- [X] T008 Sửa `backend/app/models/task.py` theo [data-model](data-model.md#đổi-tasks):
  - `in_progress` boolean NOT NULL `server_default false`
  - `board_rank` double precision NOT NULL
  - `subject_id` bigint FK `subjects.id` `ON DELETE SET NULL`
  - index `(completed_at IS NULL, in_progress, board_rank)` và index `subject_id`
  - property `status`

  Sửa `backend/app/models/settings.py`:
  - `attachment_max_mb` smallint NOT NULL mặc định 50, CHECK "`BETWEEN 1 AND 500`"
  - `backup_attachments_warn_mb` integer NOT NULL mặc định 1024, CHECK "`BETWEEN 100 AND 1000000`"
- [X] T009 Tạo `backend/app/models/attachment.py`, đăng ký trong `backend/app/models/__init__.py`. Hai model:
  - `AttachmentBlob`:
    - `sha256` char(64) PK chữ thường hex
    - `size` bigint NOT NULL `>= 0`
    - `mime_type` text NOT NULL mặc định `application/octet-stream`
    - `is_executable` boolean NOT NULL mặc định false
    - `created_at`
  - `Attachment`:
    - `id`
    - `blob_sha256` FK `ON DELETE RESTRICT`
    - `task_id` / `subject_id` / `session_id` / `exam_id` FK `ON DELETE CASCADE`, CHECK "`num_nonnulls(task_id, subject_id, session_id, exam_id) = 1`"
    - `display_name` text NOT NULL "1–255 ký tự, NFC, không chứa `/` hay ký tự điều khiển"
    - `created_at`
    - index từng cột nơi gắn và index biểu thức `vn_fold(display_name)`
- [X] T010 Viết migration `backend/migrations/versions/0012_kanban_attachments.py` (down_revision `0011_periods_canonical_names`): thêm cột/bảng/index của T008–T009; đặt `board_rank` bằng `row_number()` theo thứ tự `sort_key` hiện có (hạn chót, giờ, ưu tiên, id) trong từng nhóm `completed_at IS NULL`; `downgrade` xoá theo thứ tự ngược
- [X] T011 [P] Tạo `backend/app/services/board_rank.py` (hàm thuần của T005): `task_status`, `rank_between`, `needs_rebalance`, `rebalance`, `done_window_start`
- [X] T012 [P] Tạo `backend/app/services/attachments_store.py` (hàm của T006):
  - gốc thư mục lấy từ `config.ATTACHMENTS_DIR`;
  - `store_stream` đọc từng 1 MiB, cập nhật `hashlib.sha256`, `fsync` file rồi `fsync` thư mục, `os.replace`;
  - `open_blob(sha)`, `delete_blob(sha)`, `sweep(known_shas, now)`, `detect_mime`, `is_executable`, `unique_display_name`;
  - `ENOSPC` ném `DiskFull`;
  - không log nội dung file. `sweep` chỉ xoá file không có dòng CSDL khi thời gian sửa cũ hơn 1 giờ (tránh xoá file vừa gắn).
- [X] T013 Sửa `backend/app/services/tasks.py`:
  - `create_task` (và mọi đường tạo: thêm nhanh, deadline tự tạo trong `backend/app/services/auto_deadlines.py`, lần kế
    tiếp của task lặp trong `backend/app/services/task_series.py`) đặt `board_rank = min(cột Chưa làm) − 1`.
  - `complete_task` đặt `in_progress = False`.
  - `update_task` nhận `subject_id` (kiểm tra môn tồn tại) và `status` ∈ `todo`/`doing` (không nhận `done`).
  - `serialize_task` trong `backend/app/schemas/tasks.py` thêm `status`, `board_rank`, `subject_id`,
    `effective_subject_id`, `attachment_count`. Mục đính kèm tạm trả 0 cho tới US4. PATCH `status` và `uncomplete_task` đặt `board_rank` lên đầu cột đích (FR-006).
- [X] T014 Gọi `attachments_store.sweep` khi backend khởi động (`backend/app/__init__.py`, cạnh dọn cờ bảo trì) và mỗi ngày một lần theo kiểu `purge_expired_trash_throttled`. Chưa có bảng blob thì bỏ qua

**Checkpoint**: `./scripts/test.sh` xanh (kể cả test cũ của task, lặp, deadline tự tạo, Hôm nay); migration chạy trên DB thật sau khi `./scripts/backup.sh`. Commit.

---

## Phase 3: User Story 1 - Xem và chuyển task trên bảng Kanban (Priority: P1) 🎯 MVP

**Goal**: Trang Công việc có dạng Bảng 3 cột. Kéo thả đổi trạng thái và thứ tự. Kéo sang Xong tương đương tick, có
Hoàn tác. Cột Xong chỉ hiện 7 ngày.

**Independent Test**: Tạo 3 task; ở dạng Bảng kéo 1 sang Đang làm, 1 sang Xong, đổi thứ tự cột Chưa làm; tải lại thì
giữ nguyên; dạng Danh sách thấy task Xong đã tick.

### Tests for User Story 1

- [X] T015 [P] [US1] Test API trong `backend/tests/integration/test_board_api.py`:
  - `GET /tasks/board`:
    - 3 cột sắp theo `board_rank`;
    - cột `done` chưa sắp tay thì theo `completed_at` giảm dần;
    - `done_window=7d` ẩn task xong 10 ngày trước và trả `done_hidden_count`; `all` hiện tất cả;
    - không có task trong Thùng rác.
  - `PATCH /tasks/{id}/board`:
    - todo→doing đặt `in_progress`;
    - doing→done ghi `completed_at`, `in_progress = false` và `bump_revision`, giống `POST /tasks/{id}/complete` (so
      sánh feed `/sync/changes`);
    - done→todo gỡ hoàn thành; done→doing;
    - `before_id`/`after_id` đặt đúng vị trí; thẻ `before_id` không thuộc cột đích → 400; task trong Thùng rác → 404.
  - Task lặp kéo sang done → `next_task` ở đầu cột Chưa làm. Gọi lại với `undo` → task về cột/vị trí cũ, lần kế tiếp
    chưa sửa bị gỡ.
  - Đổi chỗ 40 lần giữa hai thẻ thì cột được sắp lại, thứ tự đúng.
  - Task mới tạo nằm đầu cột Chưa làm. Thêm test: đổi trạng thái qua PATCH `/tasks/{id}` (dạng Danh sách) và bỏ tick đều đưa thẻ lên đầu cột đích.
- [X] T016 [P] [US1] Test Vitest `frontend/tests/boardState.test.ts`:
  - `groupColumns` từ phản hồi API;
  - `applyMove(columns, id, toStatus, index)` cho kết quả lạc quan đúng;
  - `neighbours(column, index)` → `before_id`/`after_id`;
  - `rollback` khi lỗi.
- [X] T017 [P] [US1] Test Vitest `frontend/tests/boardView.test.tsx` (mock API):
  - nút "Danh sách | Bảng" đổi dạng xem và nhớ vào `localStorage` khoá `lichhoc.tasks.view`;
  - 3 cột có số thẻ; cột rỗng có "Kéo thẻ vào đây";
  - chuyển thẻ (qua bàn phím của dnd-kit) gọi `PATCH /tasks/{id}/board` đúng `status`/`before_id`/`after_id`;
  - chuyển sang Xong hiện "Hoàn tác", bấm Hoàn tác gọi PATCH với `undo`;
  - lỗi PATCH thì thẻ về chỗ cũ và có thông báo;
  - "Hiện tất cả (n ẩn)" gọi lại với `done_window=all`.

### Implementation for User Story 1

- [X] T018 [US1] Tạo `backend/app/services/board.py`:
  - `board(filters, done_window, now)` truy vấn 3 cột.
  - `move(task_id, status, before_id, after_id)`:
    - kiểm tra thẻ kề thuộc cột đích;
    - chuyển trạng thái theo bảng ở [data-model](data-model.md#đổi-tasks): sang done gọi `tasks.complete_task`, rời
      done gọi `tasks.uncomplete_task`;
    - đặt `board_rank` bằng `rank_between`, sắp lại cột khi `needs_rebalance`;
    - trả `{task, next_task, undo}`.

  Mọi thay đổi trong một transaction.
- [X] T019 [US1] Tạo schema `backend/app/schemas/board.py` (`BoardMoveIn`: `status` ∈ `todo|doing|done`, `before_id?`, `after_id?`; query `done_window` ∈ `7d|all`) và API `backend/app/api/board.py` (`GET /tasks/board`, `PATCH /tasks/{id}/board`), đăng ký blueprint trong `backend/app/__init__.py`; cập nhật `specs/001-task-class-scheduler/contracts/rest-api.md` trỏ tới contract 005
- [X] T020 [P] [US1] Frontend:
  - `frontend/src/api/board.ts`: kiểu `BoardResponse`, `useBoard(filters, doneAll)`, `useMoveCard()` với cập nhật lạc
    quan và rollback.
  - `frontend/src/features/tasks/board/boardState.ts`: hàm thuần của T016.
  - `frontend/src/api/types.ts`: `Task` thêm `status`, `board_rank`, `subject_id`, `effective_subject_id`,
    `attachment_count`.
- [X] T021 [US1] Tạo `frontend/src/features/tasks/board/BoardView.tsx`, `BoardColumn.tsx`, `BoardCard.tsx`:
  - `DndContext` + `SortableContext` mỗi cột, `PointerSensor` + `KeyboardSensor` với `sortableKeyboardCoordinates`;
  - vạch chèn khi kéo, `DragOverlay`;
  - cột Xong có nút "Hiện tất cả (n ẩn)" / "Chỉ 7 ngày gần nhất" (khoá `lichhoc.board.doneAll`);
  - toast "Đã hoàn thành “…”" kèm "Hoàn tác" trong 6 giây (dùng `useToast`);
  - ô "+ Thêm" đầu cột Chưa làm/Đang làm dùng `QuickAdd`; ở Đang làm, sau khi tạo thì gọi PATCH `status: doing`;
  - chuỗi trong `frontend/src/i18n/vi.ts` (khối `board`).
- [X] T022 [US1] Thêm nút phân đoạn "Danh sách | Bảng" trong `frontend/src/features/tasks/TasksScreen.tsx` (nhớ `lichhoc.tasks.view`, bọc `localStorage` trong try/catch như `frontend/src/lib/storage.ts`). Dạng Danh sách:
  - `frontend/src/features/tasks/TaskRow.tsx` hiện nhãn nhỏ "Đang làm";
  - `frontend/src/features/tasks/TaskDetailPanel.tsx` có ô "Trạng thái" (Chưa làm / Đang làm / Xong): Xong gọi
    complete, còn lại gọi PATCH `status`.

**Checkpoint**: Quickstart K1–K4, kiểm tra tay bước 1. Commit.

---

## Phase 4: User Story 2 - Lọc bảng và đọc nhanh thông tin trên thẻ (Priority: P1)

**Goal**: Lọc theo danh sách, nhãn, môn (cả deadline tự tạo). Thẻ hiện hạn chót, nhãn, Quan trọng, lặp, số file.

**Independent Test**: Task ở 2 danh sách, có nhãn, gắn môn khác nhau → mỗi bộ lọc chỉ còn task khớp; thẻ đủ thông tin.

### Tests for User Story 2

- [X] T023 [P] [US2] Test API trong `backend/tests/integration/test_board_filters.py`:
  - `list_ids` nhiều giá trị;
  - `tag_ids` khớp bất kỳ;
  - `subject_ids` khớp `tasks.subject_id` **và** deadline tự tạo theo môn của buổi nguồn;
  - các loại lọc kết hợp "và";
  - `done_hidden_count` tính sau khi lọc;
  - `PATCH /tasks/{id}` với `subject_id` sai → 400, `null` bỏ gắn;
  - xoá môn → `subject_id` của task thành NULL;
  - 300 task + lọc < 1 giây (SC-002).
- [X] T024 [P] [US2] Test Vitest `frontend/tests/boardFilters.test.tsx` và `frontend/tests/boardCard.test.tsx`:
  - thanh lọc gửi đúng query và nhớ ở `lichhoc.board.filters`; "Bỏ lọc";
  - thẻ hiện tiêu đề (cắt 2 dòng), hạn chót đỏ khi quá hạn và cam khi hôm nay, tối đa 3 chấm nhãn + "+n", sao Quan
    trọng, biểu tượng lặp, kẹp giấy + số khi `attachment_count > 0`;
  - thẻ Xong mờ, gạch ngang;
  - bấm thẻ mở `TaskDetailPanel`.

### Implementation for User Story 2

- [X] T025 [US2] Lọc trong `backend/app/services/board.py`:
  - `list_ids`;
  - `tag_ids` (dùng `_has_any_tag` của `backend/app/services/tasks.py`);
  - `subject_ids` theo môn hiệu lực `COALESCE(tasks.subject_id, class_sessions.subject_id)` (outer join qua
    `source_session_id`).

  Query parse trong `backend/app/api/board.py` (danh sách số cách nhau dấu phẩy, sai → 400 theo tham số)
- [X] T026 [US2] Tạo `frontend/src/features/tasks/board/BoardFilters.tsx`:
  - 3 menu chọn nhiều: danh sách (`useLists`), nhãn (giống `TagFilter`), môn (`useSubjects` của học kỳ hiện tại, kèm
    "Học kỳ khác…");
  - nút "Bỏ lọc";
  - lưu `lichhoc.board.filters`.

  Hoàn thiện `BoardCard.tsx` theo [contracts/ui.md](contracts/ui.md): dùng lại `formatDue`, chấm màu nhãn, dấu Quan
  trọng của `TaskRow`; `IconPaperclip` trong `frontend/src/ui/icons.tsx`.
- [X] T027 [US2] Ô "Môn học" trong `frontend/src/features/tasks/TaskDetailPanel.tsx`:
  - chọn môn của học kỳ hiện tại hoặc "Không gắn môn";
  - deadline tự tạo hiện môn của buổi, chỉ đọc.

**Checkpoint**: Quickstart K5, kiểm tra tay bước 3. Commit.

---

## Phase 5: User Story 4 - Đính kèm file vào task, môn học, buổi học, buổi thi (Priority: P1)

**Goal**: Gắn file bằng kéo thả, chọn file, ⌘V vào 4 loại nơi gắn. Có giới hạn, có tiến trình. Nội dung trùng chỉ lưu
một lần.

**Independent Test**: Gắn 1 file vào mỗi nơi bằng 3 cách; tải lại app → còn đủ, đúng tên/dung lượng/nội dung; cùng file
gắn 2 nơi chỉ tính dung lượng một lần.

### Tests for User Story 4

- [X] T028 [P] [US4] Test API trong `backend/tests/integration/test_attachments_api.py` (đặt `ATTACHMENTS_DIR` sang `tmp_path` bằng fixture):
  - `POST /attachments` với từng `owner_type` (`task`, `subject`, `session`, `exam`) và nhiều `file` một lần → 201,
    file trong thư mục tên = sha256.
  - Cùng nội dung gắn 5 nơi → 1 blob, 5 mục, `stats.total_bytes` tăng một lần (SC-006).
  - Tên trùng khác nội dung ở cùng nơi → "(2)".
  - Vượt giới hạn: đặt `attachment_max_mb = 1` → lỗi `file_too_large` trong `errors`, file khác vẫn lưu; `.incoming`
    rỗng.
  - Nơi gắn không có / task trong Thùng rác → 400 `owner_not_found`.
  - File 0 byte → được.
  - Giả lập `DiskFull` → 507 `disk_full`, không có mục.
  - `GET /attachments?owner_type=…`.
  - `PATCH` đổi tên (rỗng, có `/` → 400).
  - `attachment_count` có trong Task / Subject / ClassSession / Exam. Thêm hai test: (1) chạy chồng, `collect_garbage` của một nội dung trong khi upload cùng nội dung vẫn cho kết quả nhất quán (blob còn file, mục trỏ đúng); (2) upload 50 MB < 5 giây (SC-005).
- [X] T029 [P] [US4] Test Vitest `frontend/tests/attachmentsSection.test.tsx` và `frontend/tests/attachmentUpload.test.ts`:
  - mục "File đính kèm · n" hiện danh sách (biểu tượng theo loại, "2,4 MB · 11/11/2026");
  - "Thêm file" chọn nhiều file;
  - thả file lên vùng thả hiện lớp phủ và gọi upload;
  - ⌘V có ảnh trong clipboard gắn ảnh (khi không gõ trong ô chữ);
  - file vượt giới hạn bị từ chối trước khi gửi với thông báo nêu giới hạn;
  - thanh tiến trình theo `upload.onprogress` (XHR giả);
  - lỗi từng file hiện dòng đỏ + "Bỏ qua";
  - kéo thư mục bị từ chối.

### Implementation for User Story 4

- [X] T030 [US4] Tạo `backend/app/services/attachments.py`:
  - `create(owner_type, owner_id, files, max_bytes)`: với mỗi file gọi `attachments_store.store_stream`, upsert
    `AttachmentBlob` (mime, `is_executable` từ 4 KB đầu), tạo `Attachment` với `unique_display_name` (NFC).
  - `list_for(owner)`, `rename`, `count_for(...)` (bỏ mục của task trong Thùng rác), `stats()`.
  - `owner_title(attachment)`. Chèn blob bằng `INSERT … ON CONFLICT DO NOTHING`, khoá dòng blob (`FOR UPDATE`) và đặt lại file nếu đang thiếu, để chạy chồng với `collect_garbage` không để mục trỏ tới blob đã bị xoá.

  Mỗi file một transaction để file lỗi không chặn file khác.
- [X] T031 [US4] Tạo schema `backend/app/schemas/attachments.py` và API `backend/app/api/attachments.py`:
  - `GET /attachments`, `GET /attachments/{id}`, `POST /attachments`, `PATCH /attachments/{id}`.
  - `POST` đặt `request.max_content_length` theo `settings.attachment_max_mb` × số file + phần đầu, đọc
    `request.files.getlist("file")` bằng `stream`, không `save()`.

  Đăng ký blueprint. Thêm `attachment_count` vào serializer của `backend/app/schemas/subjects.py`
  (`serialize_subject`, serializer buổi học), `backend/app/schemas/tasks.py` và serializer lịch thi trong
  `backend/app/services/exams.py`/`backend/app/api/exams.py` (đếm bằng một truy vấn gộp, không N+1)
- [X] T032 [P] [US4] Frontend (giao diện gửi mỗi file một yêu cầu riêng để có tiến trình và lỗi riêng từng file):
  - `frontend/src/api/attachments.ts`: kiểu `Attachment`, `useAttachments(owner)`, `useRenameAttachment`.
  - `frontend/src/features/attachments/upload.ts`: XHR, tiến trình, huỷ, kiểm tra giới hạn từ `useSettings`.
  - `frontend/src/features/attachments/attachmentFormat.ts`: biểu tượng theo MIME/phần mở rộng, dùng lại `formatSize`.
- [X] T033 [US4] Tạo `frontend/src/features/attachments/AttachmentsSection.tsx`, `AttachmentRow.tsx`, `useAttachmentDrop.ts`:
  - vùng thả phủ cả bảng chi tiết, lớp phủ "Thả để đính kèm vào …";
  - nút "Thêm file" (`input type=file multiple`);
  - ⌘V dùng `fileFromClipboard` của `frontend/src/features/imports/usePasteFile.ts` mở rộng cho nhiều file, chỉ khi
    phần tử đang focus không phải ô nhập;
  - dòng tạm khi đang tải;
  - đổi tên tại chỗ;
  - chuỗi trong khối `attachments` của `frontend/src/i18n/vi.ts`.
- [X] T034 [US4] Gắn `AttachmentsSection` vào:
  - `frontend/src/features/tasks/TaskDetailPanel.tsx` (dưới Ghi chú);
  - `frontend/src/features/subjects/SubjectForm.tsx` (chỉ khi sửa môn đã lưu);
  - `frontend/src/components/SessionDetail.tsx`;
  - `frontend/src/features/exams/ExamForm.tsx` (khi sửa buổi thi đã lưu).

  Kẹp giấy + số file ở `TaskRow.tsx`, dòng môn trong `SubjectsScreen.tsx`, dòng buổi thi trong `ExamsScreen.tsx`.

**Checkpoint**: Quickstart K6–K9, kiểm tra tay bước 4 (trừ dán file từ Finder, làm ở US5). Commit.

---

## Phase 6: User Story 5 - Xem, mở, tải về và xoá file đính kèm (Priority: P1)

**Goal**: Xem ảnh/PDF trong app; mở loại khác bằng ứng dụng macOS; tải về; xoá có xác nhận; file thực thi chỉ tải về.

**Independent Test**: Ảnh, PDF xem trong app; .docx mở bằng ứng dụng mặc định; PDF tải về có trong Tải về; xoá ảnh →
mất khỏi danh sách, tổng dung lượng giảm.

### Tests for User Story 5

- [X] T035 [P] [US5] Test API trong `backend/tests/integration/test_attachments_content.py`:
  - `GET /content`:
    - PNG/PDF → `inline`, đúng `Content-Type`, `X-Content-Type-Options: nosniff`, CSP sandbox;
    - SVG, HTML giả PNG (`gia-mao.png`), `.docx`, `.command` → `attachment`;
    - `ETag` = sha256; `Range: bytes=0-99` → 206.
  - `GET /download` luôn `attachment` với `filename*` UTF-8 (tên có dấu).
  - `.command` có `is_executable = true`.
  - `DELETE /attachments/{id}`:
    - 204; blob còn khi nơi khác dùng;
    - xoá nơi cuối thì file biến khỏi thư mục và dòng blob mất;
    - `stats.total_bytes` giảm.
- [X] T036 [P] [US5] Test Vitest `frontend/tests/attachmentPreview.test.tsx`:
  - ảnh mở khung xem có +/−/1:1, Esc đóng;
  - "‹ ›" chuyển file cùng nơi gắn;
  - PDF dùng `<iframe>` trỏ `content_url`;
  - loại khác: trong app macOS (mock `window.__TAURI__.core.invoke`) gọi `open_attachment`, trên trình duyệt tạo link
    tải về;
  - file thực thi không có "Mở", có cảnh báo;
  - "Tải về" trong app gọi `save_attachment` và hiện "Đã lưu vào Tải về" + "Hiện trong Finder";
  - Xoá hỏi xác nhận rồi gọi DELETE.
- [X] T037 [P] [US5] Test `cargo test` trong `desktop/src-tauri/src/attachments.rs`:
  - `unique_download_path` thêm " (2)", " (3)";
  - `cache_path(sha, name)` không thoát khỏi thư mục cache (tên có `../` bị làm sạch);
  - `refuse_executable` theo metadata;
  - `parse_clipboard_paths` từ đầu ra `osascript` (nhiều file, tên có dấu, rỗng). Thêm test: hàm dựng URL chỉ chấp nhận `http://127.0.0.1:8080`, từ chối host khác (FR-029).

### Implementation for User Story 5

- [X] T038 [US5] API trong `backend/app/api/attachments.py`:
  - `GET /attachments/{id}/content` và `GET /attachments/{id}/download`: `send_file` từ volume với `conditional=True`,
    header R8, `inline` chỉ cho MIME an toàn.
  - `DELETE /attachments/{id}`.
  - `GET /attachments/stats`.

  Thêm `collect_garbage(shas)` vào `backend/app/services/attachments.py`: sau commit, xoá blob không còn mục nào (kể cả
  mục của task trong Thùng rác), rồi xoá file; lỗi xoá file chỉ ghi log.
- [X] T039 [US5] Tạo lệnh Tauri trong `desktop/src-tauri/src/attachments.rs` theo [contracts/desktop-commands.md](contracts/desktop-commands.md): `open_attachment`, `save_attachment`, `clipboard_file_paths`, `upload_paths`. Cách làm:
  - dùng `/usr/bin/curl --fail`, `/usr/bin/open`, `osascript`; chỉ gọi `http://127.0.0.1:8080`;
  - cache `~/Library/Caches/<bundle-id>/attachments/`, dọn mục > 7 ngày khi khởi động;
  - lỗi trả chuỗi tiếng Việt.

  Đăng ký lệnh trong `desktop/src-tauri/src/main.rs` (hoặc `lib.rs`). Tạo `desktop/src-tauri/capabilities/attachments.json`
  (chỉ `remote.urls: ["http://127.0.0.1:8080/*"]`, cửa sổ `main`, 4 quyền `allow-…`) và file quyền tương ứng như cách
  làm của capability `backup`.
- [X] T040 [US5] Tạo `frontend/src/features/attachments/AttachmentPreview.tsx` (Dialog lớn: ảnh có phóng to/kéo, PDF `<iframe>`, "‹ ›", Tải về, Mở bằng ứng dụng khác, Esc) và `frontend/src/features/attachments/desktop.ts`:
  - phát hiện app macOS qua `window.__TAURI__`;
  - bọc `invoke` cho 4 lệnh;
  - dự phòng trên trình duyệt bằng `<a download>`.

  Menu ⋯ của `AttachmentRow.tsx` có Xem/Mở, Tải về, Đổi tên, Xoá (ConfirmDialog "Xoá file “…” khỏi …?"). Với file thực
  thi: ẩn Mở, hiện biểu tượng cảnh báo + tooltip.
- [X] T041 [US5] ⌘V file chép từ Finder trong app macOS:
  - trong `useAttachmentDrop.ts`, nếu clipboard không có `File` thật thì gọi `clipboard_file_paths` rồi `upload_paths`,
    hiện lỗi theo từng file.
  - Spike R10: thử dán file thật trong WKWebView. Nếu WebView đã đưa `File` thì dùng luôn, ghi kết quả vào
    `specs/005-kanban-attachments/validation.md`.
  - Spike R8: thử PDF trong `<iframe>` trong app. Không hiện thì mở PDF bằng cửa sổ Tauri phụ.

**Checkpoint**: Quickstart K16, kiểm tra tay bước 4–5. Commit.

---

## Phase 7: User Story 3 - Dùng bảng bằng bàn phím (Priority: P2)

**Goal**: Mọi thao tác trên bảng làm được bằng phím, có thông báo cho trình đọc màn hình.

**Independent Test**: Chỉ bàn phím: chọn thẻ, ⌘→ hai lần → Xong; ⌘↑ đổi chỗ; Enter mở chi tiết; X bỏ Xong.

### Tests for User Story 3

- [X] T042 [P] [US3] Test Vitest `frontend/tests/boardKeys.test.tsx`:
  - mũi tên di chuyển vùng chọn: trái/phải đổi cột, giữ vị trí gần nhất; lên/xuống trong cột;
  - ⌘←/⌘→ gọi PATCH đổi cột, thẻ vẫn được chọn;
  - ⌘↑/⌘↓ đổi chỗ (PATCH với `before_id`/`after_id` đúng); không đi quá đầu/cuối cột;
  - Enter mở chi tiết; X Xong/bỏ Xong;
  - vùng `aria-live` đọc "Đã chuyển “…” sang Đang làm, vị trí 2 trên 5";
  - phím không kích hoạt khi đang gõ trong ô thêm nhanh;
  - các phím có trong bảng phím tắt (`?`).

### Implementation for User Story 3

- [X] T043 [US3] Tạo `frontend/src/features/tasks/board/useBoardKeys.ts` (vùng chọn, phím tắt, dùng `isTypingTarget` của `frontend/src/app/useHotkeys.ts`, kiểm tra không trùng phím tắt toàn cục), dùng trong `BoardView.tsx`. Thêm `announcements` + `screenReaderInstructions` tiếng Việt cho `DndContext`. Thêm mục "Bảng công việc" vào danh sách phím tắt hiện có (nơi định nghĩa bảng `?`) và chuỗi trong `frontend/src/i18n/vi.ts`

**Checkpoint**: Kiểm tra tay bước 2. Commit.

---

## Phase 8: User Story 6 - File đi theo Thùng rác, sao lưu và tìm kiếm (Priority: P2)

**Goal**: Thùng rác giữ file, xoá hẳn thì dọn. Xoá môn/buổi thi cần xác nhận. File của buổi bị xoá chuyển sang môn.
Sao lưu gồm file. ⌘F tìm tên file.

**Independent Test**: Task có file → Thùng rác → khôi phục → còn file; xoá hẳn → blob bị dọn; sao lưu + khôi phục →
mọi file mở được; ⌘F "de cuong" tìm ra file.

### Tests for User Story 6

- [X] T044 [P] [US6] Test trong `backend/tests/integration/test_attachments_lifecycle.py`:
  - Task có 2 file → `DELETE /tasks/{id}` (Thùng rác): mục ẩn khỏi `GET /attachments`, tìm kiếm, `stats`, nhưng blob
    còn. Khôi phục → hiện lại đủ.
  - `delete_permanently`, `empty_trash`, `purge_expired_trash` → mục bị xoá, blob bị dọn trừ blob nơi khác dùng
    (SC-008).
  - `DELETE /subjects/{id}` có file ở môn và buổi, không `confirm` → 409 `confirm_required` với `attachment_count`;
    `confirm=true` → xoá + dọn.
  - Tương tự `DELETE /exams/{id}`.
  - `PATCH /subjects/{id}` đổi thứ làm mất buổi có file → file chuyển sang môn, `warnings` có `attachments_moved`.
  - Nhập lại lịch thi trùng (ảnh) → file của buổi thi giữ nguyên.
  - `sweep` dọn file lạ và `.incoming` cũ. Thêm test: xoá học kỳ và thu hẹp học kỳ làm môn bị xoá, khi có file đính kèm → 409 `confirm_required` kèm `attachment_count`; có `confirm` thì xoá và dọn blob.
- [X] T045 [P] [US6] Test sao lưu trong `backend/tests/integration/test_backup_attachments.py` (dùng `isolated_app` của feature 003, `ATTACHMENTS_DIR` riêng):
  - `build_backup` tạo ZIP format 2 có `attachments/<sha>` cho mọi blob đang dùng (kể cả của task trong Thùng rác) và
    manifest `attachments.count/bytes`.
  - Xoá DB + thư mục, khôi phục → mọi file có lại, SHA-256 khớp (SC-007).
  - Khôi phục bản format 1 → chạy được, blob không còn tham chiếu bị dọn.
  - Bản có blob bị sửa → `backup_corrupt`, dữ liệu và file hiện tại nguyên vẹn, `.restore` được dọn.
  - Lỗi sau khi nạp dump → hoàn tác, file cũ còn.
  - `GET /backup/status` có `attachments_bytes`, `estimated_backup_bytes`, `attachments_warning` (đặt ngưỡng 100 MB rồi
    vượt).
- [X] T046 [P] [US6] Test tìm kiếm trong `backend/tests/integration/test_search_files.py`:
  - nhóm `files` khớp "de cuong" với "Đề cương NLP.pdf" (NFD từ Finder cũng khớp);
  - `owner` đúng cho cả 4 loại nơi gắn;
  - file của task trong Thùng rác không có;
  - `group=files`;
  - 1.000 mục < 1 giây (SC-009).
- [X] T047 [P] [US6] Test agent trong `mac-agent/tests/test_backup_attachments_warning.py`: sau sao lưu tự động khi `attachments_warning = true` → gửi một thông báo nhẹ, không quá 1 lần/ngày; `false` → không gửi
- [X] T048 [P] [US6] Test Vitest `frontend/tests/searchFiles.test.tsx`:
  - nhóm "File" có tên tô phần khớp và dòng phụ nơi gắn;
  - chọn kết quả điều hướng tới nơi gắn kèm `?attachment=<id>`, dòng file được nháy sáng;
  - hộp xác nhận xoá môn/buổi thi có "và n file đính kèm" khi API trả 409.

### Implementation for User Story 6

- [X] T049 [US6] Vòng đời:
  - Lọc mục của task trong Thùng rác ở `backend/app/services/attachments.py` (`list_for`, `count_for`, `stats`).
  - Gọi `collect_garbage` sau `delete_permanently`, `empty_trash`, `purge_expired_trash` trong
    `backend/app/services/tasks.py`, sau xoá môn trong `backend/app/services/subjects.py`, sau xoá buổi thi trong
    `backend/app/services/exams.py`. Lấy danh sách sha trước khi xoá.
  - `delete_subject`/`delete_exam` nhận `confirm`; API `backend/app/api/subjects.py`, `backend/app/api/exams.py` trả
    409 `confirm_required` kèm `attachment_count`. `delete_semester` và `update_semester` (thu hẹp, `clamp_subjects`) trong `backend/app/services/semesters.py` đếm file của các môn/buổi bị xoá, trả 409 `confirm_required` kèm `attachment_count` khi thiếu xác nhận, rồi gọi `collect_garbage` sau commit; giao diện học kỳ (`frontend/src/features/settings/SemestersSettings.tsx`) hiện số file trong hộp xác nhận.
- [X] T050 [US6] Trong `regenerate_sessions` của `backend/app/services/subjects.py`, trước khi xoá buổi theo `plan.to_delete`: chuyển mục đính kèm của các buổi đó sang `subject_id` của môn (`session_id = NULL`). Trả cảnh báo `attachments_moved` qua `_warnings` / kết quả nhập PDF trong `backend/app/services/timetable_import.py`
- [X] T051 [US6] Sao lưu format 2 trong `backend/app/services/backup.py` theo [data-model](data-model.md#bản-sao-lưu-lhbackup-format-2-r7):
  - `MANIFEST_FORMAT = 2`, nhận cả 1 và 2 khi mở.
  - `build_backup` ghi `attachments/<sha>` từ volume và thêm `attachments.count/bytes`.
  - `_open_backup` kiểm tra tên mục là sha hợp lệ, giải nén vào `<ATTACHMENTS_DIR>/.restore/<uuid>/` và kiểm tra
    SHA-256 từng file.
  - `_restore_in_maintenance`: sau khi nạp dump + nâng cấp thành công thì `os.replace` blob còn thiếu vào chỗ rồi
    `sweep`; lỗi thì xoá `.restore`.
  - `GET /backup/status` (`backend/app/services/backup_jobs.py`) thêm `attachments_bytes`, `estimated_backup_bytes`,
    `attachments_warning`. Thứ tự khôi phục: giải nén vào `.restore` → nạp dump + nâng cấp schema → `os.replace` blob vào chỗ → commit; chỉ quét dọn sau khi mọi bước thành công. Lỗi ở bước chuyển blob thì nạp lại `safety.dump`; blob cũ còn nguyên vì chưa bị xoá.
- [X] T052 [US6] Agent: trong `mac-agent/lichhoc_agent/backup.py`, sau sao lưu tự động thành công đọc `attachments_warning` từ status và gọi `notify` (tối đa 1 lần/ngày, nhớ trong `state.py`), chuỗi tiếng Việt "File đính kèm đang chiếm 1,2 GB; mỗi bản sao lưu khoảng 1,3 GB."
- [X] T053 [US6] Thêm nhóm `files` vào `backend/app/services/search.py` (`GROUPS`, truy vấn theo `vn_fold(display_name)`, bỏ task trong Thùng rác, `owner` qua `owner_title`). Frontend:
  - `frontend/src/features/search/SearchResults.tsx`: nhóm "File" có biểu tượng kẹp giấy, dòng phụ nơi gắn; chọn thì
    điều hướng kèm `?attachment=<id>`.
  - `AttachmentsSection.tsx` đọc tham số đó để cuộn tới dòng file và nháy sáng 2 giây.
  - Hộp xác nhận xoá môn (`frontend/src/features/subjects/SubjectsScreen.tsx`) và buổi thi
    (`frontend/src/features/exams/ExamsScreen.tsx`) xử lý 409 `confirm_required`.
  - Cài đặt → Sao lưu (`frontend/src/features/settings/BackupSettings.tsx`) hiện cảnh báo vàng khi
    `attachments_warning`.

**Checkpoint**: Quickstart K10–K15, kiểm tra tay bước 6, 9. Commit.

---

## Phase 9: User Story 7 - Quản lý dung lượng và giới hạn trong Cài đặt (Priority: P3)

**Goal**: Mục Cài đặt "File đính kèm" có tổng dung lượng, số file, 10 file lớn nhất, giới hạn mỗi file, ngưỡng cảnh báo.

**Independent Test**: Gắn vài file → số liệu khớp; đổi giới hạn 10 MB → file 20 MB bị từ chối.

### Tests for User Story 7

- [X] T054 [P] [US7] Test trong `backend/tests/integration/test_attachments_settings.py`:
  - `PATCH /settings` với `attachment_max_mb` 0, 501 → 400 theo trường; 10 → upload 20 MB bị từ chối, file đã gắn
    không đổi;
  - `backup_attachments_warn_mb` 99 → 400;
  - `GET /attachments/stats`: `total_bytes` gộp bản trùng, `blob_count`, `attachment_count`, `largest` 10 mục giảm dần
    kèm `owner`.
- [ ] T055 [P] [US7] Test Vitest `frontend/tests/attachmentsSettings.test.tsx`:
  - hiện "Tổng dung lượng: 1,2 GB · 86 file" và bảng 10 file lớn nhất (bấm mở nơi gắn);
  - sửa giới hạn gọi `PATCH /settings`;
  - lỗi ngoài khoảng hiện dưới ô.

### Implementation for User Story 7

- [X] T056 [US7] Thêm `attachment_max_mb` (1–500) và `backup_attachments_warn_mb` (100–1000000) vào schema/serializer settings trong `backend/app/schemas/settings.py` và `backend/app/api/settings.py`
- [ ] T057 [US7] Tạo `frontend/src/features/settings/AttachmentsSettings.tsx` theo [contracts/ui.md](contracts/ui.md), đăng ký mục `{slug: 'file-dinh-kem'}` trong `frontend/src/features/settings/SettingsScreen.tsx`, kiểu settings trong `frontend/src/api/settings.ts`, chuỗi trong `frontend/src/i18n/vi.ts`

**Checkpoint**: Quickstart kiểm tra tay bước 7. Commit.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [ ] T058 [P] Mở rộng test lưu trữ:
  - `scripts/persistence_check.py` và `scripts/test-persistence.sh`: tạo task "Đang làm" có `board_rank` và một file
    đính kèm có tiền tố `__persist_test__`;
  - kiểm tra sau `docker compose down/up` và sau `kill` vẫn còn trạng thái, thứ tự, file (SHA-256 khớp);
  - dọn khi xong (constitution V, SC-003).
- [ ] T059 [P] Cập nhật `README.md`:
  - mục "Công việc" thêm dạng Bảng và phím tắt;
  - mục "File đính kèm": cách gắn/xem/mở/tải, giới hạn, file thực thi;
  - mục "Dữ liệu nằm ở đâu": volume `lichhoc_attachments`, cách xem dung lượng (`docker system df -v`), không xoá bằng
    `docker compose down -v`, sao lưu gồm cả file;
  - bảng xử lý sự cố: "Ổ đĩa không đủ chỗ", "Không xem trước được PDF".
- [ ] T060 [P] Cập nhật `specs/001-task-class-scheduler/data-model.md` (ghi chú cột mới của `tasks`) và `specs/003-backup-nl-recurring-search/` contract sao lưu (ghi chú format 2 trỏ tới data-model 005)
- [ ] T061 Chạy `./scripts/test.sh --ocr` toàn bộ; sửa mọi lỗi (lưu ý: fixture mới không được đặt tên `*.expected.json` trong `backend/tests/fixtures/timetables/`)
- [ ] T062 Kiểm tra tay theo `specs/005-kanban-attachments/quickstart.md` trên app macOS, gồm:
  - ⌘V file từ Finder;
  - PDF trong `<iframe>`;
  - tháo ổ SSD thì app vẫn xem được file. Thêm: cuộn bảng 200+ thẻ không giật, mở app và trình duyệt cùng lúc thấy thay đổi sau khi làm mới, đo xem trước ảnh/PDF < 10 MB dưới 2 giây (SC-005).

  Ghi kết quả vào `specs/005-kanban-attachments/validation.md`. Sau đó `./scripts/backup.sh`, rồi
  `docker compose build backend web && docker compose up -d`, rồi kiểm tra
  `docker volume inspect lichhoc_attachments`. Build lại app Tauri nếu có lệnh mới.
- [ ] T063 Kiểm tra trước commit cuối:
  - `git ls-files samples` chỉ có `samples/synthetic/`;
  - không commit tài liệu cá nhân thật;
  - lịch sử không có Co-Authored-By hay tác giả Claude;
  - cập nhật **Status** trong `specs/005-kanban-attachments/spec.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → các user story.
- **US1 (Phase 3)** cần Phase 2.
- **US2 (Phase 4)** cần US1, vì dùng chung `board.py` và `BoardView`/`BoardCard`.
- **US4 (Phase 5)** chỉ cần Phase 2, độc lập với US1/US2. Số file trên thẻ chỉ hiện ra khi đã có cả US2 và US4.
- **US5 (Phase 6)** cần US4.
- **US3 (Phase 7)** cần US1.
- **US6 (Phase 8)** cần US4 và US5 (`collect_garbage`).
- **US7 (Phase 9)** cần US4 (`stats`, giới hạn).
- **Polish (Phase 10)** làm sau cùng.

### Within Each Story

- Test viết trước và chạy thấy đỏ → hàm thuần → service → API → frontend.
- Commit sau mỗi checkpoint khi `./scripts/test.sh` xanh.

### Parallel Opportunities

- Phase 1: T003, T004 song song với T001–T002.
- Phase 2: T005–T007 song song. T011 và T012 song song sau khi có test.
- Sau Phase 2 có hai nhánh độc lập:
  - **Kanban**: US1 → US2 → US3;
  - **Đính kèm**: US4 → US5 → US6 → US7.
- Hai nhánh chỉ cùng sửa `TaskDetailPanel.tsx`, `TaskRow.tsx`, `backend/app/schemas/tasks.py`; các file này làm tuần
  tự.
- Trong mỗi story các test [P] chạy song song. T020 song song với T018–T019. T032 song song với T030–T031. T037 song
  song với T035–T036.

---

## Parallel Example: User Story 4

```text
Task: "T028 Test API đính kèm trong backend/tests/integration/test_attachments_api.py"
Task: "T029 Test Vitest frontend/tests/attachmentsSection.test.tsx + attachmentUpload.test.ts"
# sau khi test đỏ:
Task: "T030 backend/app/services/attachments.py" → "T031 API + serializer attachment_count"
Task: "T032 frontend/src/api/attachments.ts + upload.ts + attachmentFormat.ts"   # song song với T030–T031
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 + Phase 2 (migration, trạng thái, thứ tự, kho file).
2. Phase 3 (US1): dạng Bảng 3 cột, kéo thả, Xong = tick, Hoàn tác.
3. **Dừng và kiểm chứng**: quickstart K1–K4 + kiểm tra tay bước 1.

### Incremental Delivery

1. US1 → US2 (lọc + thẻ): Kanban dùng được hằng ngày.
2. US4 → US5: đính kèm dùng được (gắn, xem, mở, tải, xoá).
3. US3 (bàn phím), US6 (Thùng rác, sao lưu, tìm kiếm). Phải xong US6 trước khi dùng đính kèm với tài liệu quan trọng,
   vì sao lưu mới gồm file.
4. US7 (Cài đặt) → Polish (test lưu trữ, README, build lại Docker và app).

### Lưu ý an toàn dữ liệu

- Trước khi build lại Docker với migration 0012: `./scripts/backup.sh` (sao lưu ra ngoài thư mục dự án).
- Không chạy `docker compose down -v`, vì lệnh này xoá cả `lichhoc_pgdata` lẫn `lichhoc_attachments`.
