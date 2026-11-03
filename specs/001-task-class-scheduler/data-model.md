# Data Model: Lịch Học Cá Nhân

**Feature**: `001-task-class-scheduler` | **Date**: 2026-11-04 | **Plan**: [plan.md](plan.md)

Cơ sở dữ liệu là PostgreSQL 16. Mọi bảng có `id bigserial` làm khoá chính, cùng `created_at` và
`updated_at` (`timestamptz`, mặc định `now()`); hai cột này không liệt kê lại trong từng bảng. Văn
bản dùng `text` UTF-8 và được chuẩn hoá Unicode NFC trước khi lưu. Múi giờ là `Asia/Ho_Chi_Minh`
([research R10](research.md#r10-thời-gian-múi-giờ-định-dạng-tiếng-việt)).

## Sơ đồ quan hệ

```text
semesters 1──* subjects 1──* class_sessions 0..1──0..1 tasks (auto)
                  │  └─ start_shift / end_shift ──> shifts
                  │
subject_tags *──* tags *──* session_tags (class_sessions)
                    └────*── task_tags *──* tasks *──1 task_lists

settings (1 dòng)        sync_state (1 dòng)        agent_status (1 dòng)
```

---

## semesters — Học kỳ (FR-036, FR-037)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | text | bắt buộc, 1–100 ký tự |
| start_date | date | bắt buộc |
| end_date | date | bắt buộc, `end_date >= start_date` |

- Các học kỳ không được chồng lấn ngày: ràng buộc `EXCLUDE USING gist (daterange(start_date,
  end_date, '[]') WITH &&)` (cần extension `btree_gist`).
- **Học kỳ hiện tại** là học kỳ chứa ngày hôm nay; nếu không có thì là học kỳ có `start_date`
  nhỏ nhất nhưng lớn hơn hôm nay. Giá trị này được tính khi truy vấn, không lưu.
- Xoá học kỳ thì xoá luôn (`ON DELETE CASCADE`) các môn học, buổi học và task tự tạo chưa sửa (qua
  hàm reconcile, xem R9).
- Sửa ngày làm môn học nằm ngoài khoảng mới: API trả `409` kèm danh sách môn bị ảnh hưởng. Client
  gửi lại với `clamp_subjects=true` để thu hẹp ngày của các môn đó.

## shifts — Ca học (FR-038 đến FR-040)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | text | bắt buộc, duy nhất |
| start_time | time | bắt buộc |
| end_time | time | bắt buộc, `end_time > start_time` |
| position | smallint | thứ tự hiển thị, duy nhất |

- Dữ liệu mặc định khi migrate lần đầu:

| name | start_time | end_time |
|------|-----------|----------|
| Ca 1 | 06:45 | 09:25 |
| Ca 2 | 09:35 | 12:10 |
| Ca 3 | 13:00 | 15:40 |
| Ca 4 | 15:45 | 18:25 |

- Đổi giờ ca: cập nhật `subjects.start_time` và `end_time` của các môn dùng ca đó, rồi gọi
  `regenerate_sessions` cho từng môn. Các buổi có `time_overridden = true` giữ nguyên.
- Xoá ca đang được dùng: các môn liên quan đặt `start_shift_id` và `end_shift_id` về `NULL`,
  giữ nguyên `start_time`/`end_time`, tức chuyển thành "Giờ tuỳ chỉnh".

## subjects — Môn học (FR-007 đến FR-015, FR-039, FR-043)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| semester_id | bigint FK → semesters | bắt buộc, `ON DELETE CASCADE` |
| name | text | bắt buộc, 1–200 ký tự |
| class_code | text | tuỳ chọn |
| lecturer | text | tuỳ chọn |
| room | text | tuỳ chọn |
| color | text | mã trong bảng màu (`c01`…`c12`), tự gán vòng tròn khi tạo |
| weekdays | smallint[] | 1 = Thứ Hai … 7 = Chủ Nhật; ≥ 1 phần tử, không trùng |
| start_shift_id | bigint FK → shifts | `NULL` nếu giờ tuỳ chỉnh, `ON DELETE SET NULL` |
| end_shift_id | bigint FK → shifts | `NULL` hoặc cùng/sau ca bắt đầu (theo `position`) |
| start_time | time | bắt buộc; bằng giờ bắt đầu của ca đầu nếu chọn ca |
| end_time | time | bắt buộc, `> start_time`; bằng giờ kết thúc của ca cuối nếu chọn ca |
| start_date | date | bắt buộc, nằm trong học kỳ |
| end_date | date | bắt buộc, `>= start_date`, nằm trong học kỳ |
| reminder_minutes | integer | `NULL` = theo cài đặt mặc định; `-1` = tắt nhắc; ≥ 0 |

- `start_shift_id` và `end_shift_id` cùng `NULL` hoặc cùng có giá trị.
- `start_date = end_date` nghĩa là môn chỉ học một lần (dùng khi nhập "chỉ một lần" từ ảnh).
- Cảnh báo trùng giờ (FR-015) là kết quả tính khi lưu, không phải ràng buộc. API trả kèm trường
  `warnings`.

## class_sessions — Buổi học (FR-008, FR-011 đến FR-013, FR-017)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| subject_id | bigint FK → subjects | bắt buộc, `ON DELETE CASCADE` |
| date | date | bắt buộc; duy nhất theo `(subject_id, date, start_at)` |
| start_at | timestamptz | bắt buộc |
| end_at | timestamptz | bắt buộc, `> start_at` |
| room | text | tuỳ chọn |
| is_cancelled | boolean | mặc định `false` |
| time_overridden | boolean | `true` nếu người dùng sửa giờ riêng buổi này |
| room_overridden | boolean | `true` nếu người dùng sửa phòng riêng buổi này |
| auto_task_suppressed | boolean | `true` khi người dùng đã xoá task tự tạo của buổi này |

**Trạng thái**:

```text
            sửa giờ/phòng                 huỷ
 [Thường] ───────────────> [Đã sửa riêng] ─────> [Đã huỷ]
    │  ^                                          │
    │  └──────────────── khôi phục ───────────────┘
    └─────────────── huỷ ───────────────────────> [Đã huỷ]
```

- Buổi ở trạng thái "Đã huỷ" hoặc "Đã sửa riêng" được coi là có ngoại lệ, và được giữ lại khi môn
  học thay đổi (FR-013).
- Khôi phục buổi đã huỷ chỉ đặt `is_cancelled = false`; giờ và phòng đã sửa riêng giữ nguyên.
- **Nhãn hiệu lực** của buổi học = nhãn của môn ∪ nhãn riêng của buổi.

## task_lists — Danh sách (FR-004)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | text | bắt buộc, duy nhất (không phân biệt hoa thường) |
| color | text | mã bảng màu |
| is_default_study | boolean | đúng một dòng `true`: danh sách "Học tập", nơi chứa task tự tạo |

- Dữ liệu mặc định: "Học tập" (`is_default_study = true`), "Cá nhân", "Công việc".
- Xoá danh sách có task: API trả `409`; client gửi lại với `move_to=<list_id>` hoặc
  `delete_tasks=true`. Không cho xoá danh sách có `is_default_study = true` khi chưa chọn danh sách
  khác thay thế.

## tasks — Công việc (FR-001 đến FR-006, FR-047 đến FR-050)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| list_id | bigint FK → task_lists | bắt buộc |
| title | text | bắt buộc, 1–300 ký tự sau khi bỏ khoảng trắng hai đầu |
| notes | text | tuỳ chọn |
| due_date | date | tuỳ chọn |
| due_time | time | tuỳ chọn; chỉ có khi có `due_date` |
| priority | smallint | 1 = Cao, 2 = Trung bình (mặc định), 3 = Thấp |
| completed_at | timestamptz | `NULL` = chưa hoàn thành |
| reminder_minutes | integer | `NULL` = mặc định; `-1` = tắt; ≥ 0 (chỉ dùng khi có `due_time`) |
| source_session_id | bigint FK → class_sessions | có giá trị ⇔ task tự tạo; duy nhất; `ON DELETE SET NULL` |
| is_auto | boolean | `true` nếu do quy tắc tạo ra |
| user_modified | boolean | `true` sau khi người dùng sửa bất kỳ trường nào ngoài `completed_at` |

**Giá trị suy ra**:
- `due_at` = `due_date + (due_time ?? 23:59)`, dùng để xét quá hạn và sắp xếp (FR-005).
- **Thời điểm nhắc**:
  - Task có `due_time`: `due_at − (reminder_minutes ?? settings.task_reminder_minutes)`.
  - Task chỉ có `due_date`: `due_date + settings.date_only_task_reminder_time` (mặc định 08:00).
- **Quá hạn** = chưa hoàn thành và `due_at < now()`.

**Vòng đời task tự tạo**:
- Xoá task có `is_auto = true` thì đặt `class_sessions.auto_task_suppressed = true` trước khi xoá
  (FR-049).
- Task có `is_auto = true` và `user_modified = false` mới được reconcile tự cập nhật hoặc xoá.

## tags, subject_tags, session_tags, task_tags — Nhãn (FR-042 đến FR-046)

**tags**:

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| name | text | bắt buộc, duy nhất theo `lower(name)` |
| color | text | mã bảng màu (nhiều nhãn được trùng màu) |
| system_key | text | `'e_learning'` cho nhãn hệ thống, ngược lại `NULL`; duy nhất |

- Nhãn có `system_key` không được đổi tên hay xoá; chỉ đổi màu.

**Bảng nối**: `subject_tags(subject_id, tag_id, position)`, `session_tags(session_id, tag_id,
position)`, `task_tags(task_id, tag_id, position)`.
- Khoá chính ghép `(owner_id, tag_id)`. `position` giữ thứ tự gắn, nên "nhãn gắn đầu tiên" quyết
  định màu hiển thị (FR-044).
- Thứ tự nhãn hiệu lực của buổi học: nhãn của môn trước, rồi nhãn riêng của buổi.
- Xoá nhãn thì `ON DELETE CASCADE` trên các bảng nối, sau đó reconcile task tự tạo (nếu xoá nhãn
  làm môn hết là E-Learning; riêng nhãn hệ thống thì không xoá được).

## settings — Cài đặt (1 dòng, FR-022, FR-048, FR-051)

| Cột | Kiểu | Mặc định |
|-----|------|----------|
| session_reminder_minutes | integer | 15 |
| task_reminder_minutes | integer | 60 |
| date_only_task_reminder_time | time | 08:00 |
| calendar_sync_enabled | boolean | `false` |
| calendar_sync_prompted | boolean | `false`; thành `true` sau khi đã đề nghị bật lần đầu |
| auto_deadline_evening_from | time | 20:00 (buổi bắt đầu `>=` giờ này thì thoả điều kiện) |
| auto_deadline_due_time | time | 08:00 (giờ deadline Chủ Nhật) |
| auto_deadline_excluded_keywords | text[] | `{'Giáo dục thể chất'}` |

Đổi các cột `auto_deadline_*` thì reconcile mọi buổi học có hạn chót chưa qua.

## sync_state và agent_status — Đồng bộ (FR-051 đến FR-054)

**sync_state** (1 dòng):

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| revision | bigint | tăng 1 trong cùng transaction với mọi thay đổi ảnh hưởng tới feed |

**agent_status** (1 dòng, agent ghi):

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| last_seen_at | timestamptz | lần cuối agent liên lạc |
| permission | text | `unknown`, `granted`, `denied` |
| icloud_source | text | `icloud`, `local_only`, `unknown` |
| last_synced_revision | bigint | revision đã đồng bộ xong |
| last_error | text | lỗi gần nhất (tiếng Việt, để hiển thị) |

Giao diện dùng `agent_status` để hiện cảnh báo: agent chưa chạy (`last_seen_at` cũ hơn 2 phút), bị
từ chối quyền, hoặc không có iCloud.

---

## Thực thể tạm thời (không lưu): ImportPreview (FR-028 đến FR-035)

Trả về từ `POST /api/imports/recognize`, chỉ tồn tại trong bộ nhớ của client:

```text
ImportPreview
├─ month_year: {value: "2026-11", source: "grid_dates|week_header|mini_calendar|menu_bar", certain: bool}
└─ rows[]: ImportRow
   ├─ fields: name, class_code, date, weekday, start_time, end_time, room, lecturer
   │    mỗi field = {value, certain: bool, reason?: string}
   ├─ shift: {start_shift_id, end_shift_id} | null   (+ note "không khớp ca nào")
   ├─ suggested_tags: ["e_learning"]?
   ├─ semester_id: id | null   (null ⇒ phải chọn hoặc tạo học kỳ)
   ├─ duplicate_of_session_id: id | null   ("Đã có trong lịch")
   ├─ repeat: {mode: "once"|"weekly", until: date}
   └─ selected: bool   (mặc định false nếu trùng)
```

**Quy tắc khi commit** (`POST /api/imports/commit`):
- Từ chối dòng có trường bắt buộc (`name`, `date`, `start_time`, `end_time`) còn `certain = false`
  (FR-032).
- Kiểm tra trùng lại phía server, kể cả giữa các dòng trong cùng lần nhập (FR-034).
- Mỗi dòng tạo một `subject`:
  - `weekly`: `weekdays = [weekday(date)]`, khoảng ngày từ `date` đến `until`.
  - `once`: `start_date = end_date = date`.
- Các dòng cùng tên, cùng thứ, cùng giờ được gộp thành một môn nếu người dùng chấp nhận gợi ý gộp.

---

## Quy tắc đánh dấu revision

Các thao tác sau tăng `sync_state.revision` trong cùng transaction:
- Thêm, sửa, xoá bảng `class_sessions`, `subjects`, `semesters`, `shifts`, `tasks`.
- Đổi `settings` ảnh hưởng nhắc hoặc đồng bộ.

Cài đặt bằng một hàm `bump_revision(session)` gọi trong lớp service, không dùng trigger, để dễ đọc
và dễ test.
