# Contract: REST API (frontend ↔ backend)

**Base URL**: `http://127.0.0.1:8080/api`. nginx của service `web` chuyển tiếp sang backend; cổng
chỉ mở trên localhost. Không có xác thực, vì đây là ứng dụng một người dùng chỉ truy cập được từ
chính máy (constitution IV).

## Quy ước chung

- JSON UTF-8. Ngày `YYYY-MM-DD`, giờ `HH:MM`, thời điểm ISO 8601 có offset `+07:00`.
- Mã màu là mã trong bảng màu (`c01`…`c12`). Ánh xạ sang mã hex nằm ở frontend.
- **Lỗi** có dạng:

  ```json
  {"error": {"code": "validation_error", "message": "<tiếng Việt>", "fields": {"end_time": "Giờ kết thúc phải sau giờ bắt đầu"}}}
  ```

  | HTTP | code | Khi nào |
  |------|------|---------|
  | 400 | `validation_error` | dữ liệu sai; `fields` chỉ ra trường lỗi (FR-010) |
  | 404 | `not_found` | không tìm thấy |
  | 409 | `conflict` | cần người dùng xác nhận thêm; `details` mô tả (xem từng endpoint) |
  | 413 | `image_too_large` | ảnh > 20 MB |
  | 415 | `unsupported_image` | không phải PNG/JPEG/HEIC |

- **Cảnh báo không chặn** (ví dụ trùng giờ, FR-015) trả trong trường `warnings: [{code, message}]`
  của phản hồi thành công.
- Xoá dùng `DELETE`. Việc xác nhận nằm ở giao diện (FR-027). Riêng các xoá có ảnh hưởng dây chuyền
  thì yêu cầu tham số xác nhận rõ ràng, nêu ở từng endpoint.

---

## Hôm nay và lịch

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/today` | `{date, exams[], sessions[], tasks_due_today[], overdue_tasks[], notices[]}`. `notices` gồm cảnh báo quyền thông báo hoặc trạng thái agent (FR-019, FR-057) |
| GET | `/calendar?from=YYYY-MM-DD&to=YYYY-MM-DD&tags=1,2` | `{sessions[], tasks[], exams[]}` trong khoảng ngày, lọc theo nhãn nếu có (FR-016, FR-017, FR-045, FR-057) |

**Session (đọc)**:

```json
{"id": 123, "subject_id": 7, "subject_name": "Giải tích", "date": "2026-11-16",
 "start_at": "2026-11-16T07:30:00+07:00", "end_at": "2026-11-16T09:30:00+07:00",
 "room": "A101", "is_cancelled": false, "time_overridden": false, "room_overridden": false,
 "color": "c03", "tags": [{"id": 1, "name": "E-Learning", "color": "c05"}],
 "display_color": "c05", "shift_label": "Ca 1", "auto_task_id": 45,
 "is_important": false, "important_override": null, "subject_is_important": false}
```

`is_important` là mức quan trọng hiệu lực (FR-067, FR-070); task và buổi thi trong `/today`,
`/calendar` cũng có `is_important` để giao diện tô nổi bật.

`display_color` = màu của nhãn hiệu lực đầu tiên, nếu không có nhãn thì màu môn (FR-044).
`tags` là nhãn hiệu lực (nhãn môn rồi nhãn riêng); `own_tag_ids` là nhãn riêng của buổi, dùng khi sửa.

---

## Task và danh sách

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/lists` | danh sách và số task chưa xong |
| POST | `/lists` | `{name, color}` |
| PATCH | `/lists/{id}` | đổi tên hoặc màu |
| DELETE | `/lists/{id}?move_to={id}` hoặc `?delete_tasks=true` | không có tham số mà danh sách còn task thì trả `409 {details: {task_count}}` |
| GET | `/tasks?list_id=&tags=&include_completed=false` | sắp xếp theo `due_at` (task không hạn ở cuối), rồi `priority` (FR-005) |
| POST | `/tasks` | `{title, notes?, due_date?, due_time?, priority?, list_id, tag_ids?, reminder_minutes?, is_important?}` |
| PATCH | `/tasks/{id}` | sửa một phần; với task tự tạo, sửa trường nào khác `completed` thì đặt `user_modified = true` |
| POST | `/tasks/{id}/complete` · `/tasks/{id}/uncomplete` | FR-003 |
| DELETE | `/tasks/{id}` | task tự tạo bị xoá thì đánh dấu buổi học để không tạo lại |

**Task (đọc)** thêm các trường: `due_at`, `is_overdue`, `is_auto`, `source_session_id`,
`user_modified`, `tags[]`, `display_color`, `reminder_at`.

---

## Học kỳ, ca, môn học, buổi học

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/semesters` | kèm `is_current` |
| POST | `/semesters` | `{name, start_date, end_date}`; chồng lấn thì `400` có `fields.start_date` nêu học kỳ bị chồng (FR-036) |
| PATCH | `/semesters/{id}?clamp_subjects=true` | không có `clamp_subjects` mà làm môn ra ngoài khoảng thì `409 {details: {subjects: [...]}}` |
| DELETE | `/semesters/{id}?confirm=true` | không có `confirm` thì `409 {details: {subject_count}}` (FR-037) |
| GET | `/shifts` | theo `position` |
| POST · PATCH | `/shifts`, `/shifts/{id}?confirm=true` | đổi giờ ca đang được dùng mà thiếu `confirm` thì `409 {details: {subject_count}}` (FR-040) |
| DELETE | `/shifts/{id}?confirm=true` | môn liên quan chuyển sang giờ tuỳ chỉnh |
| GET | `/subjects?semester_id=` | |
| POST | `/subjects` | xem payload bên dưới; trả `{subject, session_count, warnings}` |
| POST | `/subjects/bulk` | `{semester_id, start_date, end_date, rows: [SubjectInput…]}`; lỗi theo dòng: `fields: {"rows[2].end_time": "..."}` (FR-009, FR-010) |
| PATCH | `/subjects/{id}` | sinh lại buổi học, giữ ngoại lệ (FR-013) |
| DELETE | `/subjects/{id}` | kèm buổi học (FR-014) |
| GET | `/sessions/{id}` | một buổi học (dùng cho "Xem buổi học" từ task tự tạo, FR-050) |
| PATCH | `/sessions/{id}` | `{start_time?, end_time?, room?, tag_ids?, important_override?}`, chỉ áp dụng cho buổi này (FR-012); `important_override: null` = theo môn (FR-067) |
| POST | `/sessions/{id}/cancel` · `/sessions/{id}/restore` | FR-011 |

**SubjectInput**:

```json
{"name": "Giải tích", "semester_id": 3, "class_code": "MAT101_02", "lecturer": "TS. An",
 "room": "A101", "weekdays": [1, 4],
 "shift": {"start_shift_id": 1, "end_shift_id": 1},
 "start_time": null, "end_time": null,
 "start_date": "2026-09-07", "end_date": "2026-12-20",
 "tag_ids": [], "reminder_minutes": null, "is_important": false}
```

Chỉ được có một trong hai: `shift` hoặc cặp `start_time`/`end_time` (giờ tuỳ chỉnh).

> **Feature 004**: lịch của môn nay là danh sách `schedules` (mỗi quy tắc có `weekdays`, `start_date`,
> `end_date`, `shift` hoặc giờ, `room`) và môn có thêm `course_code`, `credits`. Dạng phẳng ở trên vẫn được
> nhận như một quy tắc duy nhất. Xem [contract 004](../../004-pdf-semester-import/contracts/rest-api.md).

---

## Nhãn

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/tags` | kèm `system_key` |
| POST | `/tags` | `{name, color}`; trùng tên (không phân biệt hoa thường) thì `400` |
| PATCH | `/tags/{id}` | nhãn hệ thống chỉ đổi được `color` |
| DELETE | `/tags/{id}` | nhãn hệ thống trả `400` |
| PUT | `/subjects/{id}/tags` · `/sessions/{id}/tags` · `/tasks/{id}/tags` | `{tag_ids: [...]}`, thứ tự trong mảng là thứ tự gắn |

---

## Lịch thi (FR-055 đến FR-058, FR-063)

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/exams?from=&to=&include_past=false` | sắp theo `start_at` |
| POST | `/exams` | `{course_name, course_code?, attempt?, date, start_time, end_time, exam_format?, room?, candidate_number?, tag_ids?, reminder_offsets?, is_important? (mặc định true)}`; trả `{exam, warnings}` (cảnh báo `time_conflict`, FR-058) |
| PATCH | `/exams/{id}` | sửa một phần; trả `{exam, warnings}` |
| DELETE | `/exams/{id}` | `204` |
| PUT | `/exams/{id}/tags` | `{tag_ids}`; nhãn "Thi" luôn được giữ ở vị trí đầu |

**Exam (đọc)**:

```json
{"id": 7, "course_code": "CSE2301", "course_name": "Cơ sở dữ liệu", "attempt": 1,
 "date": "2027-01-05", "start_at": "2027-01-05T07:30:00+07:00", "end_at": "2027-01-05T08:30:00+07:00",
 "exam_format": "Trắc nghiệm trên máy 60p", "room": "A5-310", "candidate_number": "125",
 "is_past": false, "tags": [{"id": 2, "name": "Thi", "color": "c07", "system_key": "exam"}],
 "display_color": "c07", "reminder_offsets": null,
 "conflicts": [{"kind": "session", "id": 88, "title": "Giải tích 1", "start_at": "…"}]}
```

---

## Nhập ảnh (FR-028 đến FR-035, FR-041, FR-046, FR-059 đến FR-062)

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/imports/recognize?kind=` | `multipart/form-data` với trường `image`. `kind` (tuỳ chọn: `week_schedule` hoặc `exam_table`) ép loại ảnh khi lần nhận diện trước trả `"unknown"` (FR-059). Đồng bộ, có thể mất tới ~60 giây. Trả `ImportPreview` ([data-model](../data-model.md#thực-thể-tạm-thời-không-lưu-importpreview-fr-028-đến-fr-035)). Ảnh không được lưu |
| POST | `/imports/commit` | Lịch học: `{kind: "week_schedule", rows: [ImportRow đã chỉnh, selected=true]}`; trả `{created_subjects, created_sessions, skipped_duplicates, warnings}`. Lịch thi: `{kind: "exam_table", exam_rows: [...]}`; trả `{created_exams, skipped_duplicates, warnings}` |
| POST | `/imports/timetable-pdf/preview`, `/imports/timetable-pdf/commit` | Nhập học kỳ từ PDF thời khoá biểu chính thức (feature 004): xem [contract 004](../../004-pdf-semester-import/contracts/rest-api.md) |

- `recognize` không ghi gì vào database. Với lịch thi, phản hồi **không** chứa họ tên hay mã số sinh
  viên (FR-061).
- `commit` chạy trong một transaction duy nhất: dòng nào có lỗi thì cả lần lưu bị huỷ, trả `400`
  với `fields: {"rows[i].field": "..."}` để giao diện chỉ đúng dòng lỗi.

---

## Cài đặt, nhắc dự phòng và trạng thái đồng bộ

| Method | Path | Mô tả |
|--------|------|-------|
| GET · PATCH | `/settings` | các trường trong bảng `settings` |
| GET | `/reminders/upcoming?hours=24` | `[{sync_key, kind: "session"\|"task"\|"exam"\|"digest", title, body, fire_at, important}]`. Mục có nhiều mốc (buổi thi, mục quan trọng) có một phần tử cho mỗi mốc (`sync_key` dạng `exam:7:1440`, `task:45:180`, `session:123:15`); bản tóm tắt có `sync_key = "digest:YYYY-MM-DD"`, `body` = các dòng chi tiết. Chỉ dùng cho nhắc bằng trình duyệt; trả `[]` khi `calendar_sync_enabled = true` (FR-021, FR-066) |
| GET | `/digest?date=YYYY-MM-DD` | Xem trước bản tóm tắt của một ngày (mặc định hôm nay): `{date, fire_at, title, lines[], is_important}` hoặc `{date, empty: true}` khi ngày trống (FR-065). Dùng ở Cài đặt và để kiểm thử |
| GET | `/sync/status` | `agent_status` cộng `{revision, sync_enabled}`, để giao diện hiện cảnh báo |
