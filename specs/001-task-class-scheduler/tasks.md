---

description: "Task list for Lịch Học Cá Nhân (001-task-class-scheduler)"
---

# Tasks: Quản lý công việc và lịch học cá nhân

**Input**: Design documents from `/specs/001-task-class-scheduler/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/rest-api.md](contracts/rest-api.md),
[contracts/calendar-sync.md](contracts/calendar-sync.md), [quickstart.md](quickstart.md)

**Tests**: BẮT BUỘC cho chức năng chính, theo constitution Nguyên tắc II và lựa chọn pytest của
người dùng. Trong mỗi story, viết test trước; test phải FAIL trước khi cài đặt.

**Organization**: Nhóm theo user story, theo thứ tự ưu tiên trong spec:
- P1: US1 → US2 → US3
- P2: US4 → US5 → US8 → US9 → US6
- P3: US10 → US7

Toàn bộ bảng dữ liệu được tạo trong Phase 2 bằng một migration duy nhất, vì các bảng có khoá ngoại
đan xen (xem data-model.md). Các phase user story chỉ thêm service, API và giao diện.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Chạy song song được (khác file, không phụ thuộc task chưa xong)
- **[Story]**: User story của task (US1…US10)

## Path Conventions

- Backend: `backend/app/`, test ở `backend/tests/`
- Frontend: `frontend/src/`, test ở `frontend/tests/`
- Agent macOS: `mac-agent/lichhoc_agent/`, test ở `mac-agent/tests/`
- Chuỗi hiển thị cho người dùng luôn bằng tiếng Việt và nằm trong `frontend/src/i18n/vi.ts`
  (frontend) hoặc trong `message` của lỗi API (backend). Múi giờ luôn là `Asia/Ho_Chi_Minh`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo dự án, công cụ, Docker; chạy 2 spike rủi ro.

- [X] T001 Tạo cấu trúc thư mục đúng như plan.md (`backend/app/{models,api,schemas,services,ocr,lib}`,
  `backend/tests/{unit,integration,ocr,fixtures/timetables}`, `backend/migrations`,
  `frontend/src/{api,i18n,lib,reminders,components,pages}`, `frontend/tests`,
  `mac-agent/{lichhoc_agent,launchd,scripts,tests}`, `scripts/`, `docker/db-init/`) và file
  `.gitignore` ở gốc. `.gitignore` bỏ qua `node_modules/`, `dist/`, `__pycache__/`, `.venv/`,
  `.pytest_cache/`, `backups/`, `*.dump`, `.env`, `mac-agent/build/`, `mac-agent/dist/`.
- [X] T002 Tạo `backend/pyproject.toml`:
  - Dependencies: Python 3.12, `flask>=3`, `flask-sqlalchemy>=3.1`, `flask-migrate>=4`,
    `psycopg[binary]>=3.1`, `pydantic>=2`, `gunicorn`, `easyocr>=1.7`, `pillow`, `pillow-heif`,
    `rapidfuzz`.
  - Dev dependencies: `pytest`, `ruff`.
  - Cấu hình ruff: `line-length = 100`, `select = ["E","F","I","B","UP"]`.
  - Cấu hình pytest: `testpaths = ["tests"]`, `markers = ["ocr: chạy EasyOCR thật trên ảnh mẫu
    (chậm)"]`, `addopts = "-m 'not ocr'"`.
- [X] T003 [P] Tạo `backend/Dockerfile`:
  - Base `python:3.12-slim`; `apt-get install libgl1 libglib2.0-0`.
  - `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`, rồi cài gói từ
    pyproject.
  - Tải model lúc build: `RUN python -c "import easyocr; easyocr.Reader(['vi','en'], gpu=False,
    model_storage_directory='/opt/easyocr-models', download_enabled=True)"`.
  - `ENV TZ=Asia/Ho_Chi_Minh EASYOCR_MODEL_DIR=/opt/easyocr-models`.
  - Tạo `backend/docker-entrypoint.sh`: chờ database (thử lại `flask db upgrade` tối đa 30 lần, cách
    nhau 1 giây), rồi `exec gunicorn -w 1 --threads 4 --timeout 120 -b 0.0.0.0:8000
    "app:create_app()"`.
- [X] T004 [P] Khởi tạo frontend trong `frontend/package.json`, `frontend/vite.config.ts`,
  `frontend/tsconfig.json`, `frontend/index.html`:
  - Dependencies: `react@18`, `react-dom@18`, `react-router-dom@6`, `@tanstack/react-query@5`,
    `@fullcalendar/core@6`, `@fullcalendar/react@6`, `@fullcalendar/daygrid@6`,
    `@fullcalendar/timegrid@6`, `@fullcalendar/interaction@6`.
  - Dev: `vite@5`, `typescript@5`, `vitest`, `jsdom`, `@testing-library/react`, `eslint`,
    `prettier`.
  - TS `strict: true`. `index.html` có `<html lang="vi">`, font hệ thống, không tải font hay CDN
    ngoài.
  - Vite dev proxy `/api` → `http://127.0.0.1:8080`.
  - Scripts: `dev`, `build`, `test` (vitest run), `lint`.
- [X] T005 [P] Tạo `frontend/Dockerfile` (build bằng `node:22-alpine` → chạy bằng
  `nginx:1.27-alpine`) và `frontend/nginx.conf`:
  - Phục vụ SPA với fallback về `index.html`.
  - `location /api/ { proxy_pass http://backend:8000; }`, `client_max_body_size 21m;`,
    `proxy_read_timeout 120s;`.
  - Riêng `location /api/sync/changes` đặt `proxy_read_timeout 35s; proxy_buffering off;`.
- [X] T006 Tạo `docker-compose.yml` và `docker/db-init/01-test-db.sql`:
  - Service `db`: `postgres:16-alpine`; `POSTGRES_DB=lichhoc`, `POSTGRES_USER=lichhoc`,
    `POSTGRES_PASSWORD=lichhoc`, `TZ=Asia/Ho_Chi_Minh`.
    - Volume `lichhoc_pgdata:/var/lib/postgresql/data` và `./docker/db-init:/docker-entrypoint-initdb.d:ro`.
    - Healthcheck `pg_isready -U lichhoc`. **Không** mở cổng.
  - Service `backend`: build `./backend`;
    `DATABASE_URL=postgresql+psycopg://lichhoc:lichhoc@db:5432/lichhoc`,
    `TEST_DATABASE_URL=postgresql+psycopg://lichhoc:lichhoc@db:5432/lichhoc_test`.
    - `depends_on: db: condition: service_healthy`. **Không** mở cổng.
  - Service `web`: build `./frontend`; `ports: ["127.0.0.1:8080:80"]`; `depends_on: [backend]`.
  - Cả ba service `restart: unless-stopped`.
  - Khai báo `volumes: lichhoc_pgdata: {name: lichhoc_pgdata}`.
  - `01-test-db.sql`: `CREATE DATABASE lichhoc_test OWNER lichhoc;`.
- [X] T007 [P] Tạo `docker-compose.dev.yml` (override): thêm service `web-dev` chạy `npm run dev --
  --host 0.0.0.0` với cổng `127.0.0.1:5173:5173` và mount `./frontend`; mount `./backend:/app` cho
  `backend`, chạy `flask run --debug -h 0.0.0.0 -p 8000`.
- [X] T008 [P] Tạo `frontend/eslint.config.js` (typescript-eslint + react-hooks) và
  `frontend/.prettierrc` (`printWidth: 100`, `singleQuote: true`).
- [X] T009 [P] Tạo `mac-agent/pyproject.toml` và `mac-agent/setup.py`:
  - Dependencies: Python 3.11 (Homebrew dạng framework, xem research R4), `pyobjc-framework-EventKit`,
    `requests`, `py2app`; dev `pytest`,
    `ruff`.
  - `setup.py` dùng py2app, `app=['lichhoc_agent/main.py']`, `name='LichHocAgent'`.
  - `plist` gồm: `CFBundleIdentifier=vn.lichhoc.agent`, `LSUIElement=True`,
    `NSCalendarsFullAccessUsageDescription` và `NSRemindersFullAccessUsageDescription` bằng tiếng
    Việt (ví dụ "Lịch Học Cá Nhân cần ghi buổi học vào Lịch để nhắc bạn trên Mac và iPhone").
- [X] T010 [P] **SPIKE S1 (research R2)**: viết `backend/spikes/ocr_spike.py`. Script chạy EasyOCR
  (`['vi','en']`, `download_enabled=False`) trên mọi ảnh trong `backend/tests/fixtures/timetables/`
  và in: số khối chữ, độ tin cậy trung bình, thời gian chạy, 30 dòng chữ đầu.
  - Cần người dùng cung cấp 3–5 ảnh chụp toàn màn hình thời khoá biểu thật, đã che họ tên và mã sinh
    viên.
  - Thử thêm `decoder='beamsearch'` và tiền xử lý (phóng to ×1.5, tăng tương phản).
  - Ghi kết quả và quyết định (giữ EasyOCR hay chuyển Apple Vision) vào mục "Kết quả spike" cuối R2
    trong `specs/001-task-class-scheduler/research.md`.
- [X] T011 [P] **SPIKE S2 (research R4)**: viết `mac-agent/spikes/eventkit_spike.py` và build thành
  `.app` bằng py2app với Info.plist ở T009, ký `codesign --force --deep -s -`. App phải:
  - Xin quyền đầy đủ cho Lịch và Lời nhắc (`requestFullAccessToEventsWithCompletion_`,
    `requestFullAccessToRemindersWithCompletion_`).
  - Tạo lịch "Lịch Học Cá Nhân (spike)" trong nguồn iCloud.
  - Tạo một `EKEvent` sau 10 phút có `EKAlarm` báo trước 5 phút, và một `EKReminder` có alarm.
  Kiểm tra sự kiện hiện trên iPhone và thông báo nổ đúng giờ. Ghi kết quả vào mục "Kết quả spike"
  cuối R4 trong research.md. Nếu thất bại sau 1 ngày, ghi quyết định chuyển sang Swift và cập nhật
  các task T134–T138 cho phù hợp.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: App Flask, database đầy đủ, xử lý lỗi, khung test, khung frontend.

**⚠️ CRITICAL**: Không user story nào bắt đầu được trước khi phase này xong.

- [X] T012 Tạo `backend/app/config.py` (đọc `DATABASE_URL`, `TEST_DATABASE_URL`,
  `EASYOCR_MODEL_DIR`; hằng `TIMEZONE = "Asia/Ho_Chi_Minh"`, `MAX_IMAGE_BYTES = 20 * 1024 * 1024`)
  và `backend/app/extensions.py` (`db = SQLAlchemy()`, `migrate = Migrate()`).
- [X] T013 Tạo `backend/app/__init__.py` với `create_app(config_overrides=None)`: khởi tạo `db`,
  `migrate`; đăng ký mọi blueprint dưới tiền tố `/api` (thêm dần theo story); đăng ký error handler
  từ T014; đặt `app.json.ensure_ascii = False`.
- [X] T014 Tạo `backend/app/api/errors.py`:
  - Lớp `ApiError(status, code, message, fields=None, details=None)`.
  - Handler trả JSON `{"error": {"code", "message", "fields"?, "details"?}}` đúng
    contracts/rest-api.md.
  - Ánh xạ `pydantic.ValidationError` → `400 validation_error`; `fields` dùng đường dẫn kiểu
    `rows[2].end_time` và thông điệp tiếng Việt.
  - `404 not_found`; lỗi không bắt được → `500` với thông điệp "Đã có lỗi xảy ra, vui lòng thử lại".
- [X] T015 [P] Tạo `backend/app/schemas/common.py`:
  - `ApiModel(BaseModel)` với `model_config = ConfigDict(str_strip_whitespace=True)`.
  - Kiểu `HHMM` (giờ dạng `HH:MM`) và hàm `vi_error_messages(errors)` chuyển lỗi pydantic sang câu
    tiếng Việt, ví dụ "Trường này là bắt buộc", "Phải dài từ 1 đến 300 ký tự".
- [X] T016 [P] Tạo `backend/app/lib/timeutil.py`:
  - `TZ = ZoneInfo("Asia/Ho_Chi_Minh")`, `now()`.
  - `combine(d: date, t: time) -> datetime` có tzinfo.
  - `iso(dt)` trả chuỗi ISO có offset `+07:00`.
  - `weekday_vn(d)` trả 1 = Thứ Hai … 7 = Chủ Nhật.
  Test trong `backend/tests/unit/test_timeutil.py`.
- [X] T017 [P] Tạo `backend/app/lib/text.py`: `nfc(s)` (chuẩn hoá Unicode NFC, bỏ khoảng trắng hai
  đầu), `ci_key(s)` (NFC + `casefold()`), `contains_ci(haystack, needle)`. Test trong
  `backend/tests/unit/test_text.py`, gồm chuỗi tiếng Việt có dấu tổ hợp (NFD) và dựng sẵn (NFC).
- [X] T018 [P] Tạo model `Semester` trong `backend/app/models/semester.py` theo data-model.md:
  - `name text` bắt buộc, "1–100 ký tự".
  - `start_date date`, `end_date date` với CHECK `end_date >= start_date`.
  - Các cột `id`, `created_at`, `updated_at` chung.
- [X] T019 [P] Tạo model `Shift` trong `backend/app/models/shift.py`:
  - `name` bắt buộc, duy nhất.
  - `start_time time`, `end_time time` với CHECK `end_time > start_time`.
  - `position smallint` duy nhất.
- [X] T020 [P] Tạo model `Subject` trong `backend/app/models/subject.py`:
  - `semester_id` FK `ON DELETE CASCADE`.
  - `name` "1–200 ký tự"; `class_code`, `lecturer`, `room` tuỳ chọn.
  - `color` (`c01`…`c12`).
  - `weekdays smallint[]` ("1 = Thứ Hai … 7 = Chủ Nhật; ≥ 1 phần tử, không trùng").
  - `start_shift_id`, `end_shift_id` FK `ON DELETE SET NULL`, CHECK "cùng NULL hoặc cùng có giá trị".
  - `start_time`, `end_time` với CHECK `end_time > start_time`.
  - `start_date`, `end_date` với CHECK `end_date >= start_date`.
  - `reminder_minutes integer` ("`NULL` = theo mặc định; `-1` = tắt nhắc; ≥ 0", CHECK
    `reminder_minutes IS NULL OR reminder_minutes >= -1`).
- [X] T021 [P] Tạo model `ClassSession` trong `backend/app/models/class_session.py`:
  - `subject_id` FK `ON DELETE CASCADE`.
  - `date`, `start_at timestamptz`, `end_at timestamptz` với CHECK `end_at > start_at`; UNIQUE
    `(subject_id, date, start_at)`.
  - `room`.
  - Các cờ boolean mặc định `false`: `is_cancelled`, `time_overridden`, `room_overridden`,
    `auto_task_suppressed`.
  - Index `(date)`, `(start_at)`.
- [X] T022 [P] Tạo model `TaskList` trong `backend/app/models/task_list.py`:
  - `name` duy nhất theo `lower(name)`.
  - `color`.
  - `is_default_study boolean`: "đúng một dòng `true`", dùng partial unique index `WHERE
    is_default_study`.
- [X] T023 [P] Tạo model `Task` trong `backend/app/models/task.py`:
  - `list_id` FK bắt buộc.
  - `title` "1–300 ký tự sau khi bỏ khoảng trắng hai đầu"; `notes`.
  - `due_date`, `due_time` với CHECK `due_time IS NULL OR due_date IS NOT NULL`.
  - `priority smallint` CHECK IN (1, 2, 3), mặc định 2.
  - `completed_at timestamptz`; `reminder_minutes` (cùng quy ước như Subject).
  - `source_session_id` FK `ON DELETE SET NULL`, UNIQUE.
  - `is_auto`, `user_modified` boolean mặc định `false`.
  - Index `(due_date)`, `(list_id)`.
- [X] T024 [P] Tạo model `Tag` và ba bảng nối trong `backend/app/models/tag.py`:
  - `tags`: `name` duy nhất theo `lower(name)`; `color`; `system_key` duy nhất, nullable.
  - `subject_tags(subject_id, tag_id, position)`, `session_tags(session_id, tag_id, position)`,
    `task_tags(task_id, tag_id, position)`: khoá chính ghép `(owner_id, tag_id)`, cả hai FK
    `ON DELETE CASCADE`.
- [X] T025 [P] Tạo model một-dòng trong `backend/app/models/settings.py`:
  - `Settings`: các cột và mặc định đúng bảng `settings` trong data-model.md (15, 60, 08:00,
    `false`, `false`, 20:00, 08:00, `{'Giáo dục thể chất'}`).
  - `SyncState(revision bigint)`.
  - `AgentStatus(last_seen_at, permission, icloud_source, last_synced_revision, last_error)`.
  - Cả ba bảng có CHECK `id = 1`.
- [X] T026 Tạo `backend/app/models/__init__.py` import mọi model, và quan hệ ORM: `Semester.subjects`,
  `Subject.sessions`, `Subject.tags` (theo `position`), `ClassSession.tags`, `Task.tags`,
  `Task.list`, `Task.source_session`.
- [X] T027 Tạo migration đầu tiên `backend/migrations/versions/0001_initial.py` (khởi tạo bằng
  `flask db init` rồi viết tay):
  - `CREATE EXTENSION IF NOT EXISTS btree_gist`; tạo mọi bảng ở T018–T025.
  - Ràng buộc học kỳ không chồng lấn: `EXCLUDE USING gist (daterange(start_date, end_date, '[]')
    WITH &&)`.
  - Dữ liệu mặc định:
    - 4 ca: Ca 1 06:45–09:25, Ca 2 09:35–12:10, Ca 3 13:00–15:40, Ca 4 15:45–18:25.
    - 3 danh sách: "Học tập" (`is_default_study`), "Cá nhân", "Công việc", màu c01, c02, c03.
    - Nhãn hệ thống "E-Learning" (`system_key='e_learning'`, màu c05).
    - Một dòng `settings`, `sync_state(revision=0)`, `agent_status(permission='unknown')`.
- [X] T028 [P] Tạo `backend/app/services/revision.py`: `bump_revision(session)` chạy `UPDATE
  sync_state SET revision = revision + 1 WHERE id = 1` trong transaction hiện tại.
- [X] T029 [P] Tạo `backend/app/services/colors.py`:
  - `PALETTE = ["c01", …, "c12"]`.
  - `next_color(used: list[str])`: chọn màu ít dùng nhất, ưu tiên thứ tự.
  - `display_color(tag_colors: list[str], fallback: str)`: màu nhãn đầu tiên, nếu không có thì
    `fallback`.
  Test trong `backend/tests/unit/test_colors.py`.
- [X] T030 Tạo `backend/tests/conftest.py` và `backend/tests/factories.py`:
  - Fixture `app` dùng `TEST_DATABASE_URL`, chạy `flask db upgrade` một lần mỗi phiên test.
  - Fixture `db_session`: mỗi test chạy trong transaction rồi rollback, dùng SQLAlchemy 2
    `join_transaction_mode="create_savepoint"`.
  - Fixture `client`.
  - Hàm tạo dữ liệu nhanh: `make_semester`, `make_subject`, `make_task`, `make_tag`.
- [X] T031 Tạo `backend/app/schemas/settings.py` và `backend/app/api/settings.py`: `GET/PATCH
  /api/settings` cho mọi trường của `settings`.
  - Validate: phút nhắc ≥ 0; giờ dạng `HH:MM`; `auto_deadline_excluded_keywords` là danh sách chuỗi
    không rỗng, đã chuẩn hoá NFC.
  - Mọi PATCH gọi `bump_revision`.
  - Thêm `GET /api/health`.
  Test trong `backend/tests/integration/test_settings_api.py`.
- [X] T032 [P] Tạo `frontend/src/i18n/vi.ts`: object `vi` chứa mọi chuỗi giao diện theo nhóm
  (`nav`, `today`, `tasks`, `subjects`, `calendar`, `import`, `settings`, `errors`, `confirm`) và
  hàm `t(path, params?)`.
- [X] T033 [P] Tạo `frontend/src/lib/dates.ts`:
  - `formatDayLong(iso)` → "Thứ Hai, 16/11/2026".
  - `formatDate(iso)` → "16/11/2026"; `formatTime(iso)` → "07:30" (24h).
  - `WEEKDAYS_VN` = ["Thứ Hai", …, "Chủ Nhật"]; `toIsoDate(d)`.
  Test trong `frontend/tests/dates.test.ts`.
- [X] T034 [P] Tạo `frontend/src/lib/colors.ts`: ánh xạ `c01`…`c12` sang 12 mã hex dễ phân biệt, đủ
  tương phản với chữ trắng; hàm `colorHex(code)`.
- [X] T035 Tạo `frontend/src/api/client.ts`:
  - `apiFetch<T>(path, init)` gọi `/api…`.
  - Phân tích lỗi thành lớp `ApiError {status, code, message, fields, details}`.
  - Trả `{data, warnings}` khi phản hồi có `warnings`.
- [X] T036 Tạo `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/routes.tsx`:
  - `QueryClientProvider`.
  - Layout có thanh điều hướng tiếng Việt: Hôm nay, Lịch, Công việc, Môn học, Nhập ảnh, Cài đặt.
  - Route `/` là trang Hôm nay (FR-020); các trang khác tạm là placeholder.
- [X] T037 [P] Tạo component dùng chung:
  - `frontend/src/components/ConfirmDialog.tsx`: tiêu đề, nội dung, nút "Huỷ"/"Xoá" (FR-027).
  - `frontend/src/components/FormField.tsx`: hiển thị lỗi theo `fields` của `ApiError`.
  - `frontend/src/components/WarningToast.tsx`: hiển thị `warnings`.
  - `frontend/src/components/ColorPicker.tsx`: chọn 1 trong 12 màu.

- [X] T038 Tạo `scripts/test.sh` (và `Makefile` với đích `test` gọi script này) để **toàn bộ** lint
  và test chạy bằng một lệnh duy nhất (constitution Nguyên tắc II). Script dùng `set -euo pipefail`
  và chạy lần lượt:
  1. Backend: `docker compose run --rm backend ruff check .`, `ruff format --check .`, `pytest`.
  2. Frontend: `npm ci` nếu chưa có `node_modules`, rồi `npm run lint` và `npm test`.
  3. Agent: `ruff check .` và `python -m pytest` trong `mac-agent/` (dùng venv `mac-agent/.venv`,
     tự tạo nếu chưa có).
  4. `scripts/test-persistence.sh` nếu file đã tồn tại.
  - Tuỳ chọn `--ocr` chạy thêm `pytest -m ocr`.
  - In tóm tắt pass/fail từng bước; trả mã thoát khác 0 nếu bất kỳ bước nào lỗi.

**Checkpoint**: `docker compose up -d --build` chạy được; `GET /api/health` trả 200;
`./scripts/test.sh` pass; trang web hiện khung điều hướng tiếng Việt.

---

## Phase 3: User Story 1 - Quản lý task theo danh sách (Priority: P1) 🎯 MVP

**Goal**: Tạo, sửa, xoá, hoàn thành task; quản lý danh sách; dữ liệu còn sau khi khởi động lại.

**Independent Test**: Tạo vài task ở các danh sách khác nhau, sửa, hoàn thành, xoá; chạy `docker
compose down && docker compose up -d`; dữ liệu còn nguyên (quickstart V1, V2).

### Tests for User Story 1 ⚠️

- [X] T039 [P] [US1] Test thuần trong `backend/tests/unit/test_task_rules.py`:
  - `due_at` = `due_date + (due_time ?? 23:59)`.
  - `is_overdue` chỉ đúng khi chưa hoàn thành và `due_at < now`.
  - Khoá sắp xếp: theo `due_at`, task không hạn ở cuối, rồi `priority` 1 → 3.
- [X] T040 [P] [US1] Test API trong `backend/tests/integration/test_tasks_api.py`:
  - Tạo task đầy đủ trường.
  - Tiêu đề rỗng hoặc chỉ khoảng trắng → `400` với `fields.title`.
  - Tiêu đề 301 ký tự → `400`.
  - `due_time` mà không có `due_date` → `400`; `priority` = 4 → `400`.
  - PATCH; `/complete`, `/uncomplete`; DELETE → `404` khi GET lại.
  - `include_completed=false` ẩn task đã xong.
  - Thứ tự sắp xếp đúng FR-005.
  - Tiêu đề tiếng Việt có dấu được trả về nguyên vẹn.
- [X] T041 [P] [US1] Test API trong `backend/tests/integration/test_lists_api.py`:
  - Có sẵn 3 danh sách mặc định.
  - Tạo danh sách trùng tên khác hoa thường → `400`.
  - Xoá danh sách còn task mà không có tham số → `409` với `details.task_count`.
  - `?move_to=` chuyển task; `?delete_tasks=true` xoá task.
  - Không xoá được danh sách "Học tập" khi thiếu `move_to`.
- [X] T042 [US1] Tạo `scripts/test-persistence.sh`: test tự động cho việc lưu dữ liệu và đọc lại sau
  khi khởi động lại (constitution Nguyên tắc V, FR-024, SC-008). Dùng database chính qua
  `http://127.0.0.1:8080/api`, dữ liệu có tiền tố `__persist_test__` và được dọn ở cuối.
  1. Tạo một danh sách và một task tiêu đề có dấu tiếng Việt qua API; ghi lại JSON trả về.
  2. `docker compose down` (**không** có `-v`) → `docker compose up -d` → chờ `/api/health` trả 200
     (tối đa 60 giây).
  3. `GET` lại và so sánh từng trường với JSON đã ghi; khác nhau thì báo lỗi.
  4. Tạo thêm một task, ngay khi nhận phản hồi thì chạy `docker compose kill backend db` (tắt đột
     ngột), rồi `up -d` và kiểm tra task đó vẫn còn.
  5. Xoá dữ liệu test.
  - Script được `scripts/test.sh` gọi tự động.

### Implementation for User Story 1

- [X] T043 [US1] Tạo `backend/app/schemas/tasks.py`:
  - `TaskIn`:
    - `title` bắt buộc, "1–300 ký tự sau khi bỏ khoảng trắng hai đầu"; `notes` tuỳ chọn.
    - `due_date`, `due_time` ("chỉ có khi có `due_date`").
    - `priority` ∈ {1, 2, 3}, mặc định 2; `list_id` bắt buộc.
    - `tag_ids: list[int] = []`; `reminder_minutes` ∈ {`None`, -1, ≥ 0}.
  - `TaskPatch`: mọi trường tuỳ chọn.
  - `TaskOut`: các trường trong contract, thêm `due_at`, `is_overdue`, `is_auto`,
    `source_session_id`, `user_modified`, `tags`, `display_color`, `reminder_at` (`reminder_at`
    tạm để `None`, US7 sẽ điền).
  - `ListIn`/`ListOut`.
- [X] T044 [US1] Tạo `backend/app/services/tasks.py`:
  - Hàm thuần `due_at(task)`, `is_overdue(task, now)`, `sort_key(task)`.
  - `create_task`, `update_task`: nếu `task.is_auto` và sửa bất kỳ trường nào khác `completed_at`
    thì đặt `user_modified = True`.
  - `complete_task`, `uncomplete_task`.
  - `delete_task`: nếu `is_auto` và có `source_session_id` thì đặt `auto_task_suppressed = True`
    cho buổi học trước khi xoá.
  - `list_tasks(list_id, include_completed, tag_ids)`.
  - Mọi thao tác ghi gọi `bump_revision`.
- [X] T045 [US1] Tạo `backend/app/services/task_lists.py`: tạo (gán `next_color`), đổi tên hoặc màu
  (kiểm tra trùng theo `ci_key`), xoá với `move_to` / `delete_tasks` / `409`, theo quy tắc trong
  data-model.md.
- [X] T046 [US1] Tạo blueprint `backend/app/api/tasks.py` (`/api/tasks…`) và
  `backend/app/api/lists.py` (`/api/lists…`) đúng contracts/rest-api.md; đăng ký trong
  `create_app`.
- [X] T047 [P] [US1] Tạo hook TanStack Query trong `frontend/src/api/tasks.ts` (`useTasks`,
  `useCreateTask`, `useUpdateTask`, `useCompleteTask`, `useDeleteTask`) và `frontend/src/api/lists.ts`.
  Thay đổi xong thì làm mới các query `tasks`, `today`, `calendar`.
- [X] T048 [US1] Tạo `frontend/src/components/TaskForm.tsx`:
  - Tiêu đề bắt buộc, báo lỗi ngay tại ô bằng tiếng Việt; ghi chú.
  - Ngày hạn chót, giờ (tuỳ chọn, chỉ bật khi đã có ngày).
  - Ưu tiên Cao / Trung bình / Thấp; chọn danh sách.
  - Hiển thị lỗi theo `ApiError.fields`.
- [X] T049 [US1] Tạo `frontend/src/pages/TasksPage.tsx`:
  - Cột trái là các danh sách kèm số task chưa xong; tạo, đổi tên, đổi màu, xoá danh sách (hộp
    thoại chọn "Chuyển sang danh sách…" hoặc "Xoá luôn các task" khi gặp `409`).
  - Cột phải là task đã sắp xếp: checkbox hoàn thành; task xong thì gạch ngang và làm mờ (FR-006);
    công tắc "Hiện task đã hoàn thành".
  - Nút sửa mở `TaskForm`; nút xoá có `ConfirmDialog`.

**Checkpoint**: US1 chạy độc lập; quickstart V1 và V2 pass.

---

## Phase 4: User Story 2 - Học kỳ, môn học, buổi học lặp hàng tuần (Priority: P1)

**Goal**: Quản lý học kỳ; thêm một hoặc nhiều môn có lặp hàng tuần; buổi học được sinh đúng.

**Independent Test**: Tạo học kỳ 07/09/2026–20/12/2026; nhập 3 môn trong một lần; mỗi môn đúng 15
buổi, đúng thứ, đúng giờ (quickstart V3; SC-003).

### Tests for User Story 2 ⚠️

- [X] T050 [P] [US2] Test thuần trong `backend/tests/unit/test_recurrence.py`:
  - `generate_dates([1], 2026-09-07, 2026-12-20)` → 15 ngày, đầu là 2026-09-07, cuối là
    2026-12-14.
  - Nhiều thứ `[1, 4]`; ngày bắt đầu không rơi vào thứ đã chọn.
  - Khoảng ngày không chứa thứ nào → rỗng.
  - `start_date == end_date` (học một lần).
  - `plan_regeneration`:
    - Giữ buổi `is_cancelled` / `time_overridden` / `room_overridden`.
    - Cập nhật giờ và phòng cho buổi không có ngoại lệ; xoá buổi không ngoại lệ nằm ngoài khoảng.
    - Trả `exception_conflicts` cho buổi có ngoại lệ nằm ngoài khoảng.
- [X] T051 [P] [US2] Test API trong `backend/tests/integration/test_semesters_api.py`:
  - Tạo học kỳ; chồng lấn → `400` với `fields.start_date` nêu tên học kỳ bị chồng.
  - `is_current`: học kỳ chứa hôm nay, nếu không có thì học kỳ sắp tới gần nhất.
  - PATCH làm môn ra ngoài khoảng → `409` với `details.subjects`; có `clamp_subjects=true` thì thu
    hẹp ngày môn và sinh lại buổi.
  - DELETE thiếu `confirm` → `409` với `details.subject_count`; có `confirm=true` thì xoá dây
    chuyền.
- [X] T052 [P] [US2] Test API trong `backend/tests/integration/test_subjects_api.py`:
  - POST với giờ tuỳ chỉnh → `session_count` đúng.
  - `end_time <= start_time` → `400` với `fields.end_time`.
  - `weekdays` rỗng hoặc trùng → `400`; ngày ngoài học kỳ → `400`; gửi cả `shift` lẫn giờ tuỳ chỉnh
    → `400`.
  - POST `/subjects/bulk` có dòng 3 lỗi → `400` với `fields["rows[2].end_time"]` và không môn nào
    được lưu.
  - Trùng giờ với buổi đã có → thành công kèm `warnings[0].code == "time_conflict"`.
  - Khoảng ngày không sinh buổi nào → `warnings[0].code == "no_sessions"`.
  - PATCH môn giữ buổi ngoại lệ (FR-013); DELETE xoá dây chuyền buổi học.
- [X] T053 [US2] Mở rộng `scripts/test-persistence.sh` (FR-024): trước bước khởi động lại, tạo thêm
  một học kỳ, một môn lặp hàng tuần, một buổi đã huỷ và một buổi đã đổi phòng. Sau khi `down`/`up`
  và sau khi `kill`, kiểm tra số buổi học, trạng thái huỷ và phòng đã sửa còn nguyên.

### Implementation for User Story 2

- [X] T054 [US2] Tạo `backend/app/services/recurrence.py`, chỉ chứa hàm thuần:
  - `generate_dates(weekdays, start, end) -> list[date]`.
  - `plan_regeneration(existing, desired_dates, start_time, end_time, room) -> Plan(to_create,
    to_update, to_delete, exception_conflicts)` theo research R8.
- [X] T055 [US2] Tạo `backend/app/services/semesters.py`:
  - `current_semester(today)`; `create`/`update` (bắt lỗi exclusion → `ApiError 400`).
  - Kiểm tra môn ra ngoài khoảng → `409`, hoặc thu hẹp khi `clamp_subjects`.
  - `delete` với `confirm`.
  - `bump_revision`.
- [X] T056 [US2] Tạo `backend/app/schemas/subjects.py`:
  - `SubjectInput`:
    - `name` "1–200 ký tự"; `semester_id`.
    - `weekdays` ("≥ 1 phần tử, không trùng", giá trị 1..7).
    - **Đúng một trong hai**: `shift {start_shift_id, end_shift_id}` hoặc cặp
      `start_time`/`end_time`.
    - `start_date`, `end_date`; `class_code`, `lecturer`, `room`, `tag_ids`, `reminder_minutes`.
  - `BulkSubjectsIn {semester_id, start_date, end_date, rows: list[SubjectInput không ngày]}`.
  - `SubjectOut`, `SessionOut` đúng contract (thêm `display_color`, `shift_label`, `auto_task_id`).
- [X] T057 [US2] Tạo `backend/app/services/subjects.py`:
  - `resolve_times(input)`: nếu có `shift` thì lấy giờ bắt đầu của ca đầu và giờ kết thúc của ca
    cuối; kiểm tra ca cuối có `position` ≥ ca đầu.
  - `create_subject`, `create_bulk` (một transaction; lỗi dòng nào thì báo theo
    `rows[i].field`).
  - `update_subject` dùng `plan_regeneration`; `delete_subject`.
  - `find_time_conflicts(date, start_at, end_at, exclude_subject_id)` sinh cảnh báo
    `time_conflict` (FR-015); cảnh báo `no_sessions`.
  - Mọi thao tác ghi gọi `bump_revision`.
- [X] T058 [US2] Tạo blueprint `backend/app/api/semesters.py` và `backend/app/api/subjects.py` đúng
  contract (gồm `/subjects/bulk`); đăng ký trong `create_app`.
- [X] T059 [P] [US2] Tạo hook trong `frontend/src/api/semesters.ts` và `frontend/src/api/subjects.ts`.
- [X] T060 [US2] Tạo `frontend/src/pages/SemestersPage.tsx` (đặt trong Cài đặt):
  - Danh sách học kỳ có huy hiệu "Hiện tại"; tạo, sửa, xoá.
  - Khi xoá gặp `409`: `ConfirmDialog` nêu "Sẽ xoá N môn học".
  - Khi sửa gặp `409`: hộp thoại liệt kê môn bị ảnh hưởng, nút "Thu hẹp ngày các môn" hoặc "Huỷ".
- [X] T061 [US2] Tạo `frontend/src/components/SubjectForm.tsx`:
  - Tên, mã lớp, giảng viên, phòng.
  - Chọn học kỳ (mặc định học kỳ hiện tại; chưa có học kỳ thì hiện form tạo học kỳ ngay tại chỗ).
  - Chọn nhiều thứ (Thứ Hai … Chủ Nhật); giờ bắt đầu/kết thúc dạng 24h.
  - Ngày bắt đầu/kết thúc mặc định theo học kỳ.
  - `ColorPicker`.
  - Hiện `warnings` bằng `WarningToast`.
- [X] T062 [US2] Tạo `frontend/src/components/BulkSubjectForm.tsx` và
  `frontend/src/pages/SubjectsPage.tsx`:
  - Trang Môn học liệt kê môn theo học kỳ, có nút "Thêm môn" và "Nhập nhiều môn".
  - Form nhiều dòng: thêm/bớt dòng; khoảng ngày dùng chung, mặc định cả học kỳ.
  - Lỗi `rows[i].field` hiện đúng ô và giữ nguyên dữ liệu các dòng khác.

**Checkpoint**: US2 chạy độc lập; quickstart V3 pass (phần chọn ca làm ở US8).

---

## Phase 5: User Story 3 - Trang "Hôm nay" (Priority: P1)

**Goal**: Màn hình mặc định liệt kê buổi học hôm nay, task hạn hôm nay và nhóm "Quá hạn".

**Independent Test**: Tạo buổi học và task cho hôm qua, hôm nay, ngày mai; trang Hôm nay chỉ hiện
đúng mục của hôm nay và nhóm Quá hạn.

### Tests for User Story 3 ⚠️

- [X] T063 [P] [US3] Test API trong `backend/tests/integration/test_today_api.py`:
  - Buổi học sắp theo giờ, có đủ giờ, phòng, `is_cancelled`.
  - `tasks_due_today` không gồm task của ngày khác.
  - `overdue_tasks` chỉ gồm task chưa hoàn thành có `due_at < now`.
  - Ngày trống trả về các mảng rỗng.

### Implementation for User Story 3

- [X] T064 [US3] Tạo `backend/app/services/today.py` và blueprint `backend/app/api/today.py`: `GET
  /api/today` trả `{date, sessions, tasks_due_today, overdue_tasks, notices}`. `notices` tạm rỗng,
  US7 sẽ thêm.
- [X] T065 [US3] Tạo `frontend/src/api/today.ts` và `frontend/src/pages/TodayPage.tsx`:
  - Tiêu đề "Hôm nay, Thứ …".
  - Khối Buổi học: giờ, môn, phòng; buổi huỷ có nhãn "Đã huỷ" và gạch ngang.
  - Khối Task hôm nay và khối "Quá hạn": tiêu đề, ưu tiên, danh sách; checkbox hoàn thành cập nhật
    ngay mọi query.
  - Ngày trống hiện "Hôm nay bạn không có lịch học hay việc cần làm 🎉".
  - Vùng `notices` ở đầu trang.

**Checkpoint**: MVP (US1 + US2 + US3) dùng được hằng ngày.

---

## Phase 6: User Story 4 - Sửa hoặc huỷ một buổi học riêng lẻ (Priority: P2)

**Goal**: Huỷ, khôi phục, đổi giờ hoặc phòng một buổi mà không ảnh hưởng buổi khác.

**Independent Test**: Huỷ buổi 16/11, đổi phòng buổi 23/11, rồi sửa phòng chung của môn; chỉ hai
buổi đó giữ ngoại lệ (quickstart V4).

### Tests for User Story 4 ⚠️

- [ ] T066 [P] [US4] Test API trong `backend/tests/integration/test_sessions_api.py`:
  - `/cancel`, `/restore`: khôi phục giữ nguyên giờ và phòng đã sửa riêng.
  - PATCH `start_time`/`end_time` đặt `time_overridden`; PATCH `room` đặt `room_overridden`.
  - `end_time <= start_time` → `400`.
  - Các buổi khác của môn không đổi.
  - PATCH phòng của môn sau đó vẫn giữ buổi ngoại lệ.

### Implementation for User Story 4

- [ ] T067 [US4] Tạo `backend/app/services/sessions.py` (`cancel`, `restore`, `update_session`, gọi
  `bump_revision`) và blueprint `backend/app/api/sessions.py`: `PATCH /api/sessions/{id}`, `POST
  /api/sessions/{id}/cancel|restore`.
- [ ] T068 [US4] Tạo `frontend/src/api/sessions.ts` và `frontend/src/components/SessionDetail.tsx`:
  - Hộp chi tiết buổi học: môn, ngày dạng "Thứ Hai, 16/11/2026", giờ, phòng.
  - Nút "Huỷ buổi này" / "Khôi phục"; form đổi giờ và phòng chỉ cho buổi này.
  - Mở được từ `TodayPage`.
- [ ] T069 [US4] Trong `frontend/src/components/SubjectForm.tsx` và
  `frontend/src/pages/SubjectsPage.tsx`:
  - Khi lưu môn mà API báo buổi ngoại lệ nằm ngoài khoảng mới (`409`), hiện hộp thoại xác nhận.
  - Thêm nút "Xoá môn học" có `ConfirmDialog` nêu số buổi học sẽ bị xoá (FR-014).

**Checkpoint**: US4 pass; quickstart V4 pass.

---

## Phase 7: User Story 5 - Xem lịch theo ngày, tuần, tháng (Priority: P2)

**Goal**: Lịch ngày, tuần, tháng hiển thị buổi học và task theo màu.

**Independent Test**: Với 3 môn và 5 task, chuyển qua lại 3 chế độ xem, đi tới và lui; mục hiện đúng
ngày và đúng màu (SC-006).

### Tests for User Story 5 ⚠️

- [ ] T070 [P] [US5] Test API trong `backend/tests/integration/test_calendar_api.py`:
  - `GET /api/calendar?from&to` chỉ trả mục trong khoảng (tính cả hai đầu).
  - Buổi huỷ vẫn có, kèm `is_cancelled`.
  - Task không có hạn chót không xuất hiện.
  - `display_color` = màu môn hoặc màu danh sách khi không có nhãn.
- [ ] T071 [P] [US5] Test thuần trong `frontend/tests/calendarEvents.test.ts` cho `toCalendarEvents`:
  - Buổi học thành sự kiện có giờ.
  - Task có giờ thành sự kiện có giờ; task chỉ có ngày thành sự kiện cả ngày.
  - Buổi huỷ có class `is-cancelled`.
  - Màu lấy từ `colorHex(display_color)`.

### Implementation for User Story 5

- [ ] T072 [US5] Tạo `backend/app/services/calendar.py` và blueprint `backend/app/api/calendar.py`:
  `GET /api/calendar?from=&to=` trả `{sessions, tasks}`. Tham số `tags` để trống, US9 sẽ thêm.
- [ ] T073 [US5] Tạo `frontend/src/lib/calendarEvents.ts`: hàm thuần `toCalendarEvents(sessions,
  tasks)` ánh xạ sang EventInput của FullCalendar.
- [ ] T074 [US5] Tạo `frontend/src/api/calendar.ts` và `frontend/src/pages/CalendarPage.tsx`:
  - FullCalendar với `dayGridMonth`, `timeGridWeek`, `timeGridDay`.
  - `locale: 'vi'`, `firstDay: 1`, định dạng giờ 24h (`slotLabelFormat`, `eventTimeFormat` với
    `hour12: false`), `dayMaxEvents: true` (tự hiện "+n").
  - Nút "Trước", "Sau", "Hôm nay"; nút chế độ "Ngày", "Tuần", "Tháng".
  - Tải dữ liệu theo `datesSet`.
  - Bấm buổi học mở `SessionDetail`; bấm task mở `TaskForm`.
  - CSS `.is-cancelled { text-decoration: line-through; opacity: .5 }`.
- [ ] T075 [US5] Đổi màu (FR-018): thêm `ColorPicker` vào form danh sách trong
  `frontend/src/pages/TasksPage.tsx` và kiểm tra `SubjectForm` đã có; màu được tự gán khi tạo (đã có
  `next_color` phía backend).

**Checkpoint**: US5 pass; quickstart V6 (phần không có nhãn) pass.

---

## Phase 8: User Story 8 - Ca học cố định (Priority: P2)

**Goal**: Bảng ca chỉnh được; chọn ca khi thêm môn; đổi hoặc xoá ca lan sang các môn.

**Independent Test**: Thêm môn chọn "Ca 2" → 09:35–12:10; đổi giờ Ca 2 → môn cập nhật, trừ buổi đã
sửa giờ riêng (quickstart V5).

### Tests for User Story 8 ⚠️

- [ ] T076 [P] [US8] Test thuần trong `backend/tests/unit/test_shifts.py`:
  - `resolve_range(ca1, ca2)` → 06:45–12:10.
  - `match_shift_range(start, end, shifts, tolerance_min=5)`:
    - Khớp 1 ca (lệch 4 phút vẫn khớp, lệch 6 phút thì không).
    - Khớp dãy ca liền nhau (Ca 1–2); không khớp → `None`.
- [ ] T077 [P] [US8] Test API trong `backend/tests/integration/test_shifts_api.py`:
  - Có sẵn 4 ca mặc định đúng giờ.
  - `end_time <= start_time` → `400`.
  - PATCH ca đang dùng mà thiếu `confirm` → `409` với `details.subject_count`; có `confirm=true`
    thì môn và buổi học cập nhật, trừ buổi `time_overridden`.
  - DELETE ca đang dùng (`confirm=true`): môn có `start_shift_id`/`end_shift_id` = `NULL`, giữ
    nguyên giờ.
  - Tạo môn bằng `shift: {1, 2}` → giờ 06:45–12:10.

### Implementation for User Story 8

- [ ] T078 [US8] Tạo `backend/app/services/shifts.py`:
  - Hàm thuần `resolve_range`, `match_shift_range`, `shift_label(start_shift, end_shift)` (ví dụ
    "Ca 1" hoặc "Ca 1–2").
  - `update_shift` / `delete_shift` lan thay đổi sang `subjects` rồi gọi
    `services.subjects.regenerate_sessions`.
  - Gọi `bump_revision`.
  - Dùng `resolve_range` trong `services/subjects.resolve_times` (thay code tạm ở T057).
- [ ] T079 [US8] Tạo blueprint `backend/app/api/shifts.py` (`GET/POST /api/shifts`, `PATCH/DELETE
  /api/shifts/{id}?confirm=true`); `SessionOut.shift_label` lấy từ `shift_label`.
- [ ] T080 [US8] Tạo `frontend/src/api/shifts.ts` và `frontend/src/components/ShiftPicker.tsx`:
  - Chọn "Ca n", dãy "Ca a–b" (ca cuối ≥ ca đầu), hoặc "Giờ tuỳ chỉnh" (hiện ô nhập giờ).
  - Hiển thị giờ tương ứng.
  - Thay ô giờ trong `SubjectForm.tsx` và `BulkSubjectForm.tsx` bằng `ShiftPicker`.
- [ ] T081 [US8] Tạo `frontend/src/pages/ShiftsPage.tsx` (trong Cài đặt): sửa giờ, thêm, xoá ca;
  gặp `409` thì hiện `ConfirmDialog` "N môn học sẽ cập nhật theo giờ mới" / "N môn học sẽ chuyển
  sang giờ tuỳ chỉnh".

**Checkpoint**: US8 pass; quickstart V3 (chọn ca) và V5 pass.

---

## Phase 9: User Story 9 - Nhãn có màu (Priority: P2)

**Goal**: Tạo nhãn, gắn nhiều nhãn cho task, môn và buổi; lịch hiện màu nhãn; lọc theo nhãn.

**Independent Test**: Nhãn "Gấp" đỏ gắn cho 2 task + 1 buổi → 3 mục màu đỏ; lọc "Gấp" chỉ còn 3 mục,
dưới 1 giây (quickstart V6; SC-016).

### Tests for User Story 9 ⚠️

- [ ] T082 [P] [US9] Test API trong `backend/tests/integration/test_tags_api.py`:
  - Tạo nhãn; trùng tên khác hoa thường → `400`.
  - Nhãn `e_learning`: đổi tên hoặc xoá → `400`, đổi màu → `200`.
  - `PUT /tasks/{id}/tags` giữ đúng thứ tự.
  - Nhãn hiệu lực của buổi = nhãn môn rồi đến nhãn riêng của buổi; `display_color` = màu nhãn đầu.
  - Xoá nhãn gỡ khỏi mọi mục và màu quay về màu môn hoặc danh sách.
  - `GET /api/calendar?tags=1,2` và `GET /api/tasks?tags=1` chỉ trả mục có ít nhất một nhãn đã chọn.

### Implementation for User Story 9

- [ ] T083 [US9] Tạo `backend/app/services/tags.py`:
  - CRUD (chặn sửa tên hoặc xoá nhãn có `system_key`, kiểm tra trùng `ci_key`).
  - `set_tags(owner, tag_ids)` ghi `position` theo thứ tự.
  - `effective_tags(session)`.
  - Gọi `bump_revision`.
  Tạo blueprint `backend/app/api/tags.py` gồm `PUT /api/subjects/{id}/tags`,
  `/api/sessions/{id}/tags`, `/api/tasks/{id}/tags`.
- [ ] T084 [US9] Cập nhật `backend/app/services/calendar.py`, `services/tasks.list_tasks` và
  `services/today.py`:
  - Lọc theo `tag_ids` với logic OR.
  - Tính `tags` và `display_color` bằng `colors.display_color` cho buổi học và task.
  - Xử lý `tag_ids` trong `TaskIn` và `SubjectInput`.
- [ ] T085 [US9] Tạo `frontend/src/api/tags.ts`, `frontend/src/components/TagPicker.tsx` (chọn nhiều,
  giữ thứ tự chọn) và `frontend/src/pages/TagsPage.tsx`:
  - TagsPage: tạo, đổi tên, đổi màu, xoá nhãn (nhãn E-Learning chỉ đổi màu).
  - Gắn `TagPicker` vào `TaskForm`, `SubjectForm`, `SessionDetail`.
- [ ] T086 [US9] Tạo `frontend/src/components/TagFilter.tsx` và gắn vào `CalendarPage` và
  `TasksPage`:
  - Bộ lọc lưu trong tham số URL `?tags=1,2`, nên giữ nguyên khi đổi chế độ xem (FR-045).
  - Nút "Bỏ lọc".
  - Trong `frontend/src/lib/calendarEvents.ts` thêm `renderEventContent`: hiện chấm màu cho các
    nhãn thứ 2 trở đi.
  - Thêm test lọc vào `frontend/tests/calendarEvents.test.ts`.

**Checkpoint**: US9 pass; quickstart V6 pass.

---

## Phase 10: User Story 6 + 11 - Nhập ảnh lịch học và Lịch thi (Priority: P2)

**Goal**:
- US6: kéo thả ảnh chụp thời khoá biểu, nhận diện offline, xem trước, sửa, lưu không trùng.
- US11: quản lý buổi thi; nhập ảnh bảng "Lịch thi cá nhân" (tự nhận biết loại ảnh, bỏ cột thông tin
  sinh viên); hiển thị buổi thi trên lịch và trang Hôm nay với nhãn "Thi"; cảnh báo trùng giờ.

**Independent Test**:
- US6: nhập `week-grid-01.png` → bảng xem trước khớp `week-grid-01.expected.json`; nhập lại → 0 buổi
  mới (quickstart V7, V8; SC-011, SC-012).
- US11: thêm tay 1 buổi thi trùng giờ học → có cảnh báo; nhập `exam-01.png` → loại "Lịch thi", dòng
  đã qua bỏ chọn, không có họ tên/mã SV; nhập lại → 0 buổi thi mới (quickstart V18; SC-019 đến
  SC-021).

**Phụ thuộc**: T010 (spike S1) đã có kết luận. Nếu spike chọn Apple Vision, thay T094–T095 theo
research R2.

### Tests for User Story 6 ⚠️

- [ ] T087 [US6] Chuẩn bị ảnh mẫu trong `backend/tests/fixtures/timetables/`:
  - ≥ 3 ảnh thật từ người dùng, đã che thông tin cá nhân, mỗi ảnh có file `*.expected.json`. Định
    dạng JSON: `{month_year, rows: [{name, class_code, date, weekday, start_time, end_time, room,
    lecturer}]}`.
  - Script `backend/tests/fixtures/make_synthetic.py` dùng Pillow (font DejaVuSans hỗ trợ tiếng
    Việt) vẽ 2 ảnh lưới tuần tổng hợp:
    - `synthetic-grid-01.png`: giờ đúng theo ca, có lịch tháng thu nhỏ "Tháng 11 2026".
    - `synthetic-grid-02.png`: có một ô "E-Learning", một giờ lệch ca, thanh menu
      "Th 4 4 thg 11 14:05".
    Kèm file expected tương ứng.
- [ ] T088 [P] [US6] Test thuần trong `backend/tests/unit/test_ocr_fields.py`:
  - Giờ: "07:30 - 09:30", "7h30-9h30", "07g30–09g30".
  - "Ca 2", "Tiết 1-3".
  - Phòng: "A101", "P.B2-305", "Phòng: C1.204".
  - "GV: Nguyễn Văn A"; mã lớp "INT1234_01".
  - E-Learning: "E-Learning", "Elearning", "Online".
  - Tên môn là dòng còn lại dài nhất.
- [ ] T089 [P] [US6] Test thuần trong `backend/tests/unit/test_ocr_layout.py` với danh sách
  `TextBox` dựng tay:
  - Bỏ khối thuộc thanh menu, thanh địa chỉ và Dock.
  - Nhận dạng lưới tuần từ tiêu đề "Thứ 2…Chủ nhật/CN"; gán cột theo trục x; gom khối thành ô theo
    khoảng cách dọc < 1.2 × chiều cao dòng.
  - Nhận dạng bố cục danh sách theo tiêu đề cột.
- [ ] T090 [P] [US6] Test thuần trong `backend/tests/unit/test_ocr_month_year.py`:
  - Thứ tự ưu tiên nguồn: ngày trong lưới → tiêu đề tuần → lịch thu nhỏ → thanh menu.
  - Mâu thuẫn giữa nguồn → chọn nguồn ưu tiên cao hơn, `certain=False`.
  - Thanh menu "Th 4 4 thg 11 14:05" kết hợp năm hiện tại.
  - Không có nguồn nào → `value=None`, `certain=False`.
- [ ] T091 [P] [US6] Test thuần trong `backend/tests/unit/test_import_preview.py`:
  - Ngày lệch thứ → `weekday.certain=False` với lý do.
  - Khớp ca → gán `shift`; không khớp → ghi chú "không khớp ca nào".
  - Phát hiện trùng với database (cùng tên hoặc mã lớp + ngày + giờ bắt đầu) và giữa các dòng trong
    ảnh → `duplicate_of_session_id`, `selected=False`.
  - Gán `semester_id` theo ngày (không thuộc học kỳ nào → `None`).
  - `repeat` mặc định `weekly` đến hết học kỳ, `once` khi không có học kỳ.
  - `suggested_tags=['e_learning']`.
  - Độ tin cậy OCR < 0.6 → `certain=False`.
  - Tên gần giống môn đã có (rapidfuzz ≥ 90) → sửa theo tên đã có.
- [ ] T092 [P] [US6] Test API trong `backend/tests/integration/test_imports_api.py` (monkeypatch
  `app.ocr.reader.read_boxes` trả `TextBox` dựng sẵn):
  - `recognize` trả `ImportPreview` và **không** thay đổi số dòng của bất kỳ bảng nào.
  - Ảnh > 20 MB → `413`; file không phải ảnh → `415`.
  - `commit` tạo môn và buổi (`weekly` và `once`).
  - Dòng còn trường bắt buộc chưa chắc chắn → `400` với `fields["rows[i].name"]`, không lưu gì.
  - Dòng trùng bị bỏ qua (`skipped_duplicates`).
  - Commit lại cùng dữ liệu → 0 buổi mới (SC-012).
  - Ba dòng cùng `merge_group` với `merge_accepted=true` → 1 môn; với `false` → 3 môn.
- [ ] T093 [P] [US6] Test OCR thật trong `backend/tests/ocr/test_ocr_fixtures.py`
  (`@pytest.mark.ocr`):
  - Với mỗi ảnh mẫu, chạy toàn bộ pipeline và so với file expected.
  - In tỉ lệ dòng đúng hoàn toàn và assert ≥ 0.8 (SC-011).
  - Assert mọi trường sai đều có `certain=False` hoặc nằm trong dòng bị đánh dấu.
  - Đo và in thời gian nhận diện mỗi ảnh (từ `load_image` đến khi có `ImportPreview`); assert ≤ 60
    giây mỗi ảnh (plan, SC-010).

### Implementation for User Story 6

- [ ] T094 [P] [US6] Tạo `backend/app/ocr/preprocess.py`: `load_image(bytes) -> PIL.Image`.
  - Đăng ký `pillow_heif`; kiểm tra định dạng ∈ {PNG, JPEG, HEIC}, nếu không thì `ApiError 415`.
  - Chuyển sang RGB; thu nhỏ cạnh dài về ≤ 2560 px.
  - Chế độ `enhance` (×1.5, tăng tương phản) theo kết quả spike.
- [ ] T095 [P] [US6] Tạo `backend/app/ocr/reader.py`:
  - `@dataclass TextBox(text, x0, y0, x1, y1, conf)`.
  - Singleton `easyocr.Reader(['vi','en'], gpu=False, model_storage_directory=EASYOCR_MODEL_DIR,
    download_enabled=False)` khởi tạo lười, kèm `threading.Lock`.
  - `read_boxes(image) -> list[TextBox]`, chuẩn hoá NFC.
- [ ] T096 [US6] Tạo `backend/app/ocr/fields.py` theo research R3 bước 5: các regex và hàm
  `extract_fields(lines) -> dict[field, (value, conf)]`.
- [ ] T097 [US6] Tạo `backend/app/ocr/layout.py`: `filter_chrome(boxes, image_size)`,
  `detect_layout(boxes) -> "week_grid" | "list" | None`, `columns_for_weekdays`, `group_cells`,
  `rows_from_list_layout`, theo research R3 bước 2–4.
- [ ] T098 [US6] Tạo `backend/app/ocr/month_year.py`: `infer_month_year(boxes, layout) ->
  {value, source, certain}`, theo research R3 bước 6.
- [ ] T099 [US6] Tạo `backend/app/ocr/preview.py`: `build_preview(boxes, db_context) ->
  ImportPreview`:
  - Ghép layout → fields → month/year → đối chiếu ca (`shifts.match_shift_range`) → kiểm tra thứ và
    ngày → sửa tên bằng rapidfuzz → gán học kỳ → phát hiện trùng (`services/duplicates.py`, tạo mới
    với `find_duplicate(name, class_code, date, start_time)`) → gợi ý gộp các dòng cùng tên, thứ,
    giờ bằng cách gán chung `merge_group` (`merge_accepted` mặc định `false`).
  - Schema `ImportPreview` và `ImportRow` trong `backend/app/schemas/imports.py`, đúng data-model.md.
- [ ] T100 [US6] Tạo `backend/app/services/imports.py`: `commit_import(rows)`:
  - Một transaction.
  - Từ chối trường bắt buộc `certain=False`.
  - Kiểm tra trùng lại phía server, kể cả giữa các dòng.
  - Mỗi dòng tạo môn qua `services.subjects.create_subject`: `weekly` → `weekdays=[weekday(date)]`,
    từ `date` đến `until`; `once` → `start_date=end_date=date`.
  - Các dòng có cùng `merge_group` và `merge_accepted=true` tạo **một** môn lặp hàng tuần: ngày bắt
    đầu là ngày sớm nhất trong nhóm, đến `until` của nhóm.
  - Gắn nhãn đã chọn.
  - Trả `{created_subjects, created_sessions, skipped_duplicates, warnings}`.
- [ ] T101 [US6] Tạo blueprint `backend/app/api/imports.py`:
  - `POST /api/imports/recognize`: multipart `image`; kiểm tra `request.content_length` và kích
    thước thực ≤ `MAX_IMAGE_BYTES` trước khi đọc (`413`).
  - Chỉ xử lý trong bộ nhớ: không `save()`, không ghi file tạm, không lưu database.
  - `POST /api/imports/commit`.
- [ ] T102 [US6] Tạo `frontend/src/api/imports.ts` và `frontend/src/pages/ImportPage.tsx`:
  - Vùng kéo thả và nút "Chọn ảnh" (`accept="image/png,image/jpeg,image/heic,.heic"`).
  - Kiểm tra ≤ 20 MB phía client với thông báo tiếng Việt.
  - Hiện ảnh thu nhỏ và trạng thái "Đang nhận diện… (có thể mất tới 1 phút)".
  - Hiện lỗi `413`/`415`/`500` bằng tiếng Việt.
- [ ] T103 [US6] Tạo `frontend/src/components/ImportPreviewTable.tsx`:
  - Mỗi dòng một buổi; mọi ô sửa được.
  - Ô `certain=false` tô nền vàng, lý do hiện khi rê chuột.
  - Huy hiệu "Đã có trong lịch" (mặc định bỏ chọn); "Ca n" hoặc "Giờ tuỳ chỉnh – không khớp ca nào".
  - Chọn lặp "Chỉ một lần" / "Lặp hàng tuần đến [ngày]".
  - Chọn học kỳ (dòng chưa có học kỳ tô đỏ, nút "Tạo học kỳ mới" ngay tại chỗ).
  - Gợi ý nhãn E-Learning; dòng ghi nguồn tháng/năm.
  - Các dòng có cùng `merge_group` được nhóm lại kèm thanh "Các buổi này giống nhau (cùng môn,
    thứ, giờ). Gộp thành một môn lặp hàng tuần?" với nút "Gộp" / "Giữ riêng". Chọn "Gộp" đặt
    `merge_accepted=true` cho cả nhóm và hiện một lựa chọn lặp chung.
  - Nút "Lưu" tắt khi còn trường bắt buộc chưa chắc chắn ở dòng được chọn; lỗi `rows[i]` hiện đúng
    dòng.
  - Đóng bảng thì bỏ toàn bộ kết quả.

### Tests for User Story 11 ⚠️

- [ ] T104 [P] [US11] Test thuần trong `backend/tests/unit/test_exams.py`:
  - `duration_from_format("Trắc nghiệm trên máy 60p")` = 60; `"Tự luận 90 phút"` = 90; `"Bài tập
    lớn"` = `None`.
  - `resolve_offsets`: `None` → `settings.exam_reminder_offsets` (`[1440, 60]`); `[]` → không nhắc;
    `[120]` → `[120]`.
  - `find_conflicts`: trùng buổi học chưa huỷ và buổi thi khác → có; buổi học đã huỷ → không; chạm
    mép (kết thúc 09:25, bắt đầu 09:25) → không.
  - `is_past` theo `end_at < now`.
  - `duplicate_key`: cùng mã học phần + ngày + giờ bắt đầu + lần thi → trùng; khác lần thi → không
    trùng; không có mã thì so theo tên (không phân biệt hoa thường, NFC).
- [ ] T105 [P] [US11] Test API trong `backend/tests/integration/test_exams_api.py`:
  - Tạo, sửa, xoá buổi thi (`204`); `revision` tăng ở mỗi thao tác.
  - Tên học phần rỗng → `400` `fields.course_name`; giờ kết thúc không sau giờ bắt đầu → `400`
    `fields.end_time`; `attempt = 0` → `400`; phòng trống được chấp nhận.
  - Nhãn "Thi" (`system_key='exam'`) tự gắn ở vị trí đầu; `PUT /exams/{id}/tags` với nhãn khác vẫn
    giữ "Thi" đầu tiên; xoá nhãn "Thi" → `400`.
  - Trùng giờ với buổi học chưa huỷ hoặc buổi thi khác → `201` kèm `warnings[0].code ==
    "time_conflict"` và `conflicts` trong phản hồi; với buổi học đã huỷ → không cảnh báo.
  - `GET /api/today` có `exams` của hôm nay (sắp theo giờ, kèm `conflicts`); `GET /api/calendar`
    có `exams` trong khoảng ngày; `?tags=<id nhãn Thi>` trả buổi thi.
- [ ] T106 [P] [US11] Test thuần trong `backend/tests/unit/test_ocr_exam_table.py` với `TextBox`
  dựng tay:
  - `detect_layout` → `"exam_table"` khi có ≥ 3 tiêu đề lịch thi và cột ngày `dd/mm/yyyy`;
    `"week_grid"` với tiêu đề "Thứ 2…CN"; `"unknown"` khi không đủ dấu hiệu.
  - Tiêu đề mất dấu ("Ngay thi", "Phong thi") vẫn được nhận (so khớp mờ ≥ 85).
  - Ô nhiều dòng (tên học phần xuống dòng) được ghép đúng.
  - Cột "Họ tên", "Mã SV" bị loại: giá trị bịa "Nguyễn Văn Test", "21010999" **không** xuất hiện ở
    bất kỳ đâu trong kết quả (`json.dumps` kết quả không chứa chuỗi đó).
  - Giờ "07:30 - 08:30"; giờ "07:30" + "Trắc nghiệm trên máy 60p" → kết thúc 08:30,
    `end_time_source="format_duration"`; không có thời lượng → `end_time.certain=False`.
- [ ] T107 [P] [US11] Test thuần trong `backend/tests/unit/test_exam_preview.py`:
  - Buổi thi đã kết thúc → `is_past=True`, `selected=False`.
  - Trùng với buổi thi đã có trong database và giữa các dòng trong ảnh → `duplicate_of_exam_id`,
    `selected=False`.
  - Lần thi 2 của cùng học phần không bị coi là trùng với lần 1.
- [ ] T108 [P] [US11] Test API trong `backend/tests/integration/test_imports_exams_api.py`
  (monkeypatch `app.ocr.reader.read_boxes` trả khối chữ của một bảng lịch thi có họ tên và mã SV
  bịa):
  - `recognize` trả `kind="exam_table"`, `exam_rows` đúng; nội dung phản hồi **không** chứa họ tên
    và mã SV; số dòng của mọi bảng không đổi.
  - `recognize?kind=exam_table` ép loại khi ảnh bị nhận là `"unknown"`.
  - `commit` với `kind="exam_table"` tạo buổi thi; dòng trùng bị bỏ qua (`skipped_duplicates`);
    commit lại → 0 buổi thi mới; dòng thiếu trường bắt buộc chắc chắn → `400`
    `fields["exam_rows[i].course_name"]`.
- [ ] T109 [US11] Ảnh lịch thi giả lập: mở rộng `samples/synthetic/make_samples.py` tạo
  `exam-01.png` (2880×1800) và `exam-02.png` (1440×900) mô phỏng bảng "Lịch thi cá nhân":
  - Cột STT, Mã SV, Họ tên (giá trị bịa), Mã học phần, Tên học phần, Lần thi, Ngày thi (dd/mm/yyyy),
    Giờ thi, Hình thức thi, Phòng thi, SBD.
  - 6 dòng: 2 dòng ngày đã qua, 1 dòng phòng trống, 1 dòng "Trắc nghiệm trên máy 60p" chỉ ghi giờ
    bắt đầu, 1 dòng lần thi 2.
  - File `*.expected.json` (không chứa thông tin sinh viên trong `rows`; liệt kê riêng các giá trị
    sinh viên bịa trong `student_values_must_not_appear`). Ghi rõ đây là ảnh giả lập trong README
    của thư mục.
  - Chép sang `backend/tests/fixtures/timetables/`. Mở rộng `backend/spikes/ocr_spike.py --parsed`
    và `backend/tests/ocr/test_ocr_fixtures.py` cho loại ảnh này: assert nhận đúng loại 100%, ≥ 80%
    dòng đúng mọi trường (SC-019), 0 giá trị sinh viên trong kết quả (SC-020).

### Implementation for User Story 11

- [ ] T110 [US11] Tạo migration `backend/migrations/versions/0002_exams.py` và model
  `backend/app/models/exam.py` (`Exam`, `ExamTag`) đúng data-model.md, đăng ký trong
  `app/models/__init__.py`:
  - Cột: `course_code` (tuỳ chọn), `course_name` "1–200 ký tự", `attempt` "≥ 1, mặc định 1",
    `date`, `start_at`, `end_at` (CHECK `end_at > start_at`), `exam_format`, `room` (có thể trống),
    `candidate_number` (số báo danh), `reminder_offsets`;
    `reminder_offsets integer[]` với CHECK `reminder_offsets IS NULL OR 0 <= ALL(reminder_offsets)`;
    index `(date)`, `(start_at)`.
  - `exam_tags(exam_id, tag_id, position)` khoá chính ghép, FK `ON DELETE CASCADE`.
  - Thêm cột `settings.exam_reminder_offsets integer[]` mặc định `{1440, 60}`.
  - Thêm nhãn hệ thống "Thi" (`system_key='exam'`, màu `c07`).
  - Không có cột nào cho họ tên hay mã số sinh viên (FR-061). `test_migrations_match_models` phải
    vẫn pass.
- [ ] T111 [US11] Tạo `backend/app/schemas/exams.py`, `backend/app/services/exams.py`,
  `backend/app/api/exams.py` theo contracts/rest-api.md "Lịch thi":
  - Hàm thuần `duration_from_format`, `resolve_offsets`, `find_conflicts`, `duplicate_key`,
    `is_past`.
  - CRUD; nhãn "Thi" luôn ở vị trí đầu (`replace_tag_links` + chèn nhãn hệ thống); cảnh báo
    `time_conflict` (FR-058); mọi thao tác ghi gọi `bump_revision`.
  - Thêm `exam_reminder_offsets` (danh sách số ≥ 0, tối đa 5 mốc) vào `schemas/settings.py`.
  - Đăng ký blueprint trong `create_app`.
- [ ] T112 [US11] Hiển thị buổi thi ở backend: thêm `exams` (kèm `conflicts`, `display_color`) vào
  `services/today.py`/`api/today.py` và `services/calendar.py`/`api/calendar.py` (lọc theo khoảng
  ngày và theo nhãn) (FR-057).
- [ ] T113 [US11] Nhập ảnh lịch thi (research R14):
  - `backend/app/ocr/layout.py`: `detect_layout` trả thêm `"exam_table"`.
  - `backend/app/ocr/exam_table.py`: phân tích bảng, ánh xạ tiêu đề đồng nghĩa, **loại cột thông
    tin sinh viên ngay sau khi xác định cột** và không ghi log nội dung của chúng; tính giờ kết thúc
    từ thời lượng.
  - `backend/app/ocr/preview.py`: trả `ImportPreview` có `kind` và `exam_rows` (`is_past`,
    `duplicate_of_exam_id`, `selected`).
  - `backend/app/services/imports.py` và `backend/app/api/imports.py`: `recognize` nhận `?kind=` để
    ép loại; `commit` xử lý `kind="exam_table"` trong một transaction (FR-059 đến FR-062).
- [ ] T114 [P] [US11] Tạo `frontend/src/api/exams.ts` (hook CRUD, làm mới `today`, `calendar`,
  `exams`), bổ sung kiểu `Exam` vào `frontend/src/api/types.ts`, và
  `frontend/src/components/ExamForm.tsx`: tên học phần, mã học phần, lần thi, ngày, giờ bắt đầu/kết
  thúc (24h), hình thức thi, phòng (để trống được), số báo danh; hiện `warnings` bằng `WarningToast`.
- [ ] T115 [US11] Tạo `frontend/src/pages/ExamsPage.tsx`, route `/lich-thi`, mục điều hướng "Lịch
  thi" giữa "Môn học" và "Nhập ảnh": danh sách buổi thi sắp tới theo ngày, công tắc "Hiện buổi thi đã
  qua", nhãn "Trùng giờ" khi có `conflicts`, nút sửa/xoá có `ConfirmDialog` (FR-027).
- [ ] T116 [US11] Hiển thị buổi thi ở frontend (FR-057, FR-058):
  - `TodayPage.tsx`: khối "Buổi thi" phía trên "Buổi học" (giờ, tên học phần, phòng hoặc "Chưa có
    phòng", hình thức thi, SBD, nhãn "Trùng giờ").
  - `lib/calendarEvents.ts`: thêm buổi thi (tiêu đề "Thi: …", màu nhãn "Thi"); bổ sung test trong
    `frontend/tests/calendarEvents.test.ts`.
- [ ] T117 [US11] Nhập ảnh lịch thi ở frontend: `ImportPage.tsx` và `ImportPreviewTable.tsx` xử lý
  `kind`:
  - `"exam_table"`: bảng các cột buổi thi; nhãn "Đã qua" (bỏ chọn), "Đã có trong lịch" (bỏ chọn); ô
    chưa chắc chắn tô vàng; ghi chú "giờ kết thúc tính từ 60p" khi `end_time_source =
    "format_duration"`.
  - `"unknown"`: hỏi "Đây là lịch học hay lịch thi?" rồi gọi lại `recognize?kind=…`.

**Checkpoint**: US6 và US11 pass; quickstart V7, V8, V18 pass; `pytest -m ocr` ≥ 80% cho cả hai loại
ảnh.

---

## Phase 11: User Story 10 - Tự tạo deadline cho môn đặc biệt (Priority: P3)

**Goal**: Buổi học E-Learning hoặc bắt đầu từ 20:00 tự sinh task hạn 08:00 Chủ Nhật kế tiếp, trừ môn
Giáo dục thể chất; quy tắc chỉnh được.

**Independent Test**: Môn "Triết học" + E-Learning học Thứ Ba 4 tuần → 4 task đúng hạn; "Giáo dục
thể chất 2" Thứ Tư 20:30 → 0 task (quickstart V9, V10; SC-015).

### Tests for User Story 10 ⚠️

- [ ] T118 [P] [US10] Test thuần trong `backend/tests/unit/test_auto_deadlines.py`:
  - `eligible`:
    - Môn có nhãn E-Learning → đúng.
    - Buổi có nhãn riêng E-Learning → đúng.
    - Bắt đầu đúng 20:00 → đúng; 19:59 → sai.
    - Buổi huỷ → sai.
    - Tên "giáo dục thể chất 2" (khác hoa thường, dạng NFD) → sai.
  - `due_at`:
    - Buổi Thứ Ba 10/11/2026 → Chủ Nhật 15/11/2026 08:00.
    - Buổi tối Chủ Nhật 15/11 → Chủ Nhật 22/11 08:00.
    - Buổi Chủ Nhật 06:00–07:30 → cùng ngày 08:00.
    - Đổi `auto_deadline_due_time` thì hạn đổi theo.
  - Tiêu đề "Bài tập Triết học – buổi 10/11".
  - `plan` theo đúng bảng trạng thái trong research R9 (tạo, cập nhật, xoá, không đụng task đã sửa
    hoặc đã hoàn thành, không tạo lại khi `auto_task_suppressed`, không tạo khi hạn đã qua).
  - Sau khi reconcile tự cập nhật tiêu đề hoặc hạn của task, task vẫn có `user_modified=False`.
- [ ] T119 [P] [US10] Test API trong `backend/tests/integration/test_auto_deadlines_api.py`:
  - Tạo môn E-Learning → có task trong danh sách "Học tập", ưu tiên 2, `is_auto=true`.
  - Huỷ buổi → task bị xoá; khôi phục → task được tạo lại.
  - Xoá tay task → không tạo lại.
  - Sửa tiêu đề task → đổi giờ buổi không làm task thay đổi.
  - Đổi giờ buổi hai lần liên tiếp khi task **chưa** bị sửa → task cập nhật theo cả hai lần
    (`user_modified` vẫn `false`).
  - PATCH settings `auto_deadline_evening_from` → reconcile các buổi có hạn chưa qua.
  - Gỡ nhãn E-Learning khỏi môn → task chưa sửa bị xoá.
  - Môn GDTC → 0 task.
  - Học kỳ mẫu 15 tuần → số task đúng bằng số buổi thoả điều kiện (SC-015).

### Implementation for User Story 10

- [ ] T120 [US10] Tạo `backend/app/services/auto_deadlines.py`:
  - Hàm thuần `eligible(session, subject_tags, session_tags, settings)`, `due_at(session_end,
    due_time)`, `title_for(subject_name, date)`, `plan(sessions, existing_auto_tasks, settings, now)
    -> list[Create|Update|Delete]`.
  - `reconcile(session_ids=None, subject_id=None, all_future=False)` áp kế hoạch trong transaction
    hiện tại:
    - Tạo task vào danh sách `is_default_study`, `priority=2`, `is_auto=True`, `source_session_id`.
    - Tạo, cập nhật và xoá bằng cách ghi **trực tiếp vào model `Task`**, KHÔNG gọi
      `services.tasks.update_task`/`delete_task`, vì các hàm đó đặt `user_modified=True` hoặc
      `auto_task_suppressed=True`, vốn chỉ dành cho thao tác của người dùng.
    - Gọi `bump_revision`.
- [ ] T121 [US10] Gọi `auto_deadlines.reconcile` ở cuối mỗi hàm ghi (cùng transaction):
  - `services/subjects.py`: create, create_bulk, update, delete.
  - `services/sessions.py`: cancel, restore, update.
  - `services/tags.py`: `set_tags` cho môn và buổi; xoá nhãn.
  - `services/shifts.py`: update, delete.
  - `services/semesters.py`: update, delete.
  - `services/imports.py`: commit.
  - `api/settings.py`: PATCH các trường `auto_deadline_*` → `all_future=True`.
- [ ] T122 [US10] Frontend:
  - Huy hiệu "Tự tạo" và liên kết "Xem buổi học" (mở `SessionDetail`) trong `TaskForm.tsx`, danh
    sách task `TasksPage.tsx` và `TodayPage.tsx`.
  - Tạo `frontend/src/pages/SettingsPage.tsx` với mục "Tự tạo deadline": mốc giờ (mặc định 20:00),
    giờ deadline Chủ Nhật (08:00), danh sách môn ngoại lệ (thêm/xoá từ khoá).
  - SettingsPage cũng chứa liên kết tới Học kỳ, Ca học, Nhãn.

**Checkpoint**: US10 pass; quickstart V9, V10 pass.

---

## Phase 12: User Story 7 - Thông báo nhắc trên Mac và iPhone (Priority: P3)

**Goal**: Đồng bộ buổi học và task vào Lịch/Lời nhắc của Apple kèm báo trước, để iPhone nhắc kể cả
khi Mac gập; thông báo trình duyệt là dự phòng.

**Independent Test**: Bật đồng bộ, tạo buổi học sau 20 phút với nhắc 15 phút, gập Mac → iPhone nhắc
đúng giờ; huỷ buổi → mục biến mất khỏi Lịch (quickstart V11–V14).

**Phụ thuộc**: T011 (spike S2) đã có kết luận.

### Tests for User Story 7 ⚠️

- [ ] T123 [P] [US7] Test thuần trong `backend/tests/unit/test_reminders.py`:
  - Thời điểm nhắc buổi học: mặc định 15 phút; `subject.reminder_minutes=30` ghi đè; `-1` → không
    nhắc.
  - Task có giờ: mặc định 60 phút; task chỉ có ngày → 08:00 ngày đó (`date_only_task_reminder_time`).
  - Task chỉ có ngày với `reminder_minutes=-1` → không nhắc; với `reminder_minutes=30` → vẫn 08:00
    (số phút chỉ áp dụng cho task có giờ).
  - Task đã hoàn thành, buổi huỷ → không nhắc.
  - Buổi thi: mặc định 2 thời điểm (1 ngày và 1 giờ trước); `reminder_offsets=[]` → không nhắc;
    `[120]` → 2 giờ trước; buổi thi đã qua → không nhắc (FR-063).
- [ ] T124 [P] [US7] Test API trong `backend/tests/integration/test_sync_api.py`:
  - `revision` tăng sau mỗi loại thay đổi: task, môn, buổi, học kỳ, ca, buổi thi, settings.
  - `/sync/changes?after=<rev-1>` trả ngay.
  - `/sync/changes?after=<rev>&wait=1` trả sau khoảng 1 giây với cùng `revision`.
  - `/sync/feed`:
    - Mỗi event có **đúng** các khoá `sync_key, fingerprint, title, location, start_at, end_at,
      alarms_minutes_before`; mỗi reminder có **đúng** các khoá `sync_key, fingerprint, title,
      due_at, due_has_time, alarm_at` (FR-052).
    - Buổi thi có trong `events` với `sync_key="exam:{id}"`, tiêu đề "Thi: <tên học phần>",
      `alarms_minutes_before=[1440, 60]`; không chứa số báo danh hay hình thức thi (FR-064).
    - Không có buổi huỷ, task đã hoàn thành, hay buổi trước hôm nay.
    - `fingerprint` ổn định khi không đổi và thay đổi khi đổi phòng.
  - `PUT /sync/agent-status` → `204` và `last_seen_at` được cập nhật.
  - `/reminders/upcoming` trả `[]` khi `calendar_sync_enabled=true`.
  - `/today.notices` có cảnh báo khi agent không liên lạc quá 2 phút hoặc `permission=denied`.
- [ ] T125 [P] [US7] Test API cho nhắc theo từng mục (FR-022) trong
  `backend/tests/integration/test_reminder_settings_api.py`:
  - PATCH `subjects/{id}` `reminder_minutes=30` → feed `alarms_minutes_before=[30]` và
    `/reminders/upcoming` lệch 30 phút; `-1` → `alarms_minutes_before=[]`, không có trong upcoming.
  - PATCH `exams/{id}` `reminder_offsets=[180]` → feed `alarms_minutes_before=[180]`; `[]` → không
    nhắc; PATCH `settings.exam_reminder_offsets=[2880, 30]` → buổi thi dùng mặc định đổi theo.
  - Task có giờ `reminder_minutes=10` → `alarm_at` = hạn − 10 phút.
  - Task chỉ có ngày `reminder_minutes=-1` → `reminder_at=null`, `alarm_at=null`.
  - PATCH `settings.session_reminder_minutes=5` → mọi buổi dùng mặc định đổi `alarms_minutes_before`
    thành `[5]` và `revision` tăng.
- [ ] T126 [P] [US7] Test API cho cập nhật nhắc ngay khi dữ liệu đổi (FR-023) trong
  `backend/tests/integration/test_reminder_updates_api.py`, mỗi bước kiểm tra `/reminders/upcoming`
  (khi đồng bộ tắt) và `/sync/feed` (khi đồng bộ bật) **ngay sau** request ghi, không chờ:
  - Huỷ buổi → mục biến mất; khôi phục → xuất hiện lại.
  - Đổi giờ buổi → `fire_at`/`start_at` mới; đổi hạn task → `alarm_at` mới.
  - Hoàn thành task → biến mất; bỏ hoàn thành → xuất hiện lại; xoá task hoặc môn → biến mất.
  - Đổi giờ buổi thi → các mốc nhắc dời theo; xoá buổi thi → biến mất.
  - Mỗi thao tác làm `revision` tăng đúng trong cùng request.
- [ ] T127 [P] [US7] Test trong `frontend/tests/reminders.test.ts` (Vitest, fake timers, mock
  `Notification` và `navigator.locks`):
  - Hẹn giờ các mục trong 24 giờ tới.
  - Bỏ qua mục quá giờ hơn 1 phút (không hiện dồn).
  - Mỗi `sync_key` hiện đúng 1 lần.
  - Không chạy khi `calendar_sync_enabled=true`.
  - Chỉ tab giữ lock mới hiện thông báo.
  - (FR-023) Khi gọi `refresh()` với danh sách mới không còn một mục (buổi vừa huỷ hoặc task vừa
    hoàn thành), hẹn giờ của mục đó bị huỷ và **không** có thông báo khi tới giờ; mục đổi giờ được
    hẹn lại theo giờ mới.
- [ ] T128 [P] [US7] Test thuần trong `mac-agent/tests/test_reconcile.py` cho
  `plan_changes(feed, current_items, saved_fingerprints)`:
  - Mục thiếu → create; fingerprint lệch → update; mục của app không còn trong feed → delete.
  - Lịch hoặc danh sách bị người dùng xoá → tạo lại.
  - `sync_enabled=false` → `remove_all`.
  - Không bao giờ đụng mục không có `URL` dạng `lichhoc://`.
  Thêm test `main.run_once` với `FakeCalendarStore` và `FakeBackend`.

### Implementation for User Story 7

- [ ] T129 [US7] Tạo `backend/app/services/reminders.py`: `session_alarm_minutes(session,
  settings)`, `task_alarm_at(task, settings)`, `upcoming(now, hours)`. Điền `TaskOut.reminder_at`.
  - Quy tắc `reminder_minutes`: `-1` tắt nhắc cho **mọi** task (kể cả task chỉ có ngày) và mọi môn;
    `NULL` dùng mặc định; số ≥ 0 chỉ có tác dụng với buổi học và task có giờ.
  - Buổi thi: `exam_alarm_offsets(exam, settings)` dùng `services.exams.resolve_offsets`;
    `upcoming` trả một mục cho mỗi mốc với `sync_key="exam:{id}:{phút}"`.
- [ ] T130 [US7] Tạo `backend/app/services/sync_feed.py`:
  - `build_feed(today)` theo contracts/calendar-sync.md §2: chỉ các trường cho phép; task gồm cả
    quá hạn trong 7 ngày gần nhất; `events` gồm buổi học chưa huỷ và buổi thi, mỗi event có
    `alarms_minutes_before` là danh sách.
  - `fingerprint(item)` = SHA-256 của JSON đã sắp khoá.
  - `wait_for_change(after, wait)`: kiểm tra `sync_state.revision` mỗi 1 giây bằng session mới, tối
    đa `wait ≤ 25` giây.
- [ ] T131 [US7] Tạo blueprint `backend/app/api/sync.py` (`GET /api/sync/changes`, `GET
  /api/sync/feed`, `PUT /api/sync/agent-status`, `GET /api/sync/status`) và
  `backend/app/api/reminders.py` (`GET /api/reminders/upcoming`). Thêm `notices` về agent và đồng
  bộ vào `services/today.py`.
- [ ] T132 [US7] Tạo frontend nhắc dự phòng:
  - `frontend/src/reminders/scheduler.ts`: hàm thuần lên lịch, nhận `now` và danh sách mục.
  - `frontend/src/reminders/leader.ts`: bọc `navigator.locks.request('lichhoc-reminders', …)`.
  - `frontend/src/reminders/useReminders.ts`: gắn ở `App.tsx`; tải `/api/reminders/upcoming` mỗi 5
    phút **và ngay sau mỗi thay đổi dữ liệu**: đăng ký `queryClient.getMutationCache().subscribe`,
    khi một mutation thành công thì gọi `refresh()`. `refresh()` huỷ mọi hẹn giờ cũ rồi hẹn lại theo
    danh sách mới (FR-023). Hiện thông báo bằng `new Notification(title, {body, tag: sync_key})`.
  - Nút "Bật thông báo trình duyệt" kèm giải thích; khi quyền là `denied`, hiện hướng dẫn trên
    TodayPage.
- [ ] T133 [US7] Thêm vào `frontend/src/pages/SettingsPage.tsx`:
  - Mục "Nhắc lịch": phút nhắc mặc định cho buổi học và cho task, giờ nhắc task chỉ có ngày, các
    mốc nhắc buổi thi (mặc định "1 ngày" và "1 giờ" trước, thêm/bớt mốc).
  - Công tắc "Đồng bộ với Lịch và Lời nhắc".
  - Trạng thái agent: "Chưa cài/không chạy" kèm hướng dẫn chạy `mac-agent/scripts/install.sh`, "Bị
    từ chối quyền" kèm hướng dẫn mở Cài đặt hệ thống, "Không có iCloud — iPhone sẽ không nhận được",
    "Đã đồng bộ lúc …".
  - Hộp thoại lần đầu đề nghị bật đồng bộ (dùng `calendar_sync_prompted`).
  - Chọn nhắc riêng hoặc tắt nhắc trong `ExamForm` (`reminder_offsets`: "Theo mặc định" / "Không
    nhắc" / danh sách mốc riêng).
  - Chọn nhắc riêng hoặc tắt nhắc trong `SubjectForm` và `TaskForm` (`reminder_minutes`): ô chọn
    "Theo mặc định" / "Không nhắc" / "Nhắc trước … phút". Với task chỉ có ngày, chỉ hiện "Theo
    mặc định (08:00)" / "Không nhắc".
- [ ] T134 [P] [US7] Tạo `mac-agent/lichhoc_agent/reconcile.py`: hàm thuần `plan_changes(...) ->
  Plan(create, update, delete, remove_all, recreate_containers)` theo contracts/calendar-sync.md §4.
- [ ] T135 [P] [US7] Tạo `mac-agent/lichhoc_agent/backend_client.py` (`changes(after, wait)`,
  `feed()`, `put_status(...)`; timeout 35 giây) và `mac-agent/lichhoc_agent/state.py` (đọc/ghi
  nguyên tử `~/Library/Application Support/LichHocAgent/state.json` gồm `calendar_id`,
  `reminder_list_id`, `fingerprints`).
- [ ] T136 [US7] Tạo `mac-agent/lichhoc_agent/calendar_store.py`:
  - `Protocol CalendarStore` (`ensure_containers`, `list_items`, `create`, `update`, `delete`,
    `remove_containers`, `commit`, `permission`, `source_kind`).
  - `FakeCalendarStore` cho test.
  - `EventKitStore` dùng PyObjC:
    - Xin quyền đầy đủ; tìm nguồn iCloud (`EKSourceTypeCalDAV` có tiêu đề "iCloud"), nếu không có
      thì nguồn cục bộ.
    - Danh sách lời nhắc phải tạo trong nguồn `defaultCalendarForNewReminders().source()`, không
      dùng nguồn của Lịch (lỗi `EKErrorDomain Code=24`, research R4).
    - Tạo `EKCalendar` cho sự kiện và cho lời nhắc tên "Lịch Học Cá Nhân".
    - Ánh xạ trường đúng contracts/calendar-sync.md §5, `URL=lichhoc://session/{id}`,
      `lichhoc://exam/{id}` hoặc `lichhoc://task/{id}`; mỗi phần tử `alarms_minutes_before` là một
      `EKAlarm`.
    - Chỉ thao tác trên hai `calendarIdentifier` trong `state.json`.
- [ ] T137 [US7] Tạo `mac-agent/lichhoc_agent/main.py`:
  - Vòng lặp `changes` → `feed` → `plan_changes` → áp lên store → `commit` → `put_status`.
  - Thử lại khi backend lỗi: 30 giây → tăng dần tới 5 phút, **không** xoá mục đã ghi.
  - Log xoay vòng `~/Library/Logs/LichHocAgent/agent.log` (1 MB × 3).
  - Hàm `run_once()` để test.
- [ ] T138 [US7] Tạo `mac-agent/launchd/vn.lichhoc.agent.plist` (`Label=vn.lichhoc.agent`,
  `RunAtLoad=true`, `KeepAlive=true`, `ProgramArguments` trỏ tới
  `~/Applications/LichHocAgent.app/Contents/MacOS/LichHocAgent`) và `mac-agent/scripts/install.sh`:
  - Tạo venv bằng Homebrew `/opt/homebrew/opt/python@3.11/bin/python3.11` (Python dạng framework;
    Python do uv cài không chạy được py2app, xem research R4).
  - Chạy `python setup.py py2app` từ một **thư mục tạm không có `pyproject.toml`** (chép `setup.py`,
    `app_plist.py`, `lichhoc_agent/` sang), vì py2app báo lỗi `install_requires is no longer
    supported` khi gặp `[project].dependencies`. Sau đó chạy `codesign --force --deep -s -`.
  - Chép app vào `~/Applications/`, chép plist vào `~/Library/LaunchAgents/`.
  - `launchctl bootout` (bỏ qua lỗi) rồi `launchctl bootstrap gui/$UID …`.
  - Tuỳ chọn `--uninstall`.

**Checkpoint**: US7 pass; quickstart V11–V14 pass.

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Tài liệu, sao lưu, hiệu năng, kiểm chứng toàn bộ.

- [ ] T139 [P] Tạo `scripts/backup.sh` (`docker compose exec -T db pg_dump -U lichhoc -Fc lichhoc >
  backups/lichhoc-$(date +%Y%m%d-%H%M).dump`, tự tạo thư mục `backups/`) và `scripts/restore.sh
  <file>` (hỏi "Ghi đè dữ liệu hiện tại? (y/N)", rồi `pg_restore --clean --if-exists -U lichhoc -d
  lichhoc`).
- [ ] T140 [P] Tạo `backend/app/cli.py` với lệnh `flask seed-demo`: 1 học kỳ, 6 môn (2 môn
  E-Learning, 1 môn 20:30), 200 task rải trong học kỳ, vài nhãn. Đăng ký trong `create_app`.
- [ ] T141 Viết `README.md` bằng tiếng Việt:
  - Giới thiệu; yêu cầu (macOS 14+, OrbStack, cần internet chỉ ở lần build đầu).
  - Chạy bằng `docker compose up -d --build`; mở `http://127.0.0.1:8080`.
  - Cài agent (`mac-agent/scripts/install.sh`) và bật đồng bộ; lưu ý chữ ký ad-hoc có thể khiến
    macOS hỏi lại quyền sau khi build lại.
  - Vị trí dữ liệu (volume `lichhoc_pgdata`, trong OrbStack tại
    `~/OrbStack/docker/volumes/lichhoc_pgdata`).
  - ⚠️ `docker compose down -v` xoá dữ liệu.
  - Sao lưu và khôi phục (`scripts/backup.sh`, `scripts/restore.sh`).
  - Chạy test (theo quickstart.md).
  - Xử lý sự cố: agent không chạy, bị từ chối quyền, không có iCloud.
- [ ] T142 [P] Kiểm tra chuỗi tiếng Việt và kết nối ngoài:
  - Tìm chuỗi tiếng Anh còn hiển thị trong `frontend/src/` (ngoài `i18n/vi.ts`) và `message` của
    `ApiError` ở backend.
  - Kiểm tra `frontend/dist` không chứa URL `http(s)://` ngoài localhost; backend không gọi mạng
    ngoài (V15).
  - Sửa mọi chỗ còn sót.
- [ ] T143 Đo hiệu năng với `flask seed-demo`: trang Hôm nay < 2 giây (SC-005); chuyển chế độ xem và
  lọc nhãn < 1 giây (SC-006, SC-016). Nếu chậm thì thêm index hoặc eager-load trong
  `services/calendar.py` và `services/today.py`.
- [ ] T144 [P] Thêm `.pre-commit-config.yaml` (ruff check/format cho `backend/` và `mac-agent/`,
  eslint/prettier cho `frontend/`).
- [ ] T145 Chạy toàn bộ kịch bản quickstart V1–V17 trên máy thật (gồm V12 với iPhone, V15 tắt Wi-Fi,
  V16 thử từ máy khác trong LAN). Ghi kết quả pass/fail kèm ghi chú vào
  `specs/001-task-class-scheduler/validation.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: bắt đầu ngay. T010 và T011 (spike) chạy song song với phần còn lại.
- **Foundational (Phase 2)**: sau Setup; chặn mọi user story.
- **User stories (Phase 3–12)**: sau Foundational, theo thứ tự ưu tiên.
- **Polish (Phase 13)**: sau các story mong muốn.

### User Story Dependencies

| Story | Phụ thuộc | Ghi chú |
|-------|-----------|---------|
| US1 Task (P1) | Foundational | Độc lập |
| US2 Môn học (P1) | Foundational | Độc lập; tạm nhập giờ tay |
| US3 Hôm nay (P1) | US1, US2 | Cần task và buổi học để hiển thị |
| US4 Ngoại lệ buổi (P2) | US2 | |
| US5 Lịch (P2) | US1, US2 | Dùng `SessionDetail` (US4) nếu đã có, nếu chưa thì chỉ xem |
| US8 Ca học (P2) | US2 | Thay ô giờ trong form của US2 |
| US9 Nhãn (P2) | US1, US2, US5 | Màu nhãn và bộ lọc trên lịch |
| US6 Nhập ảnh (P2) | US2, US8, T010 | Đối chiếu ca; gợi ý nhãn E-Learning dùng nhãn hệ thống đã có |
| US10 Deadline tự tạo (P3) | US1, US2, US9 | Cần nhãn E-Learning gắn được |
| US11 Lịch thi (P2) | US2, US3, US5, US9, US6 (pipeline OCR), T010 | Làm cùng phase với US6; trùng giờ cần buổi học; hiển thị cần lịch và nhãn |
| US7 Nhắc (P3) | US1, US2, T011 | Có thể làm trước US10; feed tự gồm task tự tạo khi US10 xong và buổi thi khi US11 xong |

### Within Each User Story

- Test viết trước và phải FAIL → schema → service (hàm thuần trước) → API → frontend.
- Mọi service ghi dữ liệu gọi `bump_revision`. Từ Phase 11, mọi service ghi còn gọi
  `auto_deadlines.reconcile`.

### Parallel Opportunities

- Phase 1: T003, T004, T005, T007, T008, T009, T010, T011 song song sau T001–T002.
- Phase 2: model T018–T025 song song; T015–T017, T028, T029, T032–T034, T037 song song.
- Trong mỗi story: các task test `[P]` chạy song song; hook API frontend `[P]` song song với service
  backend.
- Sau MVP: US4, US8 song song (cùng phụ thuộc US2); agent (T134–T138) song song với phần backend của
  US7 (T129–T131), vì giao tiếp qua contract đã cố định.

---

## Parallel Example: User Story 6

```bash
# Viết test song song:
Task: "Test thuần fields trong backend/tests/unit/test_ocr_fields.py"            # T088
Task: "Test thuần layout trong backend/tests/unit/test_ocr_layout.py"            # T089
Task: "Test thuần month_year trong backend/tests/unit/test_ocr_month_year.py"    # T090
Task: "Test thuần preview trong backend/tests/unit/test_import_preview.py"       # T091
Task: "Test API imports trong backend/tests/integration/test_imports_api.py"     # T092

# Rồi cài đặt song song hai module độc lập:
Task: "backend/app/ocr/preprocess.py"   # T094
Task: "backend/app/ocr/reader.py"       # T095
```

## Parallel Example: User Story 7

```bash
# Backend và agent song song (cùng contract calendar-sync.md):
Task: "Test sync API trong backend/tests/integration/test_sync_api.py"   # T124
Task: "Test reconcile trong mac-agent/tests/test_reconcile.py"           # T128
Task: "mac-agent/lichhoc_agent/reconcile.py"                             # T134
Task: "mac-agent/lichhoc_agent/backend_client.py + state.py"             # T135
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Phase 1 Setup, chạy 2 spike song song để có kết luận sớm.
2. Phase 2 Foundational.
3. US1 → US2 → US3. Ứng dụng đã dùng hằng ngày được: task, lịch học lặp, trang Hôm nay.
4. **DỪNG và KIỂM CHỨNG** quickstart V1, V2, V3 (phần giờ tay).

### Incremental Delivery

1. MVP.
2. US4 + US8: lịch học khớp thực tế (ngoại lệ, ca).
3. US5 + US9: xem lịch và nhãn.
4. US6 + US11: nhập ảnh lịch học, rồi lịch thi (quản lý, nhập ảnh bảng lịch thi). Làm sau cùng
   trong nhóm P2 vì rủi ro cao nhất và cần ảnh mẫu.
5. US10 → US7: tự động hoá và nhắc trên iPhone.
6. Polish và kiểm chứng toàn bộ V1–V18.

---

## Notes

- `[P]` = khác file, không phụ thuộc task chưa xong.
- Commit sau mỗi task hoặc nhóm task logic; lint và test phải pass trước khi merge (constitution).
- Ảnh mẫu thật phải che thông tin cá nhân trước khi commit.
- Không thêm phụ thuộc ngoài danh sách trong plan.md nếu chưa ghi lý do (constitution: Ràng buộc bổ
  sung).
