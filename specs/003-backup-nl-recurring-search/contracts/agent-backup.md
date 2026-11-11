# Agent — sao lưu, khôi phục, thông báo (đợt 1)

Mở rộng `mac-agent/lichhoc_agent/`. Mọi hàm quyết định là hàm thuần có test (`tests/test_backup_*.py`).

## Luồng chạy

```
luồng chính: vòng lặp sự kiện Cocoa (nhận click thông báo)                       [research R10]
luồng nền:   loop:
               changes = long-poll /sync/changes (≤ 25 s)
               đồng bộ Lịch/Lời nhắc như hiện tại
               backup_tick(now):
                 config = cache (làm mới khi backup_config_revision đổi)
                 job = claim() nếu backup_jobs_pending > 0
                 if job.kind == backup_now            → run_backup("thu-cong", job)
                 elif job.kind == restore             → run_restore(job)
                 elif backup_due(now, …)              → run_backup("tu-dong")
                 if stale_notice_due(now, …)          → notify_stale()
                 report() nếu có thay đổi hoặc đã 60 s
```

## `run_backup(kind)`

1. `dest = resolve_destination(config)` → `(path, state, message)`:
   - `destination_path = null` → thư mục mặc định trong iCloud Drive; tạo nếu `com~apple~CloudDocs` tồn tại,
     nếu không: `icloud_off` "iCloud Drive chưa bật. Bật iCloud Drive hoặc chọn thư mục khác."
   - đường dẫn tự chọn không tồn tại → `missing` "Không tìm thấy thư mục sao lưu (ổ đĩa có thể đã được tháo).
     Sẽ thử lại khi ổ được cắm lại."
   - không ghi được → `no_permission` / `not_writable` kèm cách khắc phục (research R6).
   - `state != ok` → ghi `last_attempt` thất bại, log WARNING, kết thúc (không ném lỗi, không hộp thoại).
2. `GET /backup/dump?kind=…` stream vào `.<tên>.partial`, `fsync`, đọc lại SHA-256, so với header.
3. `os.replace` → tên thật (`unique_name` thêm `-2`, `-3` nếu trùng).
4. `prune(files, retention_count, protect=None)` — chỉ sau khi bước 3 thành công; chỉ file khớp mẫu tên; mới
   nhất giữ lại; file `protect` (bản đang được khôi phục) không bao giờ bị xoá. Trong `run_restore`, bước
   `pre_backup` gọi `run_backup(..., protect=source_path)` và dọn lại một lần sau khi khôi phục xong (FR-006).
   Mỗi file bị xoá ghi một dòng log INFO "Đã xoá bản sao lưu cũ: <tên>".
5. Ghi `last_attempt`/`last_success`, log INFO "Sao lưu xong: <tên> (<dung lượng>)", `report()`.

Lỗi ở bất kỳ bước nào → xoá file `.partial`, log ERROR kèm lý do, `last_attempt_ok = false`, không xoá bản cũ.

## `run_restore(job)`

Bước (cập nhật `job.step` trước mỗi bước): `pre_backup` (= `run_backup("truoc-khoi-phuc")`, thất bại → job
`failed` "Không tạo được bản sao lưu dữ liệu hiện tại nên chưa khôi phục.") → `downloading` (nếu file đang trên
iCloud; chờ ≤ 5 phút) → kiểm tra manifest + SHA-256 (hỏng → `failed` "Bản sao lưu bị hỏng, không thể khôi
phục") → `uploading` + `restoring` (`POST /backup/restore`) → `resync` (`sync_once(force=True)`) → `done`
"Đã khôi phục dữ liệu về <giờ> <ngày>". Backend trả `upgrade_failed` → agent gửi lại bản `truoc-khoi-phuc`
vừa tạo qua `POST /backup/restore`, rồi job `failed` "Không nâng cấp được dữ liệu của bản sao lưu cũ; dữ liệu
đã được đưa về như trước khi khôi phục." Trong lúc khôi phục, các lời gọi `/sync/*` và `/backup/agent-report`
trả 503 `restoring` là bình thường: agent bỏ qua, không tính là lỗi. Mỗi bước ghi một dòng log INFO (lỗi:
ERROR kèm lý do) vào `agent.log`.

## Hàm thuần (test bắt buộc)

| Hàm | Ca test tối thiểu |
|-----|-------------------|
| `backup_due(now, schedule_time, enabled, last_success_at, last_attempt_at)` | đúng giờ; trước giờ; ngủ 18:00→07:30 (bù một lần); tắt 3 ngày (một bản); đổi giờ sang 22:00; vừa thất bại < 4 phút (chưa thử lại); tắt sao lưu; đồng hồ lùi |
| `stale_notice_due(now, last_success_at, enabled_since, notified_for)` | chưa đủ 3 ngày; vừa quá 3 ngày; đã gửi cho mốc này; có bản mới rồi lại quá 3 ngày |
| `parse_backup_name(name)` / `unique_name(dir_names, created_at, kind)` | 3 loại; file lạ; `.icloud`; trùng phút |
| `prune(files, keep)` | 16 bản giữ 14; giảm xuống 7; file lạ không bị đụng; `keep` ≥ số bản |
| `resolve_destination(config, fs)` | mặc định có/không iCloud; SSD tháo; không quyền (fs giả lập) |

## Log (FR-010a)

Ghi vào `~/Library/Logs/LichHocAgent/agent.log` (handler hiện có): bắt đầu/kết thúc mỗi lần sao lưu, khôi phục,
xoá bản cũ, thư mục đích, dung lượng, lý do lỗi. Không ghi nội dung dữ liệu.

## Thông báo

Tiêu đề "Lịch Học Cá Nhân", nội dung "Đã 3 ngày chưa sao lưu được dữ liệu. Mở Cài đặt → Sao lưu để kiểm
tra."; bấm → `open lichhoc://cai-dat/sao-luu`. Xin quyền thông báo lần đầu khi cần gửi.


> **Feature 005**: file `.lhbackup` lên **format 2** — thêm `attachments/<sha256>` cho mỗi file đính kèm và `attachments` trong
> `manifest.json`; `GET /backup/status` thêm `attachments_bytes`, `estimated_backup_bytes`, `attachments_warning`. Agent đọc
> được cả format 1 và 2 (chỉ chép nguyên file). Xem [data-model 005](../../005-kanban-attachments/data-model.md#bản-sao-lưu-lhbackup-format-2-r7).
