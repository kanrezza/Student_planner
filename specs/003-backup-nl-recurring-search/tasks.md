---

description: "Danh sách task cho feature 003 — sao lưu tự động, thêm nhanh bằng câu tiếng Việt, tìm kiếm, task lặp lại"
---

# Tasks: Sao lưu tự động, thêm nhanh bằng câu tiếng Việt, task lặp lại và tìm kiếm

**Input**: Design documents from `specs/003-backup-nl-recurring-search/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Có — constitution II bắt buộc test cho chức năng chính; mọi test chạy qua `./scripts/test.sh`. Test
viết trước và phải FAIL trước khi làm phần cài đặt tương ứng.

**Organization**: Theo user story của spec. Thứ tự phase đi theo **4 đợt** của plan (chỉ dẫn của người dùng:
sao lưu & khôi phục → thêm nhanh tự nhiên → tìm kiếm → task lặp lại), nên US3 (task lặp, P2) nằm sau US5 (tìm
kiếm, P3). Hai kịch bản lặp của US4 (US4-7, US4-8) cần task lặp nên được bật ở phase của US3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Chạy song song được (khác file, không phụ thuộc task chưa xong)
- **[Story]**: User story của spec (US1…US5)
- Đường dẫn tính từ gốc repo: `backend/`, `frontend/`, `mac-agent/`, `desktop/`, `scripts/`

## Đợt và phase

| Đợt | Phase | User story |
|-----|-------|------------|
| — | 1 Setup, 2 Foundational | — |
| 1 | 3 (US1), 4 (US2) | Sao lưu tự động, khôi phục |
| 2 | 5 (US4) | Thêm nhanh bằng câu tiếng Việt (chưa bật cụm lặp) |
| 3 | 6 (US5) | Tìm kiếm |
| 4 | 7 (US3) | Task lặp lại (+ bật cụm lặp trong thêm nhanh) |
| — | 8 Polish | — |

Cuối mỗi đợt: `./scripts/test.sh` pass → commit (không thêm dòng Co-Authored-By / "Generated with Claude Code",
xem `CLAUDE.md`) → hướng dẫn thử bằng tiếng Việt theo [quickstart.md](quickstart.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Phụ thuộc mới cho cả feature.

- [x] T001 Cài `postgresql-client-16` từ kho apt PGDG trong `backend/Dockerfile` (thêm khoá `https://www.postgresql.org/media/keys/ACCC4CF8.asc`, nguồn `apt.postgresql.org` bookworm-pgdg, `apt-get install -y --no-install-recommends postgresql-client-16`; comment: chỉ cần internet lúc build, research R2); kiểm tra `docker compose run --rm backend pg_dump --version` in `16.x`
- [x] T002 [P] Thêm `pyobjc-framework-UserNotifications>=10.3` vào `mac-agent/pyproject.toml` và gói `UserNotifications` vào `packages`/`includes` của py2app trong `mac-agent/setup.py`
- [x] T003 [P] Thêm `tauri-plugin-dialog = "2"` và `tauri-plugin-deep-link = "2"` vào `desktop/src-tauri/Cargo.toml`; khai báo scheme `lichhoc` trong `plugins.deep-link.desktop.schemes` của `desktop/src-tauri/tauri.conf.json`
- [x] T004 [P] Thêm mục chữ tiếng Việt rỗng cho các nhóm `backup`, `quickAdd`, `search`, `recurrence` trong `frontend/src/i18n/vi.ts` (các task sau điền chữ vào đúng nhóm)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Gỡ rủi ro kiến trúc của agent trước khi làm sao lưu (research R10).

**⚠️ CRITICAL**: Phase 3 không bắt đầu trước khi T005–T007 xong.

- [x] T005 Spike `mac-agent/spikes/notify_thread_spike.py`: chạy `PyObjCTools.AppHelper.runConsoleEventLoop` trên luồng chính, một luồng nền gọi `EKEventStore` (đọc danh sách lịch) mỗi 5 giây và gửi một thông báo `UNUserNotificationCenter` có delegate nhận click (click → `subprocess.run(["open", "lichhoc://cai-dat/sao-luu"])`); build bằng py2app như agent thật; ghi kết quả (được / không được, lỗi gặp) vào cuối `specs/003-backup-nl-recurring-search/research.md` mục R10
- [x] T006 Nếu T005 thất bại: sửa `specs/003-backup-nl-recurring-search/plan.md` (Complexity Tracking + Rủi ro) và `contracts/agent-backup.md` mục Thông báo sang phương án `osascript -e 'display notification …'` (không mở Cài đặt khi bấm), ghi rõ lệch FR-008; nếu T005 thành công: ghi "Spike OK" và bỏ qua
- [x] T007 Tách vòng lặp đồng bộ của `mac-agent/lichhoc_agent/main.py` sang luồng nền: `main()` khởi tạo luồng `daemon=True` chạy `run_forever`, luồng chính chạy vòng lặp sự kiện Cocoa (theo kết quả T005); giảm `RETRY_MAX` từ 300 xuống 120 (research R5); `--once` vẫn chạy đồng bộ trên luồng chính; cập nhật `mac-agent/tests/test_main.py` cho `RETRY_MAX = 120` và chạy lại toàn bộ test agent

**Checkpoint**: Agent chạy hai luồng, đồng bộ Lịch/Lời nhắc vẫn đúng (test agent pass, kiểm tay một lần đồng bộ).

---

## Phase 3: User Story 1 — Sao lưu tự động hằng ngày (Priority: P1) 🎯 MVP · Đợt 1

**Goal**: Mỗi ngày (mặc định 21:00) tự sao lưu vào thư mục chọn, sao lưu bù, giữ N bản, trạng thái và "Sao lưu
ngay" trong Cài đặt, cảnh báo nhẹ + thông báo macOS khi quá 3 ngày.

**Independent Test**: quickstart B1–B5, B10 — đặt giờ = bây giờ + 2 phút, có bản mới trong thư mục, trạng thái
đúng; 5 lần "Sao lưu ngay" với giữ lại 3 → còn 3 bản; tháo SSD → cảnh báo nhẹ, cắm lại → bản bù.

### Tests cho User Story 1 ⚠️

- [x] T008 [P] [US1] Test hàm thuần `backup_due(now, schedule_time, enabled, last_success_at, last_attempt_at)` trong `mac-agent/tests/test_backup_schedule.py`: đúng 21:00; trước giờ; ngủ 18:00→07:30 hôm sau (đến hạn, một lần); tắt 3 ngày (một lần); đổi giờ sang 22:00; vừa thất bại < 4 phút (chưa đến hạn) và ≥ 4 phút (đến hạn); `enabled=False`; chưa từng sao lưu; đồng hồ lùi (last_success_at ở tương lai) — theo `contracts/agent-backup.md`
- [x] T009 [P] [US1] Test `parse_backup_name`, `unique_name`, `prune` trong `mac-agent/tests/test_backup_files.py`: ba loại `tu-dong`/`thu-cong`/`truoc-khoi-phuc`; file lạ (`ghi-chu.txt`, `LichHoc-abc.lhbackup`) bị bỏ qua; dạng chỉ-trên-iCloud `.LichHoc-2026-11-05-2100-tu-dong.lhbackup.icloud` được nhận với `location="icloud"`; trùng phút → `-2`, `-3`; 16 bản giữ 14; giảm còn 7; `keep` ≥ số bản không xoá gì; file lạ không bao giờ nằm trong danh sách xoá; `protect=<bản cũ nhất>` khi đang có 15 bản với giữ 14 → bản đó KHÔNG bị xoá (FR-006, khôi phục bản cũ nhất)
- [x] T010 [P] [US1] Test `resolve_destination(config, fs)` với hệ thống file giả trong `mac-agent/tests/test_backup_destination.py`: `destination_path=None` + có `com~apple~CloudDocs` → tạo `Lịch Học Cá Nhân/Sao lưu`, `state="ok"`; không có `com~apple~CloudDocs` → `icloud_off`; đường dẫn tự chọn không tồn tại → `missing` và KHÔNG tạo thư mục; `PermissionError` → `no_permission`; câu `message` tiếng Việt đúng như `contracts/agent-backup.md`
- [x] T011 [P] [US1] Test `run_backup` với backend giả (trả file + `X-Backup-Sha256`) và thư mục tạm trong `mac-agent/tests/test_backup_run.py`: thành công → file tên thật, không còn `.partial`, `last_success_at` cập nhật, `prune` chạy sau; SHA-256 sai → không có file tên thật, bản cũ còn nguyên, `last_attempt_ok=False`; thư mục `missing` → không gọi backend, không ném lỗi; file `.partial` cũ hơn 1 ngày bị dọn
- [x] T012 [P] [US1] Test `stale_notice_due(now, last_success_at, enabled_since, notified_for)` trong `mac-agent/tests/test_notify.py`: chưa đủ 3 ngày; vừa quá 3 ngày → True; đã gửi cho cùng mốc → False; có bản thành công mới rồi lại quá 3 ngày → True; chưa từng có bản, tính từ `enabled_since`
- [x] T013 [P] [US1] Test tích hợp `GET /api/backup/dump` trong `backend/tests/integration/test_backup_api.py`: trả `application/zip` gồm `manifest.json` (đủ khoá `format=1`, `created_at`, `kind`, `schema_revision`, `app_version`, `dump_sha256`, `dump_size`, `counts`) và `data.dump`; header `X-Backup-Name` khớp mẫu `LichHoc-YYYY-MM-DD-HHMM-<kind>.lhbackup`, `X-Backup-Sha256` đúng; `pg_restore --list` đọc được dump; dump KHÔNG chứa dữ liệu bảng `backup_config`, `backup_status`, `backup_jobs`, `agent_status` (research R9); `kind` lạ → 400
- [x] T014 [P] [US1] Test tích hợp cấu hình và trạng thái trong `backend/tests/integration/test_backup_status_api.py`: `GET /backup/status` mặc định `enabled=true`, `schedule_time="21:00"`, `destination_path=null`, `destination_display="iCloud Drive › Lịch Học Cá Nhân › Sao lưu"`, `retention_count=14`; `PATCH /backup/config` `retention_count` 0 hoặc 366 → 400 (ràng buộc `BETWEEN 1 AND 365`); `destination_path` không bắt đầu bằng `/` → 400 "Đường dẫn thư mục phải là đường dẫn đầy đủ"; PATCH làm tăng revision đồng bộ; `PUT /backup/agent-report` cập nhật `files`, `last_attempt`, `last_success`, `destination`; `stale` = true khi `last_success_at` (hoặc `enabled_since`) cũ hơn 3 ngày; `agent_online=false` khi `reported_at` > 2 phút
- [x] T015 [P] [US1] Test tích hợp việc sao lưu trong `backend/tests/integration/test_backup_jobs_api.py`: `POST /backup/jobs {"kind":"backup_now"}` → 201 và `GET /sync/changes` có `backup_jobs_pending=1`; tạo việc thứ hai khi việc đầu `pending`/`running` → 409 `job_running`; `POST /backup/jobs/claim` → job `running`, gọi lại → 204; `PUT /backup/jobs/{id}` chuyển `done`/`failed`; việc `running` quá 30 phút không cập nhật → `failed` "Trình sao lưu không phản hồi"
- [x] T016 [P] [US1] Test Vitest `frontend/tests/backupSettings.test.tsx`: hiện "Lần gần nhất: 21:00 Thứ Năm, 05/11/2026 — 2,4 MB — Thành công"; lần gần nhất thất bại hiện lý do và vẫn hiện lần thành công gần nhất; `destination.state="missing"` hiện cảnh báo nhẹ (không phải hộp thoại); nút "Sao lưu ngay" bị vô hiệu và có trạng thái "Đang sao lưu…" khi có job `running`; `agent_online=false` hiện "Trình đồng bộ chạy nền chưa chạy, chưa sao lưu được"; ngoài Tauri hiện ô nhập đường dẫn thay cho "Chọn thư mục…"
- [x] T017 [P] [US1] Test hàm thuần `destinationDisplay(path)` trong `frontend/tests/destinationDisplay.test.ts`: `null` → "iCloud Drive › Lịch Học Cá Nhân › Sao lưu"; `/Users/x/Library/Mobile Documents/com~apple~CloudDocs/A/B` → "iCloud Drive › A › B"; `/Volumes/SSD/Sao lưu` → "SSD › Sao lưu"; đường dẫn khác giữ nguyên với `~` thay thư mục home
- [x] T018 [P] [US1] Test Rust trong `desktop/src-tauri/src/backup_cmds.rs` (`#[cfg(test)]`): `validate_reveal_path` chỉ nhận đường dẫn tuyệt đối tới thư mục có thật hoặc file kết thúc `.lhbackup`; từ chối đường dẫn tương đối, `..`, file khác đuôi; `deep_link.rs`: `lichhoc://cai-dat/sao-luu` → `http://127.0.0.1:8080/cai-dat/sao-luu`, mọi đường dẫn khác → `None`

### Implementation cho User Story 1

- [x] T019 [US1] Migration `backend/migrations/versions/0006_backup.py` + model `backend/app/models/backup.py` (đăng ký trong `backend/app/models/__init__.py`) theo data-model §1: `backup_config` một dòng (`CHECK id = 1`; `enabled` boolean mặc định `true`; `schedule_time` time mặc định `21:00`; `destination_path` text NULL "NULL = thư mục mặc định trong iCloud Drive"; `retention_count` smallint mặc định 14 `BETWEEN 1 AND 365`; `enabled_since` timestamptz mặc định `now()`; `updated_at`); `backup_status` một dòng (`destination_resolved`, `destination_state` CHECK trong `ok`|`missing`|`no_permission`|`icloud_off`|`not_writable`, `destination_message`, `last_attempt_at`, `last_attempt_ok`, `last_attempt_error`, `last_attempt_size` bigint, `last_success_at`, `last_success_size`, `files` jsonb mặc định `[]`, `reported_at`); `backup_jobs` (`kind` CHECK `backup_now`|`restore`; `source_path` bắt buộc khi `restore`; `state` CHECK `pending`|`running`|`done`|`failed`; `step`; `message`; `created_at`, `started_at`, `finished_at`; unique index một phần "tối đa một việc `pending`/`running`"); seed một dòng cho hai bảng một dòng
- [x] T020 [US1] Service `backend/app/services/backup.py` phần sao lưu: `build_backup(kind) -> (path, name, sha256)` — chạy `pg_dump -Fc --exclude-table-data=backup_config --exclude-table-data=backup_status --exclude-table-data=backup_jobs --exclude-table-data=agent_status` vào file tạm (thông tin kết nối lấy từ `DATABASE_URL`, mật khẩu qua biến `PGPASSWORD`), kiểm tra `pg_restore --list`, đếm bản ghi các bảng chính cho `counts`, đọc `schema_revision` từ `alembic_version`, ghi ZIP `STORED` (`manifest.json` + `data.dump`), tính SHA-256; `backup_name(created_at, kind)`; lỗi → `BackupError("dump_failed", "<tiếng Việt>")`; xoá file tạm sau khi gửi
- [x] T021 [US1] Service `backend/app/services/backup_jobs.py`: `get_config`, `update_config` (gọi `bump_revision`; `destination_path` khác null phải bắt đầu bằng `/`), `apply_agent_report`, `status_view(now)` (tính `stale`, `agent_online`, `destination_display` theo T017 phía Python), `create_job` (409 `job_running`, gọi `bump_revision`), `claim_job`, `update_job`, `expire_stuck_jobs(now)` (`running` > 30 phút → `failed` "Trình sao lưu không phản hồi"); schema pydantic trong `backend/app/schemas/backup.py`
- [x] T022 [US1] Blueprint `backend/app/api/backup.py` (đăng ký trong `backend/app/__init__.py`): `GET /backup/status`, `GET`/`PATCH /backup/config`, `POST /backup/jobs`, `POST /backup/jobs/claim`, `PUT /backup/jobs/<id>`, `GET /backup/dump?kind=` (stream file, header `X-Backup-Name`, `X-Backup-Sha256`, `Content-Length`), `PUT /backup/agent-report` — đúng `contracts/rest-api.md`
- [x] T023 [US1] Thêm `backup_jobs_pending` và `backup_config_revision` vào phản hồi `GET /sync/changes` trong `backend/app/api/sync.py`; cập nhật test hiện có của `/sync/changes` trong `backend/tests/integration/test_sync_api.py`
- [x] T024 [P] [US1] Mở rộng `mac-agent/lichhoc_agent/backend_client.py`: `backup_config()`, `claim_job()` (204 → `None`), `update_job(id, **fields)`, `download_backup(kind, dest_file) -> (name, sha256)` (stream theo khối 1 MB), `put_backup_report(report)`
- [x] T025 [P] [US1] Mở rộng `mac-agent/lichhoc_agent/state.py`: khoá `backup_last_attempt_at`, `backup_last_success_at`, `stale_notified_for` (ISO string hoặc `None`), đọc/ghi nguyên tử như các khoá hiện có; thêm test đọc/ghi vào `mac-agent/tests/test_state.py`
- [x] T026 [US1] Module `mac-agent/lichhoc_agent/backup.py`: `backup_due` (T008), `parse_backup_name`, `unique_name`, `prune` (T009), `resolve_destination` (T010; thư mục mặc định `~/Library/Mobile Documents/com~apple~CloudDocs/Lịch Học Cá Nhân/Sao lưu`), `list_backups(dir)` (đọc manifest khi file có trên máy, suy từ tên khi chỉ có trên iCloud), `run_backup(kind, backend, state, config, job=None, protect=None)` (T011: `.partial` → `fsync` → đọc lại SHA-256 → `os.replace` → `prune(..., protect)` (mỗi file bị xoá log INFO "Đã xoá bản sao lưu cũ: <tên>") → ghi trạng thái → log INFO "Sao lưu xong: <tên> (<dung lượng>)"; lỗi → log ERROR kèm lý do, xoá `.partial`, không xoá bản cũ), `backup_tick(now, backend, state, changes)`
- [x] T027 [P] [US1] Module `mac-agent/lichhoc_agent/notify.py`: `stale_notice_due` (T012), `send_stale_notice()` (tiêu đề "Lịch Học Cá Nhân", nội dung "Đã 3 ngày chưa sao lưu được dữ liệu. Mở Cài đặt → Sao lưu để kiểm tra.", xin quyền lần đầu; bị từ chối → log WARNING, không lỗi), delegate click → `open lichhoc://cai-dat/sao-luu`; theo phương án chốt ở T005/T006
- [x] T028 [US1] Gọi `backup_tick` sau mỗi lần xử lý `changes` trong `run_forever` của `mac-agent/lichhoc_agent/main.py`: làm mới cache cấu hình khi `backup_config_revision` đổi; `claim_job` khi `backup_jobs_pending > 0`; `backup_now` → `run_backup("thu-cong", job)` + `update_job`; ngoài ra `backup_due` → `run_backup("tu-dong")`; `stale_notice_due` → gửi thông báo và lưu `stale_notified_for`; `put_backup_report` khi có thay đổi hoặc mỗi 60 giây; mọi lỗi sao lưu được bắt riêng, không làm dừng đồng bộ Lịch
- [x] T029 [P] [US1] Lệnh Rust `desktop/src-tauri/src/backup_cmds.rs`: `pick_backup_folder() -> Option<String>` (hộp chọn thư mục của `tauri-plugin-dialog`, tiêu đề "Chọn thư mục sao lưu"), `pick_backup_file() -> Option<String>` (lọc `lhbackup`), `reveal_in_finder(path)` (kiểm tra bằng `validate_reveal_path` của T018 rồi `open -R`); đăng ký plugin dialog và ba lệnh trong `desktop/src-tauri/src/main.rs`
- [x] T030 [P] [US1] Capability `desktop/src-tauri/capabilities/backup.json`: `windows: ["main"]`, `remote.urls: ["http://127.0.0.1:8080/*"]`, chỉ ba quyền của T029 (định nghĩa trong `desktop/src-tauri/permissions/backup.toml`); KHÔNG cấp quyền plugin dialog/shell trực tiếp (research R11)
- [x] T031 [P] [US1] Deep link `desktop/src-tauri/src/deep_link.rs`: đăng ký `tauri-plugin-deep-link`, khi nhận `lichhoc://cai-dat/sao-luu` thì hiện + focus cửa sổ chính và điều hướng webview tới `http://127.0.0.1:8080/cai-dat/sao-luu` (hàm thuần ánh xạ ở T018); app đang tắt thì mở rồi điều hướng sau khi backend sẵn sàng
- [x] T032 [P] [US1] `frontend/src/app/desktopBridge.ts`: `isDesktop()`, `pickBackupFolder()`, `pickBackupFile()`, `revealInFinder(path)` gọi `window.__TAURI_INTERNALS__.invoke` khi có, ngoài Tauri trả `null`
- [x] T033 [P] [US1] API client `frontend/src/api/backup.ts` (+ kiểu trong `frontend/src/api/types.ts`, khoá trong `frontend/src/api/keys.ts`): `useBackupStatus()` (poll 2 giây khi có `job` chưa xong, nếu không thì 30 giây), `usePatchBackupConfig()`, `useCreateBackupJob()`
- [x] T034 [P] [US1] Hàm thuần `frontend/src/features/settings/destinationDisplay.ts` (T017) và định dạng dung lượng "2,4 MB" trong `frontend/src/lib/format.ts`
- [x] T035 [US1] Trang `frontend/src/features/settings/BackupSettings.tsx` theo `contracts/ui.md` mục Cài đặt → Sao lưu (thẻ trạng thái, "Sao lưu ngay", công tắc + giờ dùng ô giờ hiện có, thư mục với "Chọn thư mục…"/"Dùng thư mục mặc định"/"Mở trong Finder", "Giữ lại [N] bản gần nhất" 1–365, danh sách bản — nút "Khôi phục" để trống hành vi cho US2); chữ trong nhóm `backup` của `frontend/src/i18n/vi.ts`; đăng ký mục "Sao lưu" (`/cai-dat/sao-luu`) trong `frontend/src/features/settings/SettingsScreen.tsx`
- [x] T036 [US1] Chấm cảnh báo trên biểu tượng Cài đặt trong `frontend/src/app/IconRail.tsx` khi `stale` hoặc `destination.state != "ok"` (chú thích khi rê chuột: "Sao lưu cần chú ý"); thêm test vào `frontend/tests/backupSettings.test.tsx`
- [x] T037 [US1] Cập nhật `mac-agent/scripts/install.sh` (cài bản agent mới, nhắc cấp quyền Tệp và thư mục / Thông báo) và README mục "Dữ liệu nằm ở đâu, sao lưu" trong `README.md`: sao lưu tự động 21:00, vị trí mặc định, đổi thư mục, quyền macOS cần cấp, log ở `~/Library/Logs/LichHocAgent/agent.log`; giữ `scripts/backup.sh`/`restore.sh` cho dùng thủ công
- [x] T038 [US1] Thêm tham số `backup-stale` cho `scripts/validate.sh` / `backend/scripts_validate.py`: lùi `backup_status.last_success_at` (và `enabled_since`) 4 ngày để chạy kịch bản quickstart B5 ngay trong đợt 1

**Checkpoint**: quickstart B1–B5, B10 pass; `./scripts/test.sh` pass.

---

## Phase 4: User Story 2 — Khôi phục từ bản sao lưu (Priority: P1) · Đợt 1

**Goal**: Chọn bản trong danh sách (hoặc file bất kỳ) → xác nhận → tự sao lưu "Trước khi khôi phục" → khôi phục
trọn vẹn → đồng bộ lại Lịch/Lời nhắc.

**Independent Test**: quickstart B6–B9 — xoá hẳn một task, khôi phục bản trước đó, task trở lại, có bản "Trước
khi khôi phục", cấu hình sao lưu không đổi.

### Tests cho User Story 2 ⚠️

- [x] T039 [P] [US2] Test tích hợp `POST /api/backup/restore` trong `backend/tests/integration/test_restore_api.py` (dùng test DB): tạo dữ liệu → dump → sửa/xoá dữ liệu → restore → dữ liệu khớp 100% `counts` và nội dung task/danh sách/nhãn/môn/buổi/buổi thi/settings (SC-002), với dữ liệu một học kỳ (6 môn × 15 buổi, 300 task) khôi phục xong dưới 60 giây; `backup_config` và `backup_jobs` giữ giá trị trước khi restore; `sync_state.revision` sau restore > cả hai giá trị trước; file sửa vài byte → 400 `backup_corrupt`, dữ liệu giữ nguyên; manifest `schema_revision` không có trong `migrations/versions` → 409 `backup_too_new`, dữ liệu giữ nguyên; dump lỗi giữa chừng (giả lập) → 500 `restore_failed`, dữ liệu giữ nguyên
- [x] T040 [P] [US2] Test bản cũ hơn trong `backend/tests/integration/test_restore_upgrade.py`: dump tạo ở revision `0005_exams` (downgrade test DB, dump, upgrade lại) → restore → `schema_upgraded=true`, bảng mới có đủ, dữ liệu cũ còn; giả lập `flask db upgrade` lỗi → 500 `upgrade_failed`, chế độ bảo trì vẫn bật cho tới khi lần restore kế tiếp (bản "Trước khi khôi phục") xong
- [x] T041 [P] [US2] Test chế độ bảo trì trong `backend/tests/integration/test_maintenance.py`: khi cờ khôi phục bật, `GET /api/tasks` → 503 `{"error":{"code":"restoring","message":"Đang khôi phục dữ liệu…"}}`; `GET /api/backup/status` và `GET /api/health` vẫn 200; cờ được tắt cả khi restore lỗi
- [x] T042 [P] [US2] Test `run_restore` với backend giả trong `mac-agent/tests/test_restore_run.py`: thứ tự bước `pre_backup` → `uploading` → `restoring` → `resync` → `done` (message "Đã khôi phục dữ liệu về <giờ> <ngày>"); pre_backup thất bại → `failed` "Không tạo được bản sao lưu dữ liệu hiện tại nên chưa khôi phục." và KHÔNG gọi `/backup/restore`; SHA-256 trong manifest sai → `failed` "Bản sao lưu bị hỏng, không thể khôi phục"; file chỉ có trên iCloud → bước `downloading` trước (hàm tải được giả lập), quá 5 phút → `failed`; khôi phục bản cũ nhất khi đang có đủ 14 bản → file nguồn không bị `prune` xoá trước khi gửi (gọi `run_backup(..., protect=source_path)`), dọn lại sau khi xong; backend trả `upgrade_failed` → agent gửi lại bản `truoc-khoi-phuc` vừa tạo và job `failed` "Không nâng cấp được dữ liệu của bản sao lưu cũ; dữ liệu đã được đưa về như trước khi khôi phục."; lời gọi `/sync/*` và `/backup/agent-report` trả 503 `restoring` trong lúc khôi phục không làm job lỗi
- [x] T043 [P] [US2] Test Vitest `frontend/tests/restoreFlow.test.tsx`: bấm "Khôi phục" mở hộp xác nhận với đúng câu "Khôi phục dữ liệu về lúc 21:00 Thứ Tư, 04/11/2026? Dữ liệu hiện tại sẽ được sao lưu trước rồi bị thay thế." và nút "Khôi phục"/"Huỷ"; Huỷ không tạo job; xác nhận tạo job `restore` với `source_path`; job `running` hiện lớp phủ "Đang khôi phục dữ liệu…" kèm bước; `done` → toast "Đã khôi phục dữ liệu về …" và `queryClient.invalidateQueries()` toàn bộ; API trả 503 `restoring` → giao diện hiện lớp phủ thay vì lỗi

### Implementation cho User Story 2

- [x] T044 [US2] Phần khôi phục của `backend/app/services/backup.py`: `restore_backup(stream)` — lưu file tạm, mở ZIP, đọc manifest, kiểm tra SHA-256 (`backup_corrupt`), kiểm tra `schema_revision` có trong thư mục migrations (`backup_too_new`), đọc giữ `backup_config`/`backup_status`/`backup_jobs`/`agent_status` và `sync_state.revision`, bật cờ `/tmp/lichhoc-restoring`, `db.engine.dispose()`, chạy `pg_restore --clean --if-exists --single-transaction --no-owner --exit-on-error`, nếu revision cũ hơn head thì chạy `flask db upgrade` (subprocess) — lỗi → `BackupError("upgrade_failed")` trả 500, giữ cờ bảo trì để agent khôi phục lại bản "Trước khi khôi phục" (research R8) — ghi lại các bảng đã giữ, đặt `sync_state.revision = max(cũ, mới) + 1`, tắt cờ trong `finally`; log từng bước
- [x] T045 [US2] `backend/app/api/maintenance.py`: `before_app_request` trả 503 `restoring` khi có cờ `/tmp/lichhoc-restoring`, trừ `GET /api/health`, `GET /api/backup/status`, `PUT /api/backup/jobs/<id>`, `PUT /api/backup/agent-report`, `POST /api/backup/restore`; đăng ký trong `backend/app/__init__.py`; thêm `POST /backup/restore` (stream thân `application/zip`, giới hạn 500 MB) vào `backend/app/api/backup.py`
- [x] T046 [P] [US2] Thêm `location /api/backup/` trong `frontend/nginx.conf` (trước `location /api/`): `client_max_body_size 500m`, `proxy_read_timeout 600s`, `proxy_send_timeout 600s`, `proxy_request_buffering off`, `proxy_buffering off` — để agent gửi bản khôi phục và tải bản sao lưu qua cổng 8080 không bị chặn 21 MB / 120 giây; thêm ca upload 30 MB vào `scripts/persistence_check.py`
- [x] T047 [P] [US2] Module `mac-agent/lichhoc_agent/icloud.py`: `is_cloud_only(path)` (nhận dạng `.Tên.icloud`), `ensure_downloaded(path, timeout=300)` gọi `NSFileManager.defaultManager().startDownloadingUbiquitousItemAtURL_error_` rồi chờ file thật xuất hiện (kiểm tra mỗi 2 giây), quá hạn → `TimeoutError`
- [x] T048 [US2] `run_restore(job, backend, store, state)` trong `mac-agent/lichhoc_agent/backup.py` theo `contracts/agent-backup.md` (bước `pre_backup` gọi `run_backup("truoc-khoi-phuc", protect=source_path)` và chỉ dọn bản thừa sau khi khôi phục xong; `upgrade_failed` → gửi lại bản "Trước khi khôi phục"; bỏ qua 503 `restoring` của `/sync/*` và `/backup/agent-report`; mỗi bước log INFO/ERROR vào `~/Library/Logs/LichHocAgent/agent.log` (FR-010a); cập nhật `job.step` trước mỗi bước, `backend.upload_restore(path)` stream file, sau cùng `sync_once(force=True)`); thêm `upload_restore` vào `mac-agent/lichhoc_agent/backend_client.py` (timeout 10 phút); gọi từ `backup_tick` khi `job.kind == "restore"`
- [x] T049 [P] [US2] Hộp xác nhận + "Chọn bản sao lưu khác…" trong `frontend/src/features/settings/RestoreDialog.tsx` (dùng `ConfirmDialog` hiện có; nút "Chọn bản sao lưu khác…" gọi `pickBackupFile()` — app chỉ đọc đúng file người dùng chọn, theo constitution 2.3.1 ngoại lệ 2, ngoài Tauri dùng ô nhập đường dẫn); nối nút "Khôi phục" ở `BackupSettings.tsx`
- [x] T050 [US2] Lớp phủ toàn app `frontend/src/features/settings/RestoreOverlay.tsx` gắn trong `frontend/src/app/AppShell.tsx` (hiện khi job `restore` đang chạy hoặc khi API trả 503 `restoring`; chữ bước: "Đang sao lưu dữ liệu hiện tại…", "Đang tải bản sao lưu từ iCloud…", "Đang khôi phục dữ liệu…", "Đang cập nhật Lịch và Lời nhắc…"); xử lý 503 `restoring` trong `frontend/src/api/client.ts`; khi xong toast + invalidate toàn bộ truy vấn
- [x] T051 [US2] Thêm vòng sao lưu → xoá dữ liệu → khôi phục → so sánh `counts` vào `scripts/test-persistence.sh` / `scripts/persistence_check.py` (gọi `GET /api/backup/dump` và `POST /api/backup/restore` trực tiếp, không cần agent)

**Checkpoint**: Đợt 1 xong — quickstart B1–B10 pass; `./scripts/test.sh` và `./scripts/test-persistence.sh` pass; commit "feat(003): đợt 1 — sao lưu tự động và khôi phục".

---

## Phase 5: User Story 4 — Thêm nhanh bằng câu tiếng Việt (Priority: P2) · Đợt 2

**Goal**: Ô "Thêm công việc" hiểu ngày giờ, nhãn, danh sách, Quan trọng, ưu tiên; tô sáng và xem trước khi gõ;
bấm để huỷ hiểu. Cụm lặp được viết và test đầy đủ nhưng giao diện chạy với `recurrence: false` đến Phase 7.

**Independent Test**: quickstart N1–N7 — bộ ≥ 400 ca pass; gõ các câu mẫu thấy tô sáng/xem trước đúng; Enter tạo
task đúng tiêu đề và trường.

### Tests cho User Story 4 ⚠️

- [x] T052 [P] [US4] Test `foldVi` trong `frontend/tests/foldVi.test.ts`: đủ 134 chữ có dấu tiếng Việt (hoa + thường, a ă â e ê i o ô ơ u ư y × 5 dấu + không dấu) và `đ/Đ` → chữ không dấu thường; bảng ánh xạ vị trí đúng với chuỗi NFC và NFD; xuất danh sách cặp (gốc → gập) ra `frontend/tests/fixtures/vi-fold-pairs.json` để Phase 6 đối chiếu với `vn_fold`
- [x] T053 [P] [US4] Bộ ca `frontend/src/features/tasks/quickParse/quickParse.cases.ts` (≥ 400 ca, `now = 2026-11-05T10:00+07:00` Thứ Năm, mặc định đang xem "Tất cả") chia nhóm theo research R12 và `contracts/quick-add-grammar.md`: (a) toàn bộ 18 dòng bảng FR-030 và 15 kịch bản US4; (b) hôm nay/hnay/mai/ngày mai/mốt/ngày mốt/ngày kia; (c) thứ 2…thứ 7, thứ hai…thứ bảy, T2…T7, CN, chủ nhật — kể cả "thứ 5" hôm nay khi giờ chưa qua/đã qua; (d) tuần sau, thứ X tuần sau/tuần tới; (e) D/M, DD/MM, DD/MM/YYYY (chỉ dấu `/`; "20-11" giữ là chữ), ngày đã qua → năm sau, 31/2 và 32/11 không hiểu; (f) giờ 9h, 9h30, 9g, 9:30, 21:00, 9 giờ, 9 giờ 30, 9 rưỡi; (g) buổi sáng/trưa/chiều/tối/đêm đứng riêng và ghép, "tối nay"; (h) giờ 1–5 không buổi → chiều, "5h sáng", 0h, 12h; (i) ghép giờ với `viewDefaultDate` (Hôm nay, Ngày mai, 7 ngày tới) kể cả giờ đã qua; (j) #nhãn có/không dấu, nhiều nhãn, nhãn mới; ~danh sách có/không, không khớp → giữ chữ; (k) `*` và "quan trọng"; (l) !cao/!tb/!thấp/!thap, "!" và "!gấp" giữ chữ; (m) gõ không dấu và HOA; (n) ranh giới từ: "maintain", "Lab 3", "Lab 3-4" và "Bài 1-2" (không phải ngày — chỉ dấu `/`), "Tháng 9h", "CN" trong từ; "Gọi chị Mai"; (n2) "tuần tới", "9 rưỡi", "9h rưỡi", "9 giờ 30 phút", "9g30", "đêm" đứng riêng (22:00), "11h đêm" (23:00), "12h đêm" (00:00 hôm sau), "2h đêm" (02:00), "1h trưa" (13:00), "12h sáng" giữ là chữ; (o) nhiều cụm cùng loại → chỉ cụm đầu; (p) huỷ hiểu theo khoá `kind:start:text` và khoá mất hiệu lực khi chữ đổi; (q) tiêu đề rỗng → `titleMissing`; (r) cụm lặp (hằng/hàng/mỗi ngày, mỗi N ngày, hằng tuần, thứ 2 và thứ 5 hàng tuần, mỗi thứ 2, hằng tháng, ngày 5 hằng tháng) với `recurrence: true`, và cùng câu với `recurrence: false` thì giữ là chữ
- [x] T054 [P] [US4] Test chạy bộ ca `frontend/tests/quickParse.test.ts` (mỗi ca một `it`, so `title`, các khoảng tô sáng, `fields`, `dueInPast`, `titleMissing`) + test bất biến: tiêu đề không bao giờ chứa khoảng đã hiểu; parse chuỗi 300 ký tự < 2 ms (trung bình 50 lần)
- [x] T055 [P] [US4] Test tích hợp `tag_names` trong `backend/tests/integration/test_tasks_api.py`: `POST /tasks` với `tag_names: ["gap"]` khi đã có nhãn "Gấp" → gắn nhãn có sẵn, không tạo mới; `["ThóiQuenMới"]` → tạo nhãn màu mặc định cùng transaction; lỗi validate task → nhãn mới không được tạo
- [x] T056 [P] [US4] Test Vitest `frontend/tests/quickAdd.test.tsx`: gõ "Nộp bài QTDA thứ 6 9h #Gấp" → 3 vùng `mark`, xem trước "Hạn: 09:00 Thứ Sáu, 06/11 · Nhãn: Gấp", Enter gửi `title="Nộp bài QTDA"`, `due_date="2026-11-06"`, `due_time="09:00"`, `tag_ids=[id Gấp]`; bấm vào "Mai" trong "Gọi chị Mai" → hết tô sáng, Enter gửi tiêu đề nguyên câu; gõ "~" mở gợi ý, ↓ + Enter chọn danh sách (không tạo task); Esc đóng gợi ý giữ chữ; đang `compositionstart` thì không parse lại; tiêu đề rỗng → "Thiếu tên công việc", Enter không gửi; ở "Ngày mai" gõ "Họp nhóm 9h" → hạn ngày mai 09:00

### Implementation cho User Story 4

- [x] T057 [P] [US4] `frontend/src/lib/foldVi.ts`: `foldVi(s) -> {folded, map}` (NFD, bỏ dấu kết hợp, `đ→d`, `Đ→D`, chữ thường; `map[i]` = vị trí trong chuỗi gốc) và `foldKey(s)` (chỉ chuỗi gập) — T052
- [x] T058 [P] [US4] `frontend/src/features/tasks/quickParse/lexicon.ts`: bảng mẫu có thứ tự (dài trước ngắn) cho mọi loại trong `contracts/quick-add-grammar.md` (ngày, thứ, tuần sau, DD/MM, giờ, buổi, nhãn, danh sách, Quan trọng, ưu tiên, lặp), viết trên chuỗi đã gập, có ranh giới từ theo FR-029
- [x] T059 [US4] `frontend/src/features/tasks/quickParse/tokenize.ts`: quét chuỗi gập theo lexicon, trả `QuickToken[]` (vị trí theo chuỗi gốc qua `map`), mỗi loại chỉ cụm đầu (nhãn nhận tất cả), đánh dấu `dismissed` theo `ctx.dismissed`; tắt nhận cụm lặp khi `ctx.recurrence = false`; khớp `#`/`~` với `ctx.tags`/`ctx.lists` bằng `foldKey`
- [x] T060 [US4] `frontend/src/features/tasks/quickParse/resolve.ts`: từ token → `fields` theo mục "Bảng giờ" và "Giải nghĩa hạn" của `contracts/quick-add-grammar.md` (giờ 1–5 không buổi +12; buổi đứng riêng sáng 08:00/trưa 12:00/chiều 14:00/tối 20:00/đêm 22:00; chỉ giờ → `viewDefaultDate` nếu có, nếu không hôm nay/ngày mai; thứ X hôm nay mà giờ đã qua → tuần sau; DD/MM không năm đã qua → năm sau; lặp không ngày → ngày khớp gần nhất); tính `dueInPast`
- [x] T061 [US4] `frontend/src/features/tasks/quickParse/title.ts` + `index.ts`: `buildTitle(text, tokens)` (bỏ khoảng đã hiểu không bị huỷ, gộp khoảng trắng, bỏ `, . ; : - –` ở hai đầu) và `parseQuickAdd(text, ctx)` ghép tokenize → resolve → title; chạy T053/T054 pass
- [x] T062 [US4] Backend `tag_names`: thêm `tag_names: list[str] = []` vào schema tạo task trong `backend/app/schemas/tasks.py`; trong `backend/app/services/tasks.py` so khớp tên nhãn bằng khoá gập dấu + `casefold` (thêm `fold_key` vào `backend/app/lib/text.py`), tạo nhãn mới qua `backend/app/services/tags.py` trong cùng transaction — T055
- [x] T063 [US4] Lớp tô sáng + xem trước trong `frontend/src/features/tasks/QuickAdd.tsx` (tách component `QuickAddHighlight.tsx` và `QuickAddPreview.tsx` cùng thư mục): `<input>` thật chữ trong suốt + lớp gương có `<mark>` (research R13); xem trước dạng chip theo `contracts/ui.md` ("Hạn: …", "Danh sách: …", "Nhãn: …"/"Nhãn mới: …", "★ Quan trọng", "Ưu tiên: …", hạn đã qua màu đỏ "đã qua", "Thiếu tên công việc"); click trong vùng tô sáng → thêm khoá vào `dismissed`; tooltip "Bấm để giữ làm chữ"; không parse lại khi đang soạn bằng bộ gõ; `ctx.recurrence = false`
- [x] T064 [US4] Gợi ý `#`/`~` trong `frontend/src/features/tasks/QuickAddSuggest.tsx` (Radix popover có sẵn): lọc theo `foldKey`, hiện chấm màu nhãn / emoji danh sách, ↑/↓, Enter/Tab chọn (chèn tên đầy đủ, kể cả có khoảng trắng), Esc đóng; khi gợi ý mở Enter không tạo task
- [x] T065 [US4] Nối `parseQuickAdd` với `frontend/src/features/tasks/quickAddDefaults.ts`: `viewDefaultDate` lấy từ mặc định của danh sách đang xem; giá trị hiểu được thắng mặc định, nhãn hiểu được cộng thêm nhãn mặc định (FR-033); gửi `tag_names` cho nhãn mới qua `frontend/src/api/tasks.ts`; cập nhật `frontend/tests/quickAddDefaults*.test.ts` nếu có
- [x] T066 [US4] Chữ nhóm `quickAdd` trong `frontend/src/i18n/vi.ts` (định dạng "Thứ Sáu, 06/11" qua `frontend/src/lib/dates.ts`) và mục gợi ý cú pháp trong bảng phím tắt ⌘/ (`frontend/src/app/ShortcutsDialog.tsx`): ví dụ "mai 9h #nhãn ~danh sách * !cao"

**Checkpoint**: Đợt 2 xong — quickstart N1–N7 pass; `./scripts/test.sh` pass; commit "feat(003): đợt 2 — thêm nhanh bằng câu tiếng Việt".

---

## Phase 6: User Story 5 — Tìm kiếm (Priority: P3) · Đợt 3

**Goal**: ⌘F hoặc ô tìm ở cột danh sách; tìm không dấu/hoa thường trong task, danh sách, nhãn, môn học, buổi
học, buổi thi; nhóm kết quả, tô sáng, "Gồm cả đã hoàn thành", bấm mở chi tiết hoặc lọc.

**Independent Test**: quickstart S1–S5.

### Tests cho User Story 5 ⚠️

- [x] T067 [P] [US5] Test đối chiếu `vn_fold` trong `backend/tests/integration/test_vn_fold.py`: đọc `frontend/tests/fixtures/vi-fold-pairs.json` (T052), mọi cặp `SELECT vn_fold(gốc)` = chuỗi gập của frontend
- [x] T068 [P] [US5] Test tích hợp `GET /api/search` trong `backend/tests/integration/test_search_api.py`: "nop bai"/"NỘP BÀI"/"Nop Bai" tìm được "Nộp bài QTDA"; "do an" tìm được "Đồ án"; "email thay" khớp ghi chú, có `snippet` ~80 ký tự; nhiều từ ("nop qtda") phải chứa đủ; task ở Thùng rác không bao giờ có; task đã xong chỉ có khi `include_done=1`; nhóm `lists`/`tags` có `open_count`; môn khớp theo `name`/`class_code`/`lecturer`; buổi học khớp theo tên môn/`class_code`/`room`; buổi thi khớp theo `course_name`/`course_code`/`room`; buổi học sắp tới trước rồi buổi đã qua (gần nhất trước); thứ tự Công việc theo hạn gần nhất, không hạn ở cuối; `limit` 20 + `total`; `group=tasks&limit=200`; `q` rỗng/chỉ khoảng trắng → mọi nhóm rỗng
- [x] T069 [P] [US5] Test hiệu năng trong `backend/tests/integration/test_search_perf.py` (đánh dấu `slow`, chạy trong `./scripts/test.sh`): seed 1.000 task + 6 môn × 15 buổi, 20 truy vấn khác nhau mỗi truy vấn < 300 ms
- [x] T070 [P] [US5] Test Vitest `frontend/tests/search.test.tsx`: ⌘F ở trang Lịch → về Công việc, focus ô tìm; gõ → sau debounce gọi `/search`; nhóm theo thứ tự Công việc, Danh sách, Nhãn, Môn học, Buổi học, Buổi thi, nhóm trống không hiện; `highlight("Nộp bài QTDA", "nop bai")` tô đúng "Nộp bài"; "Xem thêm (n)"; công tắc "Gồm cả đã hoàn thành"; không kết quả → "Không tìm thấy kết quả cho “…”"; Esc xoá và quay lại màn hình trước; ↑/↓ + ↩ mở kết quả; bấm nhãn → điều hướng tới danh sách task của nhãn; hoàn thành một task từ bảng chi tiết khi đang xem kết quả → kết quả cập nhật

### Implementation cho User Story 5

- [x] T071 [US5] Migration `backend/migrations/versions/0007_search.py`: `CREATE EXTENSION IF NOT EXISTS unaccent`; `CREATE FUNCTION vn_fold(text) RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$ SELECT lower(public.unaccent('public.unaccent', coalesce($1, ''))) $$`; downgrade xoá hàm (giữ extension) — T067
- [x] T072 [US5] Service `backend/app/services/search.py`: chuẩn hoá `q` (NFC, cắt, tách từ, gập bằng `fold_key`), một truy vấn cho mỗi nhóm với `vn_fold(<các trường ghép>) LIKE '%' || :từ || '%'` cho từng từ (escape `%`/`_`), trường tìm đúng bảng ở `data-model.md` §3 (môn: `name`, `class_code`, `lecturer`; buổi học: tên môn, `class_code`, `room`; buổi thi: `course_name`, `course_code`, `room` — không có cột ghi chú), loại trừ và thứ tự theo FR-040, `snippet` khi khớp ghi chú, `total` + `limit`/`group`
- [x] T073 [US5] Blueprint `backend/app/api/search.py` (đăng ký trong `backend/app/__init__.py`) + schema phản hồi theo `contracts/rest-api.md` mục Tìm kiếm — T068, T069
- [x] T074 [P] [US5] `frontend/src/api/search.ts` (`useSearch(q, includeDone)` debounce 120 ms, giữ dữ liệu cũ khi đang tải; khoá truy vấn `search` được invalidate sau mọi mutation task/danh sách/nhãn/môn/buổi học/buổi thi trong `frontend/src/api/*.ts` để kết quả tự cập nhật — edge case) và `frontend/src/features/search/highlight.ts` (`highlightRanges(text, query)` dùng `foldVi` + `map`, nhiều từ)
- [x] T075 [US5] `frontend/src/features/search/SearchBox.tsx` ở đầu `frontend/src/features/tasks/ListColumn.tsx` (biểu tượng kính lúp, chữ gợi ý "Tìm kiếm"); gõ → điều hướng `/cong-viec/tim-kiem?q=…`; Esc xoá và quay lại đường dẫn trước khi tìm; thêm ⌘F vào `frontend/src/app/shortcutsTable.ts` và `frontend/src/app/useHotkeys.ts` (⌘F hoạt động cả khi đang trong ô nhập)
- [x] T076 [US5] `frontend/src/features/search/SearchResults.tsx` cho đường dẫn `cong-viec/tim-kiem` (thêm vào `frontend/src/features/tasks/viewRoutes.ts`): các nhóm theo `contracts/ui.md`, mục task dùng lại `TaskRow` (mờ + dấu đã xong khi đã hoàn thành), đoạn trích ghi chú, chữ khớp tô sáng, "Xem thêm (n)", công tắc "Gồm cả đã hoàn thành" (lưu trên URL `done=1`), chọn bằng ↑/↓ + ↩
- [x] T077 [US5] Điều hướng khi bấm kết quả (FR-042) trong `frontend/src/features/search/openResult.ts`: task → mở `TaskDetailPanel` giữ trang kết quả; danh sách → `/cong-viec/danh-sach/<id>`; nhãn → `/cong-viec/nhan/<id>` (đã đối chiếu `buildTaskPath`/`parseTaskPath` trong `viewRoutes.ts` — dùng hàm đó, không ghép chuỗi tay); môn học → `/mon-hoc` chọn môn; buổi học → `SessionDetail`; buổi thi → chi tiết buổi thi ở `/lich-thi`
- [x] T078 [US5] Chữ nhóm `search` trong `frontend/src/i18n/vi.ts`; thêm tham số `search-perf` (gọi T069 với dữ liệu seed) cho `scripts/validate.sh` / `backend/scripts_validate.py`

**Checkpoint**: Đợt 3 xong — quickstart S1–S5 pass; `./scripts/test.sh` pass; commit "feat(003): đợt 3 — tìm kiếm không dấu".

---

## Phase 7: User Story 3 — Task lặp lại (Priority: P2) · Đợt 4

**Goal**: Quy tắc lặp (hằng ngày, mỗi N ngày, hằng tuần nhiều thứ, hằng tháng; kết thúc không/vào ngày/sau N
lần); hoàn thành → lần kế tiếp; hỏi phạm vi khi sửa/xoá; đúng trên danh sách thông minh, lịch, bản tóm tắt, nhắc,
Lời nhắc/iPhone; bật cụm lặp trong thêm nhanh.

**Independent Test**: quickstart R1–R7.

### Tests cho User Story 3 ⚠️

- [ ] T079 [P] [US3] Test hàm thuần `backend/tests/unit/test_task_recurrence.py`: `occurrences(rule, start, end)` cho 4 kiểu; hằng tháng ngày 31 → 30/11, 31/12, 31/1, 28/2 (2027), 29/2 (2028); `next_due` sau hạn lần vừa xong và không sớm hơn hôm nay (quá hạn 3 ngày → 05/11 nếu giờ chưa qua, 06/11 nếu đã qua; không sinh lần đã lỡ); kết thúc `on_date` (lần kế tiếp sau ngày kết thúc → None) và `after_count` (đủ N → None); `shift_rule`: hằng ngày/mỗi N ngày đếm lại từ ngày mới, hằng tuần T2+T5 dời lần T2 sang T3 → T3+T5, dời sang T5 (đã có) → chỉ T5, hằng tháng đổi ngày D; tính đúng trong 12 tháng liên tiếp (SC-007)
- [ ] T080 [P] [US3] Test tích hợp `backend/tests/integration/test_task_series_api.py`: tạo task có `recurrence` → `task_series` + task `occurrence_no=1`; task không hạn đặt lặp → hạn = ngày khớp gần nhất; hoàn thành → `next_task` giữ tiêu đề, ghi chú, danh sách, nhãn, ưu tiên, Quan trọng, nhắc, khung giờ làm dời theo ngày mới (US3-1); bỏ hoàn thành → `removed_next_task_id`, lần kế tiếp đã sửa thì giữ cả hai (FR-019); hoàn thành hai lần liên tiếp nhanh → không trùng lần hiện tại (unique index); PATCH thiếu `scope` → 409 `scope_required`; `scope=this` chỉ đổi lần này, lần sau theo mẫu cũ; `scope=following` đổi mẫu; đổi `due_date` với `following` → quy tắc dời (FR-020a); PATCH chỉ `recurrence` không cần scope và lần hiện tại giữ nguyên hạn, lần dự kiến tính lại theo quy tắc mới; `recurrence=null` → task thường; DELETE `scope=this` → lần hiện tại vào Thùng rác + lần mới; `scope=following` → `stopped_at`; khôi phục `this` → `series_id` NULL; khôi phục `following` → chuỗi tiếp tục; task tự tạo đặt `recurrence` → 400; weekly `weekdays=[]` → 400 "Chọn ít nhất một thứ"
- [ ] T081 [P] [US3] Test hồi quy hiển thị trong `backend/tests/integration/test_task_series_views.py`: danh sách thông minh, đếm và `/search` chỉ có lần hiện tại; `/calendar` có `projected_task` cho các ngày sau lần hiện tại trong khoảng xem, không trùng ngày lần hiện tại, dừng khi chuỗi kết thúc, ≤ 400 mục; digest của các ngày tới có lần dự kiến; feed Lời nhắc (`/sync/feed`) chỉ có lần hiện tại và đổi sang lần kế tiếp sau khi hoàn thành (revision tăng)
- [ ] T082 [P] [US3] Test Vitest `frontend/tests/recurrence.test.tsx`: `describeRule` → "Lặp hằng tuần vào Thứ Hai, Thứ Năm · đến 30/11/2026", "Lặp mỗi 3 ngày", "Lặp hằng tháng vào ngày 31 · 3 lần"; RecurrenceEditor không cho lưu hằng tuần không chọn thứ; ScopeDialog hiện "Chỉ lần này"/"Lần này và các lần sau"/"Huỷ" khi API trả 409 `scope_required` rồi gửi lại với `scope`; TaskRow có biểu tượng ↻ + tooltip; `toCalendarEvents` vẽ `projected_task` mờ, không kéo được, bấm mở lần hiện tại

### Implementation cho User Story 3

- [ ] T083 [P] [US3] Hàm thuần `backend/app/services/task_recurrence.py`: dataclass `Rule` (từ `RecurrenceRule` của data-model §4), `occurrences`, `next_due`, `first_due_on_or_after`, `shift_rule`, `is_finished`, `clamp_month_day` — T079
- [ ] T084 [US3] Migration `backend/migrations/versions/0008_recurring_tasks.py` + model `backend/app/models/task_series.py`: `freq` CHECK `daily`|`every_n_days`|`weekly`|`monthly`; `interval_days` "bắt buộc khi `every_n_days`, `2..365`"; `weekdays smallint[]` "bắt buộc, không rỗng khi `weekly`; giá trị `1..7`"; `month_day` "bắt buộc khi `monthly`, `1..31`"; `anchor_date`; `end_kind` CHECK `never`|`on_date`|`after_count`; `end_date` "bắt buộc khi `on_date`"; `end_count` "bắt buộc khi `after_count`, `1..999`"; `occurrences_created`; `template` jsonb; `stopped_at`; `tasks` thêm `series_id` (FK ON DELETE SET NULL), `occurrence_no`, `spawned_from_task_id` (FK ON DELETE SET NULL), `trash_scope` CHECK `this`|`following`; unique index một phần `(series_id) WHERE series_id IS NOT NULL AND completed_at IS NULL AND deleted_at IS NULL`; CHECK `series_id IS NULL OR is_auto = false`; cập nhật `backend/app/models/task.py`
- [ ] T085 [US3] Service `backend/app/services/task_series.py`: `attach_rule(task, rule)` (tạo chuỗi + mẫu từ task, đặt hạn nếu chưa có), `on_complete(task, now) -> next_task | None` (tạo từ mẫu, `spawned_from_task_id`, `user_modified=false`, tăng `occurrences_created`, `bump_revision`), `on_uncomplete(task)` (gỡ lần kế tiếp chưa sửa), `apply_edit(task, changes, scope)` (`this`: chỉ task + `user_modified=true`; `following`: task + mẫu, đổi ngày → `shift_rule`), `on_delete(task, scope)`, `on_restore(task)`, `change_rule(series, rule|None)`
- [ ] T086 [US3] Nối vào `backend/app/services/tasks.py` và `backend/app/api/tasks.py`: `recurrence` khi tạo/sửa; `scope` cho PATCH/DELETE (409 `scope_required`); `complete` trả `next_task`, `uncomplete` trả `removed_next_task_id`; serializer task thêm `series_id`, `recurrence`, `occurrence_no`, `series_finished`; schema trong `backend/app/schemas/tasks.py` (validate theo data-model §4, lỗi tiếng Việt)
- [ ] T087 [US3] Lần dự kiến: `projected_occurrences(start, end)` trong `backend/app/services/task_series.py`; thêm mục `projected_task` vào `backend/app/services/calendar.py` và gộp vào bản tóm tắt từng ngày trong `backend/app/services/digest.py` (kiểm tra `sync_feed` dùng digest mới) — T081
- [ ] T088 [P] [US3] `frontend/src/features/tasks/recurrence/describeRule.ts` + kiểu `RecurrenceRule` trong `frontend/src/api/types.ts`; `frontend/src/api/tasks.ts` thêm `recurrence`, `scope`, xử lý 409 `scope_required` (ném lỗi có kiểu để UI hỏi)
- [ ] T089 [US3] `frontend/src/features/tasks/recurrence/RecurrenceEditor.tsx` (popover: Không lặp / Hằng ngày / Mỗi N ngày / Hằng tuần với 7 nút T2…CN / Hằng tháng ngày D; kết thúc Không kết thúc / Vào ngày (`DateInput`) / Sau N lần) gắn vào hàng "Lặp lại" của `frontend/src/features/tasks/TaskDetailPanel.tsx`; ẩn với task tự tạo; hiện "Đã kết thúc lặp" khi `series_finished`
- [ ] T090 [US3] `frontend/src/features/tasks/recurrence/ScopeDialog.tsx` + hook `useScopedTaskMutation` trong `frontend/src/features/tasks/useTaskActions.ts`: mọi sửa/xoá/kéo thả task lặp hỏi phạm vi ("Sửa task lặp lại"/"Xoá task lặp lại"; "Chỉ lần này", "Lần này và các lần sau", "Huỷ"); Hoàn tác hoạt động với cả hai phạm vi; hoàn thành → task mới xuất hiện ngay (cập nhật cache lạc quan)
- [ ] T091 [US3] Biểu tượng ↻ cạnh giờ hạn + tooltip `describeRule` trong `frontend/src/features/tasks/TaskRow.tsx`; khối `projected_task` (mờ 50%, viền nét đứt, ↻, không kéo được, bấm mở lần hiện tại) trong `frontend/src/features/calendar/toCalendarEvents.ts` và `CalendarBlock.tsx`; kéo lần hiện tại dùng ScopeDialog trong `frontend/src/features/calendar/dropToPatch.ts`
- [ ] T092 [US4] Bật cụm lặp trong thêm nhanh: `ctx.recurrence = true` trong `frontend/src/features/tasks/QuickAdd.tsx`, chip xem trước "Lặp: …" dùng `describeRule`, gửi `recurrence` khi tạo; thêm US4-7, US4-8 vào `frontend/tests/quickAdd.test.tsx`
- [ ] T093 [US3] Chữ nhóm `recurrence` trong `frontend/src/i18n/vi.ts`; thêm ca "sao lưu → xoá chuỗi → khôi phục còn đủ chuỗi và quy tắc" vào `backend/tests/integration/test_restore_api.py` (quickstart R7)

**Checkpoint**: Đợt 4 xong — quickstart R1–R7 pass; `./scripts/test.sh` pass; commit "feat(003): đợt 4 — task lặp lại".

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T094 [P] Cập nhật `README.md`: thêm nhanh bằng câu (bảng cú pháp ngắn), tìm kiếm ⌘F, task lặp; bảng phím tắt thêm ⌘F; cập nhật `specs/002-redesign-macos-app/contracts/ui-shortcuts.md` hoặc trỏ sang `specs/003-backup-nl-recurring-search/contracts/ui.md`
- [ ] T095 [P] Kiểm tra tương phản ≥ 4.5:1 ở chế độ sáng/tối cho màu tô sáng thêm nhanh, tô sáng tìm kiếm, khối dự kiến và thẻ cảnh báo sao lưu bằng `frontend/src/lib/contrast.ts` (thêm ca vào test tương phản hiện có)
- [ ] T096 [P] Rà constitution IV: chạy app khi tắt mạng, xác nhận không có kết nối ra ngoài máy (`lsof -i` cho backend, agent, app) ngoài localhost; ghi kết quả vào `specs/003-backup-nl-recurring-search/quickstart.md` (SC-010)
- [ ] T097 Chạy toàn bộ quickstart B1–B10, N1–N7, S1–S5, R1–R7 và kịch bản kiểm chứng của feature 001, 002 (SC-009); ghi kết quả vào `specs/003-backup-nl-recurring-search/validation.md`
- [ ] T098 `./scripts/test.sh` và `./scripts/test-persistence.sh` pass lần cuối; đánh dấu Status "Done" trong `specs/003-backup-nl-recurring-search/spec.md`; commit

---

## Dependencies & Execution Order

### Phase

- **Setup (1)** → **Foundational (2)** → **US1 (3)** → **US2 (4)** → **US4 (5)** → **US5 (6)** → **US3 (7)** → **Polish (8)**.
- Thứ tự theo đợt người dùng chỉ định; về kỹ thuật:
  - US2 cần US1 (bản sao lưu, agent, bảng `backup_jobs`, trang Cài đặt).
  - US4 độc lập với đợt 1 (chỉ cần Setup T004); `foldVi` (T057) được US5 dùng lại.
  - US5 cần T052/T057 (`foldVi` + file cặp ký tự).
  - US3 độc lập với US4/US5, trừ T092 (cần T063) và T093 (cần T039).

### Trong mỗi story

- Test trước, phải FAIL → model/migration → service → API → agent/Tauri → giao diện.
- T019 trước T020–T022; T026 trước T028; T044 trước T045; T057 trước T059; T059 → T060 → T061 → T063;
  T071 trước T072; T083 trước T085; T084 trước T085 → T086 → T087.

### Song song

- **Setup**: T002, T003, T004 song song (T001 riêng vì build image lâu).
- **US1 tests**: T008–T018 song song (khác file, khác thành phần).
- **US1 impl**: sau T019–T023 (backend), các nhánh agent (T024–T027), Tauri (T029–T031), frontend (T032–T034) chạy song song; T035–T036 sau T032–T034.
- **US2**: T039–T043 song song; T046 (nginx), T047 và T049 song song với T044–T045.
- **US4**: T052–T056 song song; T057, T058 song song; T062 song song với chuỗi T059–T061.
- **US5**: T067–T070 song song; T074 song song với T071–T073.
- **US3**: T079–T082 song song; T083 và T088 song song với T084.

## Parallel Example: User Story 1

```text
# Viết test cùng lúc (khác file):
T008 mac-agent/tests/test_backup_schedule.py
T009 mac-agent/tests/test_backup_files.py
T013 backend/tests/integration/test_backup_api.py
T016 frontend/tests/backupSettings.test.tsx
T018 desktop/src-tauri/src/backup_cmds.rs (test)

# Sau khi backend xong (T019–T023), ba nhánh song song:
agent:    T024 → T025 → T026 → T027 → T028
tauri:    T029, T030, T031
frontend: T032, T033, T034 → T035 → T036
```

## Parallel Example: User Story 4

```text
T052 frontend/tests/foldVi.test.ts
T053 frontend/src/features/tasks/quickParse/quickParse.cases.ts
T055 backend/tests/integration/test_tasks_api.py (tag_names)
→ T057 foldVi.ts ‖ T058 lexicon.ts ‖ T062 backend tag_names
→ T059 → T060 → T061 → T063 → T064 → T065 → T066
```

## Implementation Strategy

### MVP (Đợt 1: US1 + US2)

1. Phase 1 Setup, Phase 2 spike + agent hai luồng.
2. Phase 3 (US1) → **dừng, kiểm chứng B1–B5, B10** → có sao lưu tự động hằng ngày (yêu cầu ưu tiên cao nhất).
3. Phase 4 (US2) → kiểm chứng B6–B9 → commit đợt 1. Đây là MVP: dữ liệu được bảo vệ và khôi phục được.

### Giao dần

- Đợt 2 (US4) → kiểm chứng N1–N7 → commit.
- Đợt 3 (US5) → kiểm chứng S1–S5 → commit.
- Đợt 4 (US3 + bật cụm lặp của US4) → kiểm chứng R1–R7 → commit.
- Polish → kiểm chứng toàn bộ, hồi quy 001/002.

Mỗi đợt để app ở trạng thái dùng được hằng ngày; không đợt nào phá chức năng hiện có (FR-044).
