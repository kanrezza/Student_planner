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
                    ├────*── task_tags *──* tasks *──1 task_lists
                    └────*── exam_tags *──* exams   (buổi thi: độc lập, không thuộc học kỳ/môn)

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
| Ca 2 | 09:30 | 12:10 |
| Ca 3 | 13:00 | 15:40 |
| Ca 4 | 15:45 | 18:25 |

- Đổi giờ ca: cập nhật `subjects.start_time` và `end_time` của các môn dùng ca đó, rồi gọi
  `regenerate_sessions` cho từng môn. Các buổi có `time_overridden = true` giữ nguyên.
- Xoá ca đang được dùng: các môn liên quan đặt `start_shift_id` và `end_shift_id` về `NULL`,
  giữ nguyên `start_time`/`end_time`, tức chuyển thành "Giờ tuỳ chỉnh".

## subjects — Môn học (FR-007 đến FR-015, FR-039, FR-043)

> **Feature 004**: các cột lịch của bảng này (`weekdays`, `start_time`, `end_time`, `start_date`,
> `end_date`, `start_shift_id`, `end_shift_id`, `room`) đã chuyển sang bảng `subject_schedules` (một môn có
> ≥ 1 quy tắc lặp); `subjects` thêm `course_code`, `credits`; `class_sessions` thêm `schedule_id`. Mô tả đầy
> đủ ở [data-model 004](../004-pdf-semester-import/data-model.md). Các mục "Đổi giờ ca" và "Xoá ca" ở trên
> áp dụng cho quy tắc của môn thay vì cột của `subjects`.

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
| is_important | boolean | mặc định `false`; áp dụng cho mọi buổi của môn (FR-067) |

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
| important_override | boolean | `NULL` = theo môn; `true`/`false` = đặt riêng buổi này (FR-067) |

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
- **Quan trọng hiệu lực** của buổi học = `important_override ?? subjects.is_important`.

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
| reminder_minutes | integer | `NULL` = mặc định; `-1` = tắt nhắc (áp dụng cho mọi task, kể cả task chỉ có ngày); ≥ 0 = số phút trước hạn (chỉ có tác dụng khi có `due_time`) |
| source_session_id | bigint FK → class_sessions | có giá trị ⇔ task tự tạo; duy nhất; `ON DELETE SET NULL` |
| is_auto | boolean | `true` nếu do quy tắc tạo ra |
| user_modified | boolean | `true` sau khi người dùng sửa bất kỳ trường nào ngoài `completed_at` |
| is_important | boolean | mặc định `false` (FR-067); đổi trường này cũng đặt `user_modified = true` |

**Giá trị suy ra**:
- `due_at` = `due_date + (due_time ?? 23:59)`, dùng để xét quá hạn và sắp xếp (FR-005).
- **Thời điểm nhắc**:
  - Task có `due_time`: `due_at − (reminder_minutes ?? settings.task_reminder_minutes)`.
  - Task chỉ có `due_date`: `due_date + settings.date_only_task_reminder_time` (mặc định 08:00).
  - `reminder_minutes = -1` thì không nhắc, bất kể task có giờ hay chỉ có ngày.
  - Task quan trọng: nhiều mốc theo [Quy tắc mốc nhắc](#quy-tắc-mốc-nhắc-fr-022-fr-068-fr-069).
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
| system_key | text | `'e_learning'`, `'exam'` cho nhãn hệ thống, ngược lại `NULL`; duy nhất |

- Nhãn có `system_key` không được đổi tên hay xoá; chỉ đổi màu.

**Bảng nối**: `subject_tags(subject_id, tag_id, position)`, `session_tags(session_id, tag_id,
position)`, `task_tags(task_id, tag_id, position)`, `exam_tags(exam_id, tag_id, position)`.
- Nhãn hệ thống "Thi" (`system_key='exam'`, màu mặc định `c07` đỏ) luôn là nhãn gắn đầu tiên của mọi
  buổi thi (`position = 0`); service tự thêm khi tạo và không cho gỡ (FR-056).
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
| auto_deadline_eve_reminder_time | time | 20:00; `NULL` = tắt mốc nhắc tối hôm trước hạn của task tự tạo (FR-071) |
| important_reminder_offsets | integer[] | `{1440, 180, 60, 15}` (mốc của mục quan trọng, 1–6 phần tử ≥ 0, FR-068) |
| exam_extra_reminder_offsets | integer[] | `{10080}` (mốc thêm cho buổi thi quan trọng: 7 ngày, 0–3 phần tử, FR-069) |
| exam_reminder_minutes | integer | 60 (1 mốc cho buổi thi không quan trọng, FR-069) |
| daily_digest_enabled | boolean | `true` (FR-065) |
| daily_digest_time | time | 05:00 |
| daily_digest_overdue_only | boolean | `true` ("Gửi tóm tắt khi chỉ có việc quá hạn", FR-065) |

Đổi các cột `auto_deadline_*` thì reconcile mọi buổi học có hạn chót chưa qua.

## exams — Buổi thi (FR-055 đến FR-058, FR-063, FR-064)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| course_code | text | tuỳ chọn (mã học phần) |
| course_name | text | bắt buộc, 1–200 ký tự |
| attempt | smallint | ≥ 1, mặc định 1 (lần thi) |
| date | date | bắt buộc |
| start_at | timestamptz | bắt buộc (ngày thi + giờ bắt đầu) |
| end_at | timestamptz | bắt buộc, `> start_at` |
| exam_format | text | tuỳ chọn (hình thức thi, ví dụ "Trắc nghiệm trên máy 60p") |
| room | text | tuỳ chọn (có thể trống) |
| candidate_number | text | tuỳ chọn (số báo danh) |
| reminder_offsets | integer[] | `NULL` = theo mặc định (quy tắc mốc nhắc bên dưới); `{}` = tắt nhắc; mỗi phần tử ≥ 0 |
| is_important | boolean | mặc định `true` (FR-067, FR-069) |

- Buổi thi là sự kiện một lần: không liên kết học kỳ, môn học hay quy tắc lặp; không áp dụng tự tạo
  deadline (US10).
- Index `(date)`, `(start_at)`.
- **Trùng giờ** (FR-058), tính khi đọc/lưu, không phải ràng buộc: buổi thi `E` trùng với buổi học `S`
  chưa huỷ, hoặc với buổi thi khác `E'`, khi `start < other.end AND other.start < end`. API trả
  `conflicts: [{kind: "session"|"exam", id, title, start_at}]`.
- **Đã qua** = `end_at < now()`.
- **Trùng khi nhập** (FR-062): cùng (`ci_key(course_code)` nếu cả hai có mã, ngược lại
  `ci_key(course_name)`), cùng `date`, cùng giờ bắt đầu và cùng `attempt`.
- Không có cột nào lưu họ tên hay mã số sinh viên (FR-061).

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

## Quy tắc mốc nhắc (FR-022, FR-068, FR-069)

Hàm thuần trong `services/reminders.py`, trả danh sách **phút trước** (đã bỏ trùng, sắp giảm dần):

| Mục | Thường | Quan trọng |
|-----|--------|------------|
| Buổi học | `[m]` với `m = subject.reminder_minutes ?? settings.session_reminder_minutes` | `important_reminder_offsets ∪ {subject.reminder_minutes nếu ≥ 0}` |
| Task có giờ | `[m]` với `m = task.reminder_minutes ?? settings.task_reminder_minutes` | `important_reminder_offsets ∪ {task.reminder_minutes nếu ≥ 0}` |
| Buổi thi | `[settings.exam_reminder_minutes]` | `important_reminder_offsets ∪ exam_extra_reminder_offsets` |

- `reminder_minutes = -1` (buổi học, task) hoặc `reminder_offsets = {}` (buổi thi) → `[]`, kể cả mục
  quan trọng.
- Buổi thi có `reminder_offsets` khác `NULL` → dùng đúng danh sách đó, bỏ qua bảng trên.
- Task tự tạo (`is_auto`): thêm thời điểm `due_date − 1 ngày` lúc
  `settings.auto_deadline_eve_reminder_time` nếu cột này khác `NULL` và task không tắt nhắc (FR-071);
  thời điểm trùng chỉ tính một lần.
- Task tự tạo chưa bị sửa: `is_important` do reconcile đặt bằng mức quan trọng hiệu lực của buổi
  nguồn (FR-072).
- Task quan trọng **chỉ có ngày**: thời điểm nhắc = `due_date − k ngày` lúc
  `date_only_task_reminder_time`, với `k = 0` và `k = phút // 1440` cho mỗi mốc ≥ 1440; mốc < 1440 bị
  bỏ.
- Thời điểm nhắc đã qua bị bỏ khi tính `upcoming` (nhắc trình duyệt). Trong feed vẫn gửi đủ, vì
  Lịch/Lời nhắc tự không báo mốc đã qua.

## Bản tóm tắt hằng ngày (suy ra, không lưu — FR-065, FR-066)

Hàm thuần `services/digest.py: build_digest(day, exams, sessions, tasks, shifts) -> Digest | None`:

| Trường | Mô tả |
|--------|-------|
| date | ngày của bản tóm tắt |
| fire_at | `date + settings.daily_digest_time` |
| title | một dòng, ví dụ `Hôm nay: Thi CSDL 07:30 A5-310 · Ca 1 Giải tích A101 · Việc: Nộp bài Toán, Đọc chương 3 (quá hạn) +2 việc khác` |
| lines | các dòng chi tiết: buổi thi (giờ, tên học phần, phòng) → buổi học chưa huỷ theo `start_at` (nhãn ca nếu khớp ca, ngược lại `HH:MM`; tên môn; phòng hoặc "chưa có phòng") → mỗi task được chọn một dòng (`<tiêu đề> – hạn HH:MM` hoặc `– cả ngày` cho task đến hạn, `– quá hạn từ dd/mm` cho task quá hạn) → `"+N việc khác"` nếu còn |
| is_important | `true` nếu có buổi thi hoặc mục quan trọng trong ngày (đánh dấu ★ ở đầu tiêu đề) |

- Đến hạn hôm nay = task chưa hoàn thành có `due_date = date`. Quá hạn = task chưa hoàn thành có
  `due_at < date 00:00` (tính theo dữ liệu hiện tại).
- **Chọn task**: task đến hạn hôm nay sắp theo `due_at` (task chỉ có ngày sau task có giờ), rồi task
  quá hạn sắp theo `due_at` tăng dần (quá hạn lâu nhất trước); lấy 3 task đầu, `N` = số còn lại.
- Trả `None` (không gửi) khi không có buổi thi, buổi học, task đến hạn và task quá hạn; khi chỉ có
  task quá hạn mà `daily_digest_overdue_only = false`; hoặc khi `daily_digest_enabled = false`.
- Feed sinh bản tóm tắt cho `today … today + 13` (14 ngày, research R15).
- Chỉ có tối đa 3 tiêu đề task (đã có sẵn trong Lời nhắc); không có ghi chú, số báo danh, hình thức
  thi (FR-052, FR-065).

---

## Thực thể tạm thời (không lưu): ImportPreview (FR-028 đến FR-035, FR-059 đến FR-062)

Trả về từ `POST /api/imports/recognize`, chỉ tồn tại trong bộ nhớ của client. Trường `kind` cho biết
loại ảnh nhận diện được (FR-059):

```text
ImportPreview
├─ kind: "week_schedule" | "exam_table" | "unknown"   ("unknown" ⇒ giao diện hỏi người dùng chọn loại)
├─ month_year: {value: "2026-11", source: "grid_dates|week_header|mini_calendar|menu_bar", certain: bool}
│      (chỉ với kind = "week_schedule")
├─ exam_rows[]: ExamRow   (chỉ với kind = "exam_table")
│  ├─ fields: course_code, course_name, attempt, date, start_time, end_time, exam_format, room,
│  │          candidate_number — mỗi field = {value, certain: bool, reason?: string}
│  ├─ end_time_source: "image" | "format_duration" | null   (giờ kết thúc tính từ "60p" …)
│  ├─ is_past: bool   ("Đã qua" — mặc định bỏ chọn)
│  ├─ duplicate_of_exam_id: id | null   ("Đã có trong lịch" — mặc định bỏ chọn)
│  └─ selected: bool
│  (Không có trường nào chứa họ tên, mã số sinh viên, ngày sinh, lớp — FR-061.)
└─ rows[]: ImportRow   (chỉ với kind = "week_schedule")
   ├─ fields: name, class_code, date, weekday, start_time, end_time, room, lecturer
   │    mỗi field = {value, certain: bool, reason?: string}
   ├─ shift: {start_shift_id, end_shift_id} | null   (+ note "không khớp ca nào")
   ├─ suggested_tags: ["e_learning"]?
   ├─ semester_id: id | null   (null ⇒ phải chọn hoặc tạo học kỳ)
   ├─ duplicate_of_session_id: id | null   ("Đã có trong lịch")
   ├─ repeat: {mode: "once"|"weekly", until: date}
   ├─ merge_group: string | null   (các dòng cùng tên, thứ, giờ có chung giá trị)
   ├─ merge_accepted: bool   (mặc định false; người dùng bấm "Gộp" thì cả nhóm thành true)
   └─ selected: bool   (mặc định false nếu trùng)
```

**Quy tắc khi commit** (`POST /api/imports/commit`):
- Từ chối dòng có trường bắt buộc (`name`, `date`, `start_time`, `end_time`) còn `certain = false`
  (FR-032).
- Kiểm tra trùng lại phía server, kể cả giữa các dòng trong cùng lần nhập (FR-034).
- Mỗi dòng tạo một `subject`:
  - `weekly`: `weekdays = [weekday(date)]`, khoảng ngày từ `date` đến `until`.
  - `once`: `start_date = end_date = date`.
- Các dòng cùng `merge_group` có `merge_accepted = true` tạo **một** môn lặp hàng tuần, bắt đầu từ
  ngày sớm nhất trong nhóm; nếu `merge_accepted = false` thì mỗi dòng là một môn riêng.
- Với `exam_rows`: mỗi dòng được chọn tạo một `exam`; từ chối dòng có `course_name`, `date`,
  `start_time`, `end_time` còn `certain = false`; kiểm tra trùng lại phía server (FR-062).

---

## Quy tắc đánh dấu revision

Các thao tác sau tăng `sync_state.revision` trong cùng transaction:
- Thêm, sửa, xoá bảng `class_sessions`, `subjects`, `semesters`, `shifts`, `tasks`, `exams` (kể cả
  đổi `is_important`, `important_override`).
- Đổi `settings` ảnh hưởng nhắc, bản tóm tắt hoặc đồng bộ.

Bản tóm tắt còn phụ thuộc ngày hiện tại (cửa sổ 14 ngày trượt, số task quá hạn), nên agent tự đồng
bộ lại khi sang ngày mới (contract calendar-sync §4).

Cài đặt bằng một hàm `bump_revision(session)` gọi trong lớp service, không dùng trigger, để dễ đọc
và dễ test.
