# Data Model: Bảng Kanban cho công việc và đính kèm file

**Feature**: [spec.md](spec.md) · **Research**: [research.md](research.md)

Một migration `0012_kanban_attachments` (down_revision `0011_periods_canonical_names`), cùng thư mục file trong
volume `lichhoc_attachments`.

## Đổi: `tasks`

| Cột | Kiểu | Ràng buộc / ghi chú |
|-----|------|---------------------|
| in_progress | boolean | NOT NULL, mặc định `false`. Chỉ có nghĩa khi `completed_at IS NULL`; đặt về `false` khi hoàn thành |
| board_rank | double precision | NOT NULL. Thứ tự trong cột (nhỏ lên trên). Migration: đánh số 1, 2, 3… theo `sort_key` hiện có trong từng nhóm trạng thái |
| subject_id | bigint FK → subjects | NULL, `ON DELETE SET NULL`; môn gắn tay (R3) |

Index: `(completed_at IS NULL, in_progress, board_rank)` cho truy vấn bảng; `subject_id`.

**Trạng thái suy ra** (R2):

```text
status = "done"  nếu completed_at IS NOT NULL
         "doing" nếu in_progress
         "todo"  còn lại
```

**Chuyển trạng thái** (mọi chuyển đều qua service của task, cùng một transaction):

| Từ → Đến | Hiệu ứng |
|----------|----------|
| todo → doing | `in_progress = true` |
| doing → todo | `in_progress = false` |
| todo/doing → done | `complete_task`: `completed_at = now`, `in_progress = false`, lần kế tiếp của task lặp được sinh với `board_rank` đầu cột Chưa làm, gỡ nhắc, `bump_revision` |
| done → todo | `uncomplete_task` (gỡ lần kế tiếp chưa sửa) |
| done → doing | `uncomplete_task` rồi `in_progress = true` |

Sau mỗi lần chuyển hoặc đổi chỗ: `board_rank` được đặt theo vị trí thả (giữa hai thẻ kề, `min − 1` khi lên đầu cột,
`max + 1` khi xuống cuối). Khoảng cách < `1e-6` thì sắp lại cả cột (R2). Task mới (mọi đường tạo) nhận
`board_rank = min(board_rank của cột Chưa làm) − 1`.

**Môn hiệu lực** (lọc bảng): `COALESCE(tasks.subject_id, class_sessions.subject_id qua tasks.source_session_id)`.

## Đổi: `settings`

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| attachment_max_mb | smallint | NOT NULL, mặc định 50, `BETWEEN 1 AND 500` |
| backup_attachments_warn_mb | integer | NOT NULL, mặc định 1024, `BETWEEN 100 AND 1000000` |

## Mới: `attachment_blobs` — nội dung file (một bản mỗi nội dung)

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| sha256 | char(64) | PK, chữ thường hex |
| size | bigint | NOT NULL, `>= 0` |
| mime_type | text | NOT NULL (đã xác định theo phần mở rộng + chữ ký, R8), mặc định `application/octet-stream` |
| is_executable | boolean | NOT NULL, mặc định `false` (R9) |
| created_at | timestamptz | NOT NULL, mặc định `now()` |

File trên đĩa: `/var/lib/lichhoc/attachments/<sha256[0:2]>/<sha256>` (volume `lichhoc_attachments`). Dòng blob chỉ
được tạo sau khi file đã `fsync` + đổi tên vào chỗ (R4).

## Mới: `attachments` — một lần gắn file vào một nơi

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| id | bigint | PK |
| blob_sha256 | char(64) FK → attachment_blobs | NOT NULL, `ON DELETE RESTRICT` (blob chỉ bị xoá khi hết tham chiếu) |
| task_id | bigint FK → tasks | NULL, `ON DELETE CASCADE` |
| subject_id | bigint FK → subjects | NULL, `ON DELETE CASCADE` |
| session_id | bigint FK → class_sessions | NULL, `ON DELETE CASCADE` |
| exam_id | bigint FK → exams | NULL, `ON DELETE CASCADE` |
| display_name | text | NOT NULL, 1–255 ký tự, NFC, không chứa `/` hay ký tự điều khiển |
| created_at | timestamptz | NOT NULL, mặc định `now()` |

- CHECK `num_nonnulls(task_id, subject_id, session_id, exam_id) = 1`.
- Index trên từng cột nơi gắn; index biểu thức `vn_fold(display_name)` cho tìm kiếm (R11).
- **Tên trùng trong cùng nơi gắn**: khi tạo, nếu đã có `display_name` giống (so `ci_key`) ở cùng nơi gắn thì thêm
  " (2)", " (3)"… trước phần mở rộng (US4 kịch bản 6). Cùng nội dung gắn lại vào cùng nơi cũng tạo mục mới (người dùng
  chủ động).
- **Hiển thị**: mục của task có `deleted_at` khác NULL bị ẩn khỏi mọi danh sách, số đếm, tìm kiếm và thống kê "số file";
  nhưng blob vẫn được tính là "đang dùng" (Thùng rác giữ file, FR-023).

## Vòng đời và dọn dẹp (R6, R12)

```text
upload ─▶ .incoming/<uuid> ─fsync─▶ (hash đã có? bỏ file tạm : os.replace → ab/<sha>) ─▶ INSERT blob (nếu mới) + attachment ─▶ COMMIT
xoá mục / xoá hẳn task / xoá môn / xoá buổi thi ─▶ COMMIT ─▶ collect_garbage({các sha bị ảnh hưởng})
regenerate_sessions xoá buổi có file ─▶ UPDATE attachments SET session_id=NULL, subject_id=<môn> (trước DELETE) + cảnh báo attachments_moved
khởi động backend + mỗi ngày ─▶ sweep: xoá .incoming/* cũ > 1 giờ, file không có blob VÀ có thời gian sửa cũ > 1 giờ, blob không có attachment
```

**Chạy chồng**: `collect_garbage` khoá dòng blob (`SELECT … FOR UPDATE`) rồi kiểm tra lại tham chiếu; upload chèn blob bằng `INSERT … ON CONFLICT DO NOTHING`, khoá dòng và đặt lại file nếu đang thiếu.

`collect_garbage(shas)`: với mỗi sha không còn dòng `attachments` nào (kể cả của task trong Thùng rác) → xoá dòng blob,
commit, rồi xoá file. Lỗi xoá file chỉ ghi log; lượt quét sau sẽ dọn.

## Bản sao lưu `.lhbackup` format 2 (R7)

```text
manifest.json   {"format": 2, …format 1…, "attachments": {"count": n, "bytes": b}}
data.dump       pg_dump -Fc (như cũ; gồm cả attachment_blobs, attachments)
attachments/<sha256>   mỗi blob đúng một mục, ZIP_STORED
```

Khôi phục: format 1 → như cũ, sau đó quét dọn sẽ xoá mọi blob không còn tham chiếu (dữ liệu cũ không có đính kèm).
Format 2 → kiểm tra `attachments/` khớp SHA-256 và khớp danh sách `attachment_blobs` trong dump, giải nén vào
`.restore/`, nạp dump, chuyển blob vào chỗ, quét dọn.

## Tuỳ chọn xem trên máy (localStorage, không lưu CSDL)

| Khoá | Giá trị |
|------|---------|
| `lichhoc.tasks.view` | `"list"` \| `"board"` |
| `lichhoc.board.filters` | `{list_ids: number[], tag_ids: number[], subject_ids: number[]}` |
| `lichhoc.board.doneAll` | `boolean` (cột Xong hiện tất cả) |
