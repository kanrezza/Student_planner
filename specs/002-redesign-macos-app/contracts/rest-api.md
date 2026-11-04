# Contract: REST API — phần mở rộng của feature 002

Bổ sung cho [contract REST của feature 001](../../001-task-class-scheduler/contracts/rest-api.md);
quy ước chung (base URL `http://127.0.0.1:8080/api`, lỗi, cảnh báo, ngày giờ) giữ nguyên. Endpoint
không nhắc tới ở đây không đổi, trừ việc mọi endpoint đọc task chỉ trả task **đang dùng** (không ở
Thùng rác).

## Task

**Task (đọc)** — thêm trường:

```json
{"work_date": "2026-11-12", "work_start": "19:00", "work_end": "21:00",
 "deleted_at": null, "days_left_in_trash": null, "trashed_from_list_name": null}
```

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/tasks?view=today\|tomorrow\|next7\|all\|completed\|trash&list_id=&tag_id=` | Danh sách thông minh theo [data-model](../data-model.md#danh-sách-thông-minh-fr-009); `list_id`/`tag_id` dùng thay `view` cho danh sách người dùng và nhãn. Gọi `purge_expired_trash` trước khi đọc với `view=trash`. Tham số cũ `list_id`, `tags`, `include_completed` vẫn hoạt động |
| GET | `/task-counts` | `{today, tomorrow, next7, all, lists: {"<list_id>": n}}`; gọi `purge_expired_trash` trước |
| POST | `/tasks` | thêm `work_date?`, `work_start?`, `work_end?` (cả ba hoặc không); lỗi theo trường: `work_end` "Giờ kết thúc phải sau giờ bắt đầu", `work_date` "Cần chọn đủ ngày, giờ bắt đầu và giờ kết thúc"; cảnh báo `work_after_due` |
| PATCH | `/tasks/{id}` | như POST, sửa một phần; gửi cả ba trường `null` để bỏ khung giờ làm |
| DELETE | `/tasks/{id}` | **đổi nghĩa**: chuyển vào Thùng rác, trả `200 {task}` (để Hoàn tác); task đã ở Thùng rác → `404` |
| POST | `/tasks/{id}/restore` | khôi phục; trả `{task, warnings}`, cảnh báo `list_replaced` khi `trashed_from_list_name` khác null ("Danh sách cũ "X" đã bị xoá, công việc được đưa về Học tập") |
| DELETE | `/tasks/{id}?permanent=true` | chỉ cho task trong Thùng rác; xoá hẳn, `204` |
| DELETE | `/trash` | dọn sạch Thùng rác, trả `{deleted: n}` |

## Danh sách

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/lists` | thêm `emoji` (null nếu không có) |
| POST · PATCH | `/lists`, `/lists/{id}` | nhận `emoji?`; không phải đúng một emoji → `400 {fields: {emoji: "Chỉ chọn một emoji"}}`; `null` để bỏ |
| DELETE | `/lists/{id}?delete_tasks=true` | **đổi nghĩa**: task của danh sách vào Thùng rác (chuyển sang Học tập, ghi `trashed_from_list_name`) thay vì bị xoá hẳn |

## Lịch

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/calendar?from=&to=&tags=` | `tasks` gồm task có `due_date` **hoặc** `work_date` trong khoảng (mỗi task một lần) |
| GET | `/today` | `tasks_due_today` gồm thêm task có `work_date` hôm nay |

## Buổi học

**Session (đọc)** — thêm trường `original_date` (null nếu chưa dời) và `is_moved`.

| Method | Path | Mô tả |
|--------|------|-------|
| PATCH | `/sessions/{id}` | thêm `date?` (dời sang ngày khác, FR-028). Trùng `(môn, ngày, giờ bắt đầu)` với buổi khác → `400 {fields: {date: "Môn này đã có buổi học vào ngày và giờ đó"}}`. Ngoài học kỳ → thành công kèm `warnings: [{code: "outside_semester"}]`. Trả `{session, warnings}` |

## Không đổi

- `/api/sync/*`, `/api/reminders/upcoming`, `/api/digest`: dữ liệu tự loại task trong Thùng rác; khung
  giờ làm không xuất hiện trong feed (FR-019); buổi đã dời xuất hiện theo ngày mới.
- `/api/health`: dùng cho app Tauri kiểm tra kết nối ([desktop-shell](desktop-shell.md)).
