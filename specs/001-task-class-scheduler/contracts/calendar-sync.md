# Contract: Đồng bộ Lịch/Lời nhắc (mac-agent ↔ backend ↔ EventKit)

**Bên tham gia**: `mac-agent` (LichHocAgent.app, chạy trên macOS) gọi backend qua
`http://127.0.0.1:8080/api/sync/*`. Agent là bên duy nhất ghi vào Lịch và Lời nhắc của Apple.
Cơ chế chi tiết xem [research R5](../research.md#r5-cơ-chế-đồng-bộ-backend--lịchlời-nhắc).

## 1. Chờ thay đổi (long-poll)

`GET /api/sync/changes?after={revision}&wait={giây ≤ 25}`

- Trả **ngay** `200 {"revision": N, "sync_enabled": bool}` nếu `N > after`, hoặc nếu
  `sync_enabled` vừa đổi.
- Nếu không có thay đổi trong `wait` giây: trả `200` với cùng `revision`.
- Lần đầu khởi động, agent gọi với `after=0`.

## 2. Lấy trạng thái mong muốn

`GET /api/sync/feed`

```json
{
  "revision": 812,
  "sync_enabled": true,
  "calendar_name": "Lịch Học Cá Nhân",
  "reminder_list_name": "Lịch Học Cá Nhân",
  "events": [
    {"sync_key": "session:123", "fingerprint": "9f2c…",
     "title": "Giải tích", "location": "A101",
     "start_at": "2026-11-16T07:30:00+07:00", "end_at": "2026-11-16T09:30:00+07:00",
     "important": false, "alarms_minutes_before": [15]},
    {"sync_key": "exam:7", "fingerprint": "c03d…",
     "title": "★ Thi: Cơ sở dữ liệu", "location": "A5-310",
     "start_at": "2027-01-05T07:30:00+07:00", "end_at": "2027-01-05T08:30:00+07:00",
     "important": true, "alarms_minutes_before": [10080, 1440, 180, 60, 15]}
  ],
  "reminders": [
    {"sync_key": "task:45", "fingerprint": "41ab…",
     "title": "Bài tập Triết học – buổi 10/11",
     "due_at": "2026-11-15T08:00:00+07:00", "due_has_time": true,
     "important": false, "alarms_at": ["2026-11-15T07:00:00+07:00"]}
  ],
  "digests": [
    {"sync_key": "digest:2026-11-16", "fingerprint": "77e0…", "date": "2026-11-16",
     "title": "Hôm nay: Ca 1 Giải tích A101 · Ca 3 Vật lý B203 · 1 task đến hạn",
     "notes": "Ca 1 (06:45): Giải tích – A101\nCa 3 (13:00): Vật lý – B203\nTask: 1 đến hạn hôm nay, 0 quá hạn",
     "alarm_at": "2026-11-16T05:00:00+07:00"}
  ]
}
```

**Phạm vi mục trong feed**:
- `events`: buổi học **không bị huỷ** và buổi thi (FR-064), `start_at >= đầu ngày hôm nay`.
  - `alarms_minutes_before` là danh sách phút báo trước theo
    [quy tắc mốc nhắc](../data-model.md#quy-tắc-mốc-nhắc-fr-022-fr-068-fr-069): mục thường có 1 phần
    tử, mục quan trọng nhiều phần tử (buổi thi quan trọng mặc định `[10080, 1440, 180, 60, 15]`),
    `[]` nếu đã tắt nhắc.
  - Tiêu đề buổi thi là "Thi: <tên học phần>"; `location` là phòng thi (có thể `null`).
  - `important = true` thì tiêu đề có tiền tố "★ " (FR-070).
- `reminders`: task **chưa hoàn thành** có `due_date`, kể cả quá hạn trong 7 ngày gần nhất.
  - `alarms_at` là danh sách thời điểm tuyệt đối (sắp tăng dần), `[]` nếu task đã tắt nhắc.
  - `due_has_time = false` thì ghi hạn theo ngày; `alarms_at` lúc `date_only_task_reminder_time`.
  - `important = true` thì `EKReminder.priority = 1` (cao, FR-070).
- `digests`: bản tóm tắt của `today … today + 13` không trống, chỉ khi `daily_digest_enabled`
  (FR-065, FR-066). `title` là bản một dòng (hiện trong thông báo), `notes` là các dòng chi tiết.
  Thay đổi so với bản cũ: `alarm_at` của reminder đổi thành danh sách `alarms_at`; agent cũ (0.1.x)
  cần cài lại cùng lúc với backend mới.

**Giới hạn nội dung** (FR-052, constitution IV): chỉ gồm tiêu đề, địa điểm (phòng), thời gian, báo
trước, mức quan trọng và bản tóm tắt (ca, tên môn/học phần, giờ, phòng, số lượng task). Không gửi
ghi chú, tiêu đề task trong bản tóm tắt, giảng viên, mã lớp, nhãn, số báo danh, hình thức thi hay
ảnh.

`fingerprint` = SHA-256 của các trường nội dung ở trên, để agent biết mục nào cần cập nhật.

## 3. Báo trạng thái

`PUT /api/sync/agent-status`

```json
{"permission": "granted|denied|unknown", "icloud_source": "icloud|local_only|unknown",
 "last_synced_revision": 812, "last_error": null, "agent_version": "1.0.0"}
```

Trả `204`. Backend ghi thêm `last_seen_at = now()`.

## 4. Hành vi bắt buộc của agent

| Tình huống | Hành vi |
|------------|---------|
| `sync_enabled = true`, chưa có quyền | Xin quyền đầy đủ cho Lịch và Lời nhắc; bị từ chối thì báo `permission: denied` và không ghi gì |
| Lần đầu có quyền | Tạo lịch và danh sách lời nhắc tên "Lịch Học Cá Nhân" trong nguồn iCloud (nếu không có thì nguồn cục bộ và báo `local_only`). Lưu `calendarIdentifier` vào `~/Library/Application Support/LichHocAgent/state.json` |
| Mỗi lần nhận feed | Đối chiếu theo `sync_key`, đọc từ trường `URL` của mục (`lichhoc://session/123`). Thiếu thì tạo; lệch `fingerprint` thì cập nhật; mục trong lịch hoặc danh sách của app mà không có trong feed thì xoá. Commit một lần |
| Lịch hoặc danh sách của app bị người dùng xoá | Tạo lại ở vòng sau |
| Mục do người dùng tự sửa trong Lịch | Ghi đè theo feed (agent luôn ghi khi `fingerprint` lưu cục bộ khác feed, hoặc nội dung thực tế lệch) |
| `sync_enabled` chuyển sang `false` | Xoá lịch và danh sách lời nhắc của app, xoá `state.json`, rồi tiếp tục long-poll (FR-054) |
| Sang ngày mới (theo giờ máy) | Lấy lại feed và đối chiếu toàn phần, để cửa sổ bản tóm tắt trượt sang ngày mới và xoá bản tóm tắt của ngày đã qua |
| Backend không phản hồi | Thử lại với thời gian chờ tăng dần 30 giây → 5 phút; **không** xoá mục đã ghi |
| Phạm vi ghi | Chỉ thao tác trên đúng hai `calendarIdentifier` trong `state.json`. Không đọc, sửa hay xoá lịch hoặc danh sách khác (FR-052) |

## 5. Ánh xạ sang EventKit

| Feed | EventKit |
|------|----------|
| event | `EKEvent`: `title`, `location`, `startDate`, `endDate`, `URL = lichhoc://session/{id}` hoặc `lichhoc://exam/{id}`, mỗi phần tử của `alarms_minutes_before` là một `addAlarm(EKAlarm.alarmWithRelativeOffset_(-60 × phút))` |
| reminder | `EKReminder`: `title`, `dueDateComponents` (có hoặc không có giờ), `URL = lichhoc://task/{id}`, `priority = 1` nếu `important` (ngược lại 0), mỗi phần tử `alarms_at` là một `addAlarm(EKAlarm.alarmWithAbsoluteDate_(…))` |
| digest | `EKEvent` cả ngày (`allDay = True`, `startDate = endDate = date`) trong lịch "Lịch Học Cá Nhân": `title`, `notes`, `URL = lichhoc://digest/{date}`, `addAlarm(EKAlarm.alarmWithAbsoluteDate_(alarm_at))`; không có `location` |
| ghi | `saveEvent_span_commit_error_(…, EKSpanThisEvent, False, None)` / `saveReminder_commit_error_(…, False, None)`, sau cùng `commit_()` |
