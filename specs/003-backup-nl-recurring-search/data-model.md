# Data Model — Feature 003

Mở rộng mô hình của feature 001/002. Ba migration, mỗi migration thuộc một đợt:
`0006_backup` (đợt 1), `0007_search` (đợt 3), `0008_recurring_tasks` (đợt 4). Đợt 2 không đổi CSDL.

---

## 1. Sao lưu (đợt 1)

### `backup_config` — bảng một dòng (`CHECK id = 1`), KHÔNG đi theo bản sao lưu (research R9)

| Cột | Kiểu | Mặc định | Ràng buộc / ghi chú |
|-----|------|----------|---------------------|
| `id` | smallint PK | 1 | |
| `enabled` | boolean | `true` | FR-009 công tắc |
| `schedule_time` | time | `21:00` | FR-001 |
| `destination_path` | text NULL | NULL | NULL = thư mục mặc định trong iCloud Drive (agent tự suy ra); khác NULL = đường dẫn tuyệt đối người dùng chọn |
| `retention_count` | smallint | 14 | `BETWEEN 1 AND 365` (FR-006) |
| `enabled_since` | timestamptz | `now()` | mốc tính "quá 3 ngày" khi chưa có bản nào (FR-008) |
| `updated_at` | timestamptz | | |

Sửa cấu hình → `bump_revision` để agent nhận ngay.

### `backup_status` — bảng một dòng, KHÔNG đi theo bản sao lưu; do agent ghi qua `PUT /backup/agent-report`

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `destination_resolved` | text NULL | đường dẫn thật agent đang dùng |
| `destination_state` | text | `ok` \| `missing` \| `no_permission` \| `icloud_off` \| `not_writable` |
| `destination_message` | text NULL | câu tiếng Việt cho người dùng |
| `last_attempt_at` | timestamptz NULL | |
| `last_attempt_ok` | boolean NULL | |
| `last_attempt_error` | text NULL | lý do + cách khắc phục (FR-009) |
| `last_attempt_size` | bigint NULL | byte |
| `last_success_at` | timestamptz NULL | |
| `last_success_size` | bigint NULL | |
| `files` | jsonb | danh sách `BackupFile` (dưới) mới nhất trước |
| `reported_at` | timestamptz NULL | agent coi là "không chạy" nếu > 2 phút (dùng chung quy tắc của `agent_status`) |

**Suy ra** (không lưu): `stale = enabled && now − (last_success_at ?? enabled_since) > 3 ngày` (FR-008, chấm
cảnh báo trên biểu tượng Cài đặt).

### `BackupFile` (phần tử của `backup_status.files`, cũng là nội dung file — research R3)

| Trường | Kiểu | Ghi chú |
|--------|------|---------|
| `name` | string | `LichHoc-2026-11-05-2100-tu-dong.lhbackup` |
| `path` | string | đường dẫn tuyệt đối trên Mac |
| `kind` | enum | `tu-dong` (Tự động) \| `thu-cong` (Thủ công) \| `truoc-khoi-phuc` (Trước khi khôi phục) |
| `created_at` | ISO datetime | từ manifest; nếu file chỉ có trên iCloud thì từ tên file |
| `size` | int | byte |
| `location` | enum | `local` \| `icloud` (chưa tải về máy) |

Chỉ file khớp mẫu tên của app mới được liệt kê, tính vào giới hạn và bị xoá (FR-006, edge case "file lạ").

### `backup_jobs` — việc giao cho agent, KHÔNG đi theo bản sao lưu

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `id` | bigint PK | |
| `kind` | text | `backup_now` \| `restore` |
| `source_path` | text NULL | file cần khôi phục (bắt buộc với `restore`) |
| `state` | text | `pending` → `running` → `done` \| `failed` (CHECK) |
| `step` | text NULL | với restore: `pre_backup` → `downloading` → `uploading` → `restoring` → `resync` |
| `message` | text NULL | kết quả / lỗi tiếng Việt |
| `created_at`, `started_at`, `finished_at` | timestamptz | |

Ràng buộc: tối đa một việc `pending`/`running` cùng lúc (unique index một phần trên hằng `true` WHERE
`state IN ('pending','running')`) → không chạy hai lần sao lưu chồng nhau (FR-010). Việc `running` quá 30 phút
không có báo cáo → backend đánh `failed` ("Trình sao lưu không phản hồi").

**Chuyển trạng thái**

```
pending ──claim──▶ running ──▶ done
                     │
                     └──────▶ failed
```

### Trạng thái cục bộ của agent (`state.json`, mở rộng)

| Khoá | Ý nghĩa |
|------|---------|
| `backup_last_attempt_at`, `backup_last_success_at` | để `backup_due` chạy được cả khi backend vừa khôi phục |
| `stale_notified_for` | mốc `last_success_at` (hoặc `enabled_since`) đã gửi thông báo 3 ngày (R10) |

---

## 2. Thêm nhanh (đợt 2) — không đổi CSDL

`POST /api/tasks` nhận thêm `tag_names` (R14). Kết quả hiểu câu chỉ tồn tại ở frontend:

```ts
type QuickToken = {
  kind: 'date' | 'time' | 'daypart' | 'recurrence' | 'tag' | 'list' | 'important' | 'priority';
  start: number; end: number;        // vị trí trong chuỗi gốc (UTF-16)
  text: string;                      // chữ gốc
  value: unknown;                    // ví dụ { weekday: 5, nextWeek: true }, { tagId } | { newTagName }
  dismissed: boolean;
};
type QuickParse = {
  title: string;
  tokens: QuickToken[];
  fields: {
    due_date?: string; due_time?: string;      // 'YYYY-MM-DD', 'HH:MM'
    list_id?: number; tag_ids: number[]; tag_names: string[];
    is_important?: boolean; priority?: 1 | 2 | 3;
    recurrence?: RecurrenceRule;               // chỉ khi ctx.recurrence = true (đợt 4)
  };
  dueInPast: boolean; titleMissing: boolean;
};
```

---

## 3. Tìm kiếm (đợt 3)

- Extension `unaccent`; hàm `vn_fold(text) RETURNS text IMMUTABLE PARALLEL SAFE`
  = `lower(public.unaccent('public.unaccent', coalesce($1, '')))` (R15).
- Không bảng mới, không index mới.

Trường được tìm (FR-037):

| Loại | Trường | Loại trừ |
|------|--------|----------|
| Task | `title`, `notes` | `deleted_at IS NOT NULL`; `completed_at IS NOT NULL` trừ khi `include_done` |
| Danh sách | `name` | |
| Nhãn | `name` | |
| Môn học | `subjects.name`, `subjects.class_code`, `subjects.lecturer` | |
| Buổi học | `subjects.name`, `subjects.class_code` của môn, `class_sessions.room` | buổi của học kỳ đã xoá |
| Buổi thi | `exams.course_name`, `exams.course_code`, `exams.room` | |

(Đã đối chiếu với model hiện có: `class_sessions` và `exams` không có cột ghi chú.)

---

## 4. Task lặp lại (đợt 4)

### `task_series` (mới)

| Cột | Kiểu | Ràng buộc / ghi chú |
|-----|------|---------------------|
| `id` | bigint PK | |
| `freq` | text | `daily` \| `every_n_days` \| `weekly` \| `monthly` |
| `interval_days` | smallint NULL | bắt buộc khi `every_n_days`, `2..365` |
| `weekdays` | smallint[] NULL | bắt buộc, không rỗng khi `weekly`; giá trị `1..7` (1 = Thứ Hai) |
| `month_day` | smallint NULL | bắt buộc khi `monthly`, `1..31` (tháng thiếu ngày → cuối tháng, FR-018) |
| `anchor_date` | date | ngày gốc để đếm `every_n_days` |
| `end_kind` | text | `never` \| `on_date` \| `after_count` |
| `end_date` | date NULL | bắt buộc khi `on_date` |
| `end_count` | smallint NULL | bắt buộc khi `after_count`, `1..999` |
| `occurrences_created` | smallint | số lần đã tạo, tính cả lần đầu |
| `template` | jsonb | `{title, notes, list_id, priority, is_important, reminder_minutes, tag_ids, due_time, work: {start, end, day_offset} \| null}` |
| `stopped_at` | timestamptz NULL | chuỗi dừng vì xoá "Lần này và các lần sau" |
| `created_at`, `updated_at` | | |

CHECK đảm bảo các cột bắt buộc theo `freq`/`end_kind` như bảng trên.

### `tasks` (mở rộng)

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `series_id` | bigint NULL FK → `task_series.id` ON DELETE SET NULL | |
| `occurrence_no` | smallint NULL | lần thứ mấy của chuỗi |
| `spawned_from_task_id` | bigint NULL (không có FK) | lần vừa hoàn thành đã sinh ra task này (FR-019). Không có khoá ngoại tự tham chiếu vì nó làm `pg_restore --clean` của bản sao lưu cũ báo lỗi (constraint phụ thuộc `tasks_pkey`); id task không bao giờ được dùng lại nên không sợ trỏ nhầm |
| `trash_scope` | text NULL | `this` \| `following`; chỉ khi task lặp ở Thùng rác |

- `user_modified` (đã có) được đặt `true` khi người dùng sửa một lần được sinh tự động (nghĩa mở rộng, R16).
- Unique index một phần: `UNIQUE (series_id) WHERE series_id IS NOT NULL AND completed_at IS NULL AND
  deleted_at IS NULL` → đúng một lần hiện tại mỗi chuỗi.
- CHECK: `series_id IS NULL OR is_auto = false` (task tự tạo không lặp, FR-025).
- Task lặp phải có `due_date` (khi đặt lặp mà chưa có hạn → hạn = ngày khớp quy tắc gần nhất từ hôm nay).

### Vòng đời một chuỗi

```
            đặt lặp
task thường ───────▶ lần hiện tại #1 ──hoàn thành──▶ đã xong #1 + lần hiện tại #2 ── … ──▶ lần cuối xong (hết chuỗi)
                         │   ▲
      xoá "Chỉ lần này"  │   │ bỏ hoàn thành (lần kế tiếp chưa sửa → bị gỡ)
                         ▼
          #k vào Thùng rác (trash_scope=this) + lần hiện tại #k+1
      xoá "Lần này và các lần sau"
          #k vào Thùng rác (trash_scope=following), task_series.stopped_at = now
      khôi phục: this → task thường (series_id = NULL); following → stopped_at = NULL, #k lại là lần hiện tại
```

### `RecurrenceRule` (API và frontend)

```ts
type RecurrenceRule = {
  freq: 'daily' | 'every_n_days' | 'weekly' | 'monthly';
  interval_days?: number; weekdays?: number[]; month_day?: number;
  end: { kind: 'never' } | { kind: 'on_date'; date: string } | { kind: 'after_count'; count: number };
};
```

### Lần dự kiến (suy ra, không lưu)

`{series_id, current_task_id, date, time, title, color}` cho mỗi ngày khớp quy tắc trong khoảng xem, sau lần
hiện tại, trước khi chuỗi kết thúc; dùng ở lịch (FR-022) và bản tóm tắt (FR-023).
