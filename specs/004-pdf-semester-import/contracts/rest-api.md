# Contract: REST API — thay đổi của feature 004

Bổ sung cho [contract REST của 001](../../001-task-class-scheduler/contracts/rest-api.md); quy ước chung (base URL
`http://127.0.0.1:8080/api`, dạng lỗi, `warnings`) giữ nguyên. Chỉ liệt kê endpoint mới hoặc đổi.

## Môn học: nhiều quy tắc lặp (FR-020, FR-020a)

`POST /subjects`, `POST /subjects/bulk` (mỗi dòng), `PATCH /subjects/{id}`: các trường lịch phẳng (`weekdays`,
`shift`, `start_time`, `end_time`, `start_date`, `end_date`, `room`) **được thay bằng** `schedules`.

**SubjectInput**:

```json
{"name": "Xử lý ngôn ngữ tự nhiên", "semester_id": 7, "class_code": "2-2-26(N01)",
 "course_code": "CSE703065", "credits": 3, "lecturer": null,
 "schedules": [
   {"weekdays": [5], "start_date": "2026-11-30", "end_date": "2026-12-20",
    "shift": {"start_shift_id": 2, "end_shift_id": 2}, "start_time": null, "end_time": null,
    "period_from": 4, "period_to": 6, "room": "A6-501 (PC)"},
   {"weekdays": [2], "start_date": "2026-12-21", "end_date": "2027-01-24",
    "shift": {"start_shift_id": 2, "end_shift_id": 2}, "room": "A6-203 (PC)"}
 ],
 "tag_ids": [], "reminder_minutes": null, "is_important": false}
```

- `schedules`: ≥ 1. Mỗi quy tắc: đúng một trong `shift` hoặc cặp `start_time`/`end_time`; `start_date`/`end_date`
  bỏ trống = theo học kỳ; ngày phải nằm trong học kỳ. Lỗi theo quy tắc: `fields: {"schedules[1].end_time": "…"}`
  (bulk: `rows[2].schedules[0].room`).
- `PATCH` có `schedules` = thay toàn bộ danh sách quy tắc (quy tắc nào giữ `id` thì cập nhật, không có `id` thì tạo,
  vắng mặt thì xoá); sinh lại buổi, giữ ngoại lệ, buổi có ngoại lệ ngoài lịch mới → `409` như hiện nay (cần
  `?force=true`).
- **Subject** (phản hồi) có thêm `course_code`, `credits`, `schedules: [{id, position, weekdays, start_date,
  end_date, shift, start_time, end_time, period_from, period_to, room}]`; bỏ các trường lịch phẳng.

## Bảng tiết (FR-011 đến FR-015)

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/periods` | `[{number, start_time, end_time, is_manual, shift_id}]` theo `number`; `shift_id` = ca chứa tiết (nếu có) |
| PUT | `/periods/{number}` | `{start_time, end_time}`; tạo hoặc sửa tiết, đặt `is_manual = true`. `400` nếu `end_time ≤ start_time` hoặc `number` ngoài 1–30; trả kèm `warnings` nếu chồng giờ tiết kề |
| POST | `/periods/{number}/reset` | Về giờ suy từ ca (`is_manual = false`); tiết không thuộc ca nào (13–30) thì xoá, trừ 16–18 về mặc định |
| DELETE | `/periods/{number}` | Xoá tiết (chỉ tiết không thuộc ca nào) |

`PATCH /shifts/{id}` (đã có): trong cùng transaction tính lại các tiết của ca đó có `is_manual = false`.

## Nhập thời khoá biểu PDF (FR-001 đến FR-027)

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/imports/timetable-pdf/preview` | `multipart/form-data` trường `file`. Đọc trong bộ nhớ, không lưu gì. Trả `TimetablePdfPreview` ([data-model](../data-model.md#thực-thể-tạm-không-lưu-timetablepdfpreview)) |
| POST | `/imports/timetable-pdf/commit` | Lưu phần đã chọn sau khi người dùng sửa (xem dưới). Một transaction |

**Lỗi của `preview`** (mỗi lỗi một `message` tiếng Việt, chỉ cách khắc phục):

| HTTP | code | Khi nào |
|------|------|---------|
| 413 | `file_too_large` | > 20 MB |
| 415 | `unsupported_file` | không phải PDF (không bắt đầu bằng `%PDF-`) |
| 422 | `pdf_encrypted` | có mật khẩu |
| 422 | `pdf_unreadable` | file hỏng |
| 422 | `pdf_too_long` | > 20 trang |
| 422 | `pdf_no_text` | không có chữ ("hãy dùng nhập từ ảnh") |
| 422 | `pdf_not_timetable` | không tìm thấy bảng có Mã HP, Lớp học phần, Thứ 2…CN, Thời gian |

**Commit payload**:

```json
{"semester": {"choice": "create", "name": "HK2 2026–2027", "start_date": "2026-11-30", "end_date": "2027-02-28"},
 "subjects": [
   {"existing_subject_id": null, "course_code": "FFS701069", "name": "Bóng đá", "class_code": "2-2-26(N01)",
    "credits": 1, "tag_ids": [],
    "schedules": [{"weekdays": [1], "start_date": "2026-11-30", "end_date": "2027-01-24",
                   "shift": {"start_shift_id": 2, "end_shift_id": 2}, "period_from": 4, "period_to": 6,
                   "room": "Sân bóng đá", "save_periods": false}]}
 ]}
```

- `semester.choice`: `use` (`semester_id`), `extend` (`semester_id`, `start_date`, `end_date` mới), `create`
  (`name`, `start_date`, `end_date`).
- `schedules[j].save_periods` (mặc định `false`): quy tắc có khoảng tiết chưa có giờ trong bảng tiết và người dùng
  đã nhập giờ tay; `true` thì ghi các tiết đó vào bảng tiết (`is_manual = true`, chia theo luật FR-012) trong cùng
  transaction (FR-015).
- Chỉ gửi môn và quy tắc được chọn. Server **tính lại** việc khớp môn đã có (R9), không tin trạng thái từ client;
  `existing_subject_id` chỉ là gợi ý và phải khớp khoá R9, sai thì `400`.
- Lỗi theo vị trí: `fields: {"subjects[3].schedules[0].start_time": "Chưa có giờ cho tiết 13–15"}`.
- Thành công: `{semester_id, created_subjects, updated_subjects, created_sessions, updated_sessions,
  skipped_sessions, kept_exception_sessions, warnings}`; ghi tên chuẩn (FR-028); `bump_revision` để đồng bộ/nhắc
  lịch/deadline tự tạo chạy như khi thêm môn bằng tay (FR-026).

## Tên môn chuẩn (FR-028, FR-029)

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/canonical-names` | `[{id, name, course_code, created_at}]` |
| DELETE | `/canonical-names` | Xoá toàn bộ danh sách |

`POST /imports/recognize` (nhập ảnh, đã có): tên sửa theo danh sách tên chuẩn có `reason: "Đã sửa theo thời khoá
biểu"`. `POST /imports/commit` dạng lịch tuần: mỗi dòng ảnh tạo môn với 1 quy tắc.
