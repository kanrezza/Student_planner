# Data Model: Thiết kế lại giao diện và đóng gói app macOS

**Feature**: `002-redesign-macos-app` | **Date**: 2026-11-04 | **Plan**: [plan.md](plan.md)

Feature này **mở rộng** data model của feature 001
([001 data-model](../001-task-class-scheduler/data-model.md)); mọi bảng và quy tắc ở đó giữ nguyên.
Thay đổi nằm trong một migration mới `backend/migrations/versions/0004_redesign.py` (sau
`0003_auto_deadline_reminder`). Migration lịch thi của feature 001 (T110) đổi số thành
`0005_exams.py` nếu làm sau.

---

## tasks — thêm cột

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| work_date | date | tuỳ chọn; ngày của khung giờ làm (FR-018) |
| work_start | time | tuỳ chọn |
| work_end | time | tuỳ chọn |
| deleted_at | timestamptz | `NULL` = không ở Thùng rác; có giá trị = thời điểm chuyển vào Thùng rác (FR-030) |
| trashed_from_list_name | text | tuỳ chọn; tên danh sách cũ khi task vào Thùng rác do xoá danh sách (FR-031) |

- CHECK `(work_date IS NULL) = (work_start IS NULL) AND (work_date IS NULL) = (work_end IS NULL)`.
- CHECK `work_end IS NULL OR work_end > work_start`.
- Index một phần `(deleted_at) WHERE deleted_at IS NOT NULL` cho Thùng rác và việc xoá hẳn; index
  `(work_date)`.
- **Task đang dùng** (`active`) = `deleted_at IS NULL`. Mọi truy vấn của feature 001 (danh sách,
  Hôm nay, lịch, feed đồng bộ, bản tóm tắt, nhắc trình duyệt, đếm task của danh sách, reconcile
  deadline tự tạo) chỉ xét task đang dùng.
- Khung giờ làm KHÔNG ảnh hưởng: thời điểm nhắc, `due_at`, quá hạn, feed đồng bộ, bản tóm tắt
  (FR-019). Sửa khung giờ làm của task tự tạo đặt `user_modified = true`.
- **Cảnh báo** (không chặn): `work_date > due_date` → `warnings: [{code: "work_after_due"}]`.

### Vòng đời Thùng rác

```text
            xoá (⌘⌫)                    > 30 ngày hoặc "Xoá vĩnh viễn"/"Dọn sạch"
 [Đang dùng] ─────────> [Trong Thùng rác] ─────────────────────────────> [Đã xoá hẳn]
      ^                       │
      └────── khôi phục ──────┘
```

- Vào Thùng rác: `deleted_at = now()`; nếu `is_auto` và có `source_session_id` thì đặt
  `class_sessions.auto_task_suppressed = true` (FR-031); `bump_revision`.
- Khôi phục: `deleted_at = NULL`, `trashed_from_list_name = NULL`; nếu task tự tạo còn buổi nguồn thì
  `auto_task_suppressed = false` rồi reconcile buổi đó; `bump_revision`.
- Xoá hẳn tự động: `deleted_at < now() − 30 ngày` (`purge_expired_trash`, research R6).
- **Còn N ngày** = `30 − số ngày đã qua kể từ deleted_at` (làm tròn lên, tối thiểu 0).

## task_lists — thêm cột

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| emoji | text | tuỳ chọn; đúng một emoji (một cụm ký tự hiển thị, kiểm tra ở schema bằng biểu thức emoji của Unicode), tối đa 16 byte (CHECK) |

- Xoá danh sách với `delete_tasks=true` (feature 001): các task chưa ở Thùng rác được chuyển sang
  danh sách "Học tập", vào Thùng rác và ghi `trashed_from_list_name` = tên danh sách bị xoá.

## class_sessions — thêm cột

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| original_date | date | `NULL` = chưa dời; có giá trị = ngày gốc trước khi dời (FR-028) |

- **Ngày khoá** khi sinh lại buổi theo quy tắc lặp = `original_date ?? date`.
- `has_exception` = `is_cancelled OR time_overridden OR room_overridden OR original_date IS NOT
  NULL`.
- Dời về đúng ngày gốc → `original_date = NULL` (vẫn có thể còn `time_overridden`).
- Ràng buộc `uq_class_sessions_slot (subject_id, date, start_at)` giữ nguyên.

**Trạng thái** (bổ sung vào sơ đồ của feature 001):

```text
 [Thường] ── dời ngày ──> [Đã dời] ── huỷ ──> [Đã huỷ]
    ^                        │  ^                 │
    └── dời về ngày gốc ─────┘  └──── khôi phục ──┘
```

## Thực thể suy ra (không lưu)

### Danh sách thông minh (FR-009)

Chỉ task đang dùng và chưa hoàn thành. `D` = hôm nay (giờ Việt Nam).

| View | Điều kiện |
|------|-----------|
| `today` | `due_date = D` OR quá hạn (`due_at < now`) OR `work_date = D` |
| `tomorrow` | `due_date = D+1` OR `work_date = D+1` |
| `next7` | `due_date ∈ [D, D+6]` OR `work_date ∈ [D, D+6]` OR quá hạn |
| `all` | mọi task chưa hoàn thành |
| `completed` | task đang dùng đã hoàn thành, sắp `completed_at` giảm dần |
| `trash` | `deleted_at IS NOT NULL`, sắp `deleted_at` giảm dần |
| `list:{id}` | task chưa hoàn thành của danh sách |
| `tag:{id}` | task chưa hoàn thành có nhãn |

Số đếm (`/task-counts`) = số task của các view `today`, `tomorrow`, `next7`, `all`, và từng danh
sách (task chưa hoàn thành, đang dùng).

### Nhóm task trong khu vực chính (FR-010) — hàm thuần ở frontend `groupTasks(tasks, now)`

Ngày tham chiếu của task = `min(due_date, work_date)` theo các giá trị có mặt (task có khung giờ làm
hôm nay nhưng hạn tuần sau nằm ở nhóm Hôm nay).

| Nhóm | Điều kiện | Sắp xếp |
|------|-----------|---------|
| Quá hạn | `is_overdue` | `due_at` tăng |
| Hôm nay | ngày tham chiếu = D | giờ (khung giờ làm hoặc giờ hạn; không giờ ở cuối), rồi ưu tiên |
| Ngày mai | = D+1 | như trên |
| 7 ngày tới | ∈ [D+2, D+6], tách theo từng ngày có tiêu đề "Thứ Năm, 12/11" | như trên |
| Sau này | > D+6 | ngày, rồi giờ |
| Không có hạn | không có hạn và không có khung giờ làm | ưu tiên, rồi `id` |

### Giá trị mặc định khi thêm nhanh (FR-017) — hàm thuần `quickAddDefaults(view, now, studyListId)`

| View | `due_date` | `list_id` | `tag_ids` |
|------|------------|-----------|-----------|
| today | D | Học tập | [] |
| tomorrow | D+1 | Học tập | [] |
| next7 | D | Học tập | [] |
| all, completed, trash | null | Học tập | [] |
| list:{id} | null | id | [] |
| tag:{id} | null | Học tập | [id] |

### Khối trên lịch (FR-022, FR-023) — hàm thuần `toCalendarEvents`

| Mục | Vị trí | Kéo | Kéo dãn |
|-----|--------|-----|---------|
| Task có khung giờ làm | `work_date work_start` → `work_end` | có (chưa xong) | có |
| Task có giờ hạn, không khung giờ làm | `due_at` → `due_at + 30 phút`, biểu tượng hạn chót | có (chưa xong) | không |
| Task chỉ có ngày hạn | Cả ngày, `due_date` | có (chưa xong) | không |
| Buổi học | `start_at` → `end_at`, kèm phòng, "Đã dời"/"Đã huỷ" | có (chưa huỷ), hỏi xác nhận | không |
| Buổi thi (khi có US11) | `start_at` → `end_at`, nền đậm, nhãn "Thi" | không | không |

### Quy tắc kéo thả (FR-026 đến FR-028) — hàm thuần `dropToPatch(item, start, end, allDay)`

| Mục / đích | PATCH |
|------------|-------|
| Task có khung giờ làm → giờ khác | `PATCH /tasks/{id}` `{work_date, work_start, work_end}` (giữ thời lượng) |
| Task có khung giờ làm → kéo dãn | `{work_end}` (≥ 15 phút sau `work_start`) |
| Task có khung giờ làm → hàng Cả ngày | `{work_date: null, work_start: null, work_end: null, due_date: ngày đích}` |
| Task chỉ giờ hạn → giờ khác | `{due_date, due_time}` |
| Task chỉ giờ hạn → hàng Cả ngày | `{due_date, due_time: null}` |
| Task chỉ ngày → giờ trong lưới | `{work_date, work_start, work_end: start + 1 giờ}` |
| Task chỉ ngày → Cả ngày ngày khác | `{due_date}` |
| Vùng trống được chọn | mở bảng tạo task với `{work_date, work_start, work_end, due_date: ngày đó}` |
| Buổi học → giờ/ngày khác | sau xác nhận: `PATCH /sessions/{id}` `{date, start_time, end_time}` |

Mọi thời điểm làm tròn 15 phút. **Hoàn tác** (FR-029) = gửi PATCH với giá trị cũ của đúng các trường
đã đổi.

### Trạng thái giao diện (lưu trong trình duyệt/webview, không ở database)

- `localStorage`: mục và view đang chọn gần nhất, các nhóm đã thu gọn, chế độ lịch gần nhất.
- Kích thước và vị trí cửa sổ: plugin window-state của Tauri (thư mục Application Support của app).
