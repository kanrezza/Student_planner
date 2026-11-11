# Contract: REST API — thay đổi của feature 005

Bổ sung cho [contract REST của 001](../../001-task-class-scheduler/contracts/rest-api.md) và
[004](../../004-pdf-semester-import/contracts/rest-api.md); base URL, định dạng lỗi, `warnings` giữ nguyên.

## Task: trạng thái, thứ tự, môn

**Task** (phản hồi) thêm: `status: "todo" | "doing" | "done"`, `board_rank: number`, `subject_id: number | null`,
`effective_subject_id: number | null`, `attachment_count: number`.

`POST /tasks`, `PATCH /tasks/{id}` nhận thêm `subject_id` (null = bỏ gắn) và `status: "todo" | "doing"` (chuyển sang
`done` vẫn qua `POST /tasks/{id}/complete` hoặc endpoint bảng dưới đây). Task mới luôn ở đầu cột Chưa làm.

### `GET /tasks/board`

Query: `list_ids`, `tag_ids`, `subject_ids` (danh sách số cách nhau bằng dấu phẩy; rỗng = không lọc), `done_window`
(`7d` mặc định | `all`).

```json
{"columns": {"todo": [Task…], "doing": [Task…], "done": [Task…]},
 "done_hidden_count": 12}
```

- Mỗi cột sắp theo `board_rank`; cột `done` chưa từng sắp tay → theo `completed_at` giảm dần (R2).
- Nhãn: khớp bất kỳ; các loại lọc kết hợp "và"; môn theo môn hiệu lực. Không có task trong Thùng rác.
- `done_window=7d`: chỉ task có `completed_at` ≥ 00:00 của ngày (hôm nay − 6) giờ Việt Nam; `done_hidden_count` là số task
  Xong khớp bộ lọc bị ẩn.

### `PATCH /tasks/{id}/board`

```json
{"status": "doing", "before_id": 12, "after_id": 30}
```

- `before_id` / `after_id`: thẻ ngay trên / ngay dưới vị trí thả trong cột đích (thiếu = đầu/cuối cột). Thẻ không thuộc cột
  đích → 400 `validation_error`.
- Đổi trạng thái theo bảng chuyển ở [data-model](../data-model.md#đổi-tasks); `done` dùng đúng `complete_task`, rời `done`
  dùng `uncomplete_task`.
- `200`: `{"task": Task, "next_task": Task | null, "undo": {"status": "todo", "before_id": 7, "after_id": null}}`.
- `404` task không có hoặc trong Thùng rác.

## Đính kèm

**Attachment**:

```json
{"id": 41, "display_name": "Đề cương NLP.pdf", "size": 2516582, "mime_type": "application/pdf",
 "preview": "pdf", "is_executable": false, "created_at": "2026-11-11T20:15:00+07:00",
 "owner": {"type": "subject", "id": 7, "title": "Xử lý ngôn ngữ tự nhiên"},
 "content_url": "/api/attachments/41/content", "download_url": "/api/attachments/41/download"}
```

`preview`: `"image"` | `"pdf"` | `null` (R8). `owner.type`: `task` | `subject` | `session` | `exam`.

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/attachments?owner_type=task&owner_id=5` | Danh sách theo `created_at` |
| GET | `/attachments/{id}` | Một mục |
| POST | `/attachments` | `multipart/form-data`: `owner_type`, `owner_id`, `file` (lặp được). Trả `201 {"attachments": [Attachment…], "errors": [{"name", "code", "message"}]}`; file lỗi không chặn file khác |
| PATCH | `/attachments/{id}` | `{"display_name": "…"}` |
| DELETE | `/attachments/{id}` | `204`; dọn blob nếu hết tham chiếu |
| GET | `/attachments/{id}/content` | Nội dung; `inline` chỉ khi `preview` khác `null`, ngược lại `attachment` (R8). Có `ETag` = sha256, hỗ trợ `Range` |
| GET | `/attachments/{id}/download` | Luôn `Content-Disposition: attachment; filename*=UTF-8''…` |
| GET | `/attachments/stats` | `{"total_bytes", "blob_count", "attachment_count", "largest": [Attachment…10], "max_file_mb", "backup_warn_mb"}` |

**Lỗi upload** (theo từng file trong `errors`, hoặc HTTP khi cả yêu cầu hỏng):

| HTTP | code | Khi nào |
|------|------|---------|
| 413 | `file_too_large` | file vượt `attachment_max_mb` ("File vượt quá 50 MB (giới hạn trong Cài đặt → File đính kèm)") |
| 400 | `owner_not_found` | nơi gắn không có hoặc task trong Thùng rác |
| 400 | `validation_error` | thiếu `file`, `owner_type` sai |
| 507 | `disk_full` | không đủ chỗ ("Ổ đĩa không đủ chỗ") |

Mục của task trong Thùng rác: `GET` theo task trả `404` như task; không có trong tìm kiếm, thống kê số file.

## Xoá có file: môn học, buổi thi

`DELETE /subjects/{id}` và `DELETE /exams/{id}`: nếu có file (kể cả của các buổi học của môn) và thiếu `?confirm=true`
→ `409 {"error": {"code": "confirm_required", "details": {"attachment_count": 3}}}`. Có `confirm=true` → xoá như cũ và
dọn blob.

Sửa lịch môn (`PATCH /subjects/{id}`, nhập PDF) làm mất buổi có file → file chuyển sang môn, `warnings` có
`{"code": "attachments_moved", "message": "Đã chuyển 2 file của buổi bị xoá sang môn học"}`.

## Số file ở các phản hồi khác

`Subject`, `ClassSession`, `Exam` thêm `attachment_count` (chỉ mục đang hiển thị).

## Tìm kiếm

`GET /search` thêm nhóm `files`: `{"attachment_id", "name", "owner": {type, id, title}, "snippet"}`; `group=files` lọc
riêng.

## Cài đặt

`GET/PATCH /settings` thêm `attachment_max_mb` (1–500) và `backup_attachments_warn_mb` (100–1000000); ngoài khoảng → 400
theo trường.

## Sao lưu

- `.lhbackup` format 2 ([data-model](../data-model.md#bản-sao-lưu-lhbackup-format-2-r7)); khôi phục nhận format 1 và 2.
- `GET /backup/status` thêm `attachments_bytes`, `estimated_backup_bytes`, `attachments_warning: bool`.
- `nginx`: `location /api/attachments` `client_max_body_size 510m`, `proxy_request_buffering off`.
