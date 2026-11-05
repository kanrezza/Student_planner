# REST API — phần thêm của feature 003

Gốc `/api`, chỉ qua `http://127.0.0.1:8080` (constitution IV). JSON, ngày `YYYY-MM-DD`, giờ `HH:MM`, thời điểm
ISO 8601 có múi giờ. Lỗi theo dạng hiện có: `{"error": {"code": "...", "message": "<tiếng Việt>", "fields": {...}}}`.

## Sao lưu (đợt 1)

### Dùng bởi giao diện

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/backup/status` | Cấu hình + trạng thái + danh sách bản + việc đang chạy |
| PATCH | `/backup/config` | Sửa `enabled`, `schedule_time`, `destination_path` (null = mặc định; khác null phải là đường dẫn tuyệt đối bắt đầu bằng `/`, nếu không → 400 "Đường dẫn thư mục phải là đường dẫn đầy đủ"), `retention_count` (1–365) |
| POST | `/backup/jobs` | `{"kind":"backup_now"}` hoặc `{"kind":"restore","source_path":"..."}` → 201 job; 409 `job_running` nếu đang có việc |

`GET /backup/status` → 200

```json
{
  "config": {"enabled": true, "schedule_time": "21:00", "destination_path": null,
             "destination_display": "iCloud Drive › Lịch Học Cá Nhân › Sao lưu", "retention_count": 14},
  "agent_online": true,
  "destination": {"state": "ok", "message": null, "path": "/Users/…/Sao lưu"},
  "last_attempt": {"at": "2026-11-05T21:00:12+07:00", "ok": true, "size": 2516582, "error": null},
  "last_success": {"at": "2026-11-05T21:00:12+07:00", "size": 2516582},
  "stale": false,
  "files": [{"name": "LichHoc-2026-11-05-2100-tu-dong.lhbackup", "path": "…", "kind": "tu-dong",
             "created_at": "…", "size": 2516582, "location": "local"}],
  "job": {"id": 12, "kind": "restore", "state": "running", "step": "restoring", "message": null}
}
```

`agent_online = false` → giao diện hiện "Trình đồng bộ chạy nền chưa chạy, chưa sao lưu được" và vô hiệu nút.
Khi đang khôi phục (chế độ bảo trì) **mọi** API khác trả 503 `{"error":{"code":"restoring", "message":"Đang
khôi phục dữ liệu…"}}`; riêng `GET /health`, `GET /backup/status`, `PUT /backup/jobs/{id}`,
`PUT /backup/agent-report` và `POST /backup/restore` vẫn trả lời.

### Dùng bởi agent

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/backup/config` | Cấu hình hiện tại (agent cache lại) |
| POST | `/backup/jobs/claim` | Nhận việc `pending` cũ nhất → 200 job (đã chuyển `running`) hoặc 204 |
| PUT | `/backup/jobs/{id}` | `{"state":"running"\|"done"\|"failed","step":"…","message":"…"}` |
| GET | `/backup/dump?kind=tu-dong` | Tạo và trả file `.lhbackup` (`application/zip`); header `X-Backup-Name`, `X-Backup-Sha256`, `Content-Length` |
| POST | `/backup/restore` | Thân là file `.lhbackup` (`application/zip`, stream) → 200 `{"restored_from": "...", "schema_upgraded": bool}` |
| PUT | `/backup/agent-report` | Báo cáo thư mục và lần thử (bảng `backup_status`) |

Lỗi của `/backup/restore`: 400 `backup_corrupt` ("Bản sao lưu bị hỏng, không thể khôi phục"), 409
`backup_too_new` ("Bản sao lưu được tạo bởi phiên bản app mới hơn…"), 409 `job_running`, 500 `restore_failed`
(dữ liệu hiện tại giữ nguyên), 500 `upgrade_failed` (dữ liệu đã khôi phục nhưng nâng cấp lỗi — agent tự khôi
phục lại bản "Trước khi khôi phục", xem `agent-backup.md`). Thân tối đa 500 MB; nginx của `web` cho phép
`/api/backup/` nhận thân 500 MB và chờ tới 600 giây. Lỗi của `/backup/dump`: 500 `dump_failed`.

`GET /sync/changes` thêm trường `backup_jobs_pending: int` và `backup_config_revision: int`.

## Task (đợt 2 và 4)

### `POST /tasks` (mở rộng)

- Thêm `tag_names: string[]` (đợt 2) — tạo nhãn chưa có, so khớp không dấu/hoa thường (R14).
- Thêm `recurrence: RecurrenceRule | null` (đợt 4) — xem [data-model §4](../data-model.md).

### `PATCH /tasks/{id}` (đợt 4)

- Thêm `scope: "this" | "following"`. Task có `series_id`, sửa trường khác `recurrence`, thiếu `scope` → 409
  `{"error":{"code":"scope_required"}}`.
- `recurrence`: đặt / đổi / bỏ quy tắc (áp dụng cả chuỗi, không cần `scope`); `null` = bỏ lặp.
- Đổi `due_date` với `scope:"following"` → quy tắc dời theo FR-020a.

### `DELETE /tasks/{id}?scope=this|following` (đợt 4)

Task lặp thiếu `scope` → 409 `scope_required`. Trả về task đã vào Thùng rác và (với `this`) lần hiện tại mới.

### `POST /tasks/{id}/complete` và `/uncomplete` (đợt 4)

`complete` trả thêm `next_task` (hoặc `null` khi chuỗi kết thúc). `uncomplete` trả thêm `removed_next_task_id`.

### Đối tượng `Task` trả về (đợt 4) thêm

`series_id`, `recurrence` (quy tắc của chuỗi, hoặc `null`), `occurrence_no`, `series_finished` (bool).

## Lịch (đợt 4)

`GET /calendar?start=&end=` thêm mục `{"kind":"projected_task","series_id":…, "current_task_id":…,
"date":"…","time":"…"|null,"title":"…","color":"…"}`; tối đa 400 mục dự kiến mỗi khoảng.

## Tìm kiếm (đợt 3)

`GET /search?q=<từ khoá>&include_done=0|1&group=<loại>&limit=20`

- `q` sau khi chuẩn hoá NFC, cắt khoảng trắng, rỗng → 200 với mọi nhóm rỗng.
- Không có `group`: mỗi nhóm tối đa `limit` (mặc định 20, tối đa 200) mục + `total`. Có `group` (`tasks`,
  `lists`, `tags`, `subjects`, `sessions`, `exams`): chỉ nhóm đó, dùng cho "Xem thêm".

```json
{
  "query": "nop bai",
  "groups": {
    "tasks":    {"total": 3, "items": [{"id": 5, "title": "Nộp bài QTDA", "list": {"id": 1, "name": "Học tập", "emoji": "📚"},
                                        "due_date": "2026-11-06", "due_time": "09:00", "completed": false,
                                        "matched_field": "title", "snippet": null}]},
    "lists":    {"total": 0, "items": []},
    "tags":     {"total": 0, "items": []},
    "subjects": {"total": 0, "items": []},
    "sessions": {"total": 0, "items": []},
    "exams":    {"total": 0, "items": []}
  }
}
```

- `snippet`: khi khớp ở ghi chú, đoạn ~80 ký tự quanh chỗ khớp đầu tiên (frontend tự tô sáng).
- Danh sách/nhãn kèm `open_count`; buổi học/thi kèm `subject`, `starts_at`, `room`, `is_cancelled`.
- Thứ tự theo FR-040.
