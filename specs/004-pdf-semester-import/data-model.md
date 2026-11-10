# Data Model: Nhập học kỳ từ file PDF thời khoá biểu chính thức

**Feature**: [spec.md](spec.md) · **Research**: [research.md](research.md)

PostgreSQL 16, giữ quy ước hiện có (`IdMixin`, `TimestampMixin`, `ci_key`, `fold_key`, giờ Việt Nam). Hai migration
mới: `0010_subject_schedules`, `0011_periods_canonical_names`.

## Thay đổi: `subjects`

| Cột | Thay đổi | Ghi chú |
|-----|----------|---------|
| `course_code` | **thêm** `TEXT NULL` | Mã học phần, ví dụ `CSE703016`; môn tạo tay hoặc từ ảnh có thể rỗng |
| `credits` | **thêm** `SMALLINT NULL`, CHECK `credits BETWEEN 0 AND 30` | Số tín chỉ |
| `weekdays`, `start_date`, `end_date`, `start_shift_id`, `end_shift_id`, `start_time`, `end_time`, `room` | **chuyển** sang `subject_schedules` rồi xoá khỏi `subjects` | Kèm các CHECK liên quan (`ck_subjects_weekdays`, `ck_subjects_shift_pair`, `ck_subjects_times`, `ck_subjects_dates`) |
| `name`, `class_code`, `lecturer`, `color`, `reminder_minutes`, `is_important`, `semester_id`, nhãn | giữ nguyên | |

Khoảng ngày của môn (dùng khi sửa học kỳ, FR-036/037 của 001) = [min `start_date`, max `end_date`] của các quy
tắc, tính khi cần, không lưu.

Ràng buộc nghiệp vụ: môn có ít nhất 1 quy tắc (kiểm tra ở service, vì CHECK không diễn đạt được qua bảng).

## Mới: `subject_schedules` (quy tắc lặp hằng tuần)

| Cột | Kiểu | Ràng buộc | Ghi chú |
|-----|------|-----------|---------|
| `id` | BIGINT PK | | |
| `subject_id` | BIGINT | FK `subjects.id` ON DELETE CASCADE, index | |
| `position` | SMALLINT | ≥ 0, UNIQUE (`subject_id`, `position`) | Thứ tự hiển thị; khi hai quy tắc trùng ngày thì quy tắc đứng trước thắng |
| `weekdays` | SMALLINT[] | ≥ 1 phần tử, ⊆ {1…7} | Nhập PDF luôn 1 thứ; quy tắc tạo tay có thể nhiều thứ (giữ tương thích môn cũ) |
| `start_date`, `end_date` | DATE | `end_date >= start_date` | |
| `start_shift_id`, `end_shift_id` | BIGINT NULL | FK `shifts.id` ON DELETE SET NULL; cả hai cùng NULL hoặc cùng có | Gắn ca/dãy ca |
| `start_time`, `end_time` | TIME | `end_time > start_time` | Luôn có giá trị (bản sao giờ ca khi gắn ca) |
| `period_from`, `period_to` | SMALLINT NULL | cả hai cùng NULL hoặc `1 ≤ period_from ≤ period_to ≤ 30` | Khoảng tiết gốc từ PDF, để hiển thị "Tiết 1–2" |
| `room` | TEXT NULL | | Phòng của quy tắc |
| `created_at`, `updated_at` | TIMESTAMPTZ | | |

Validation (service + pydantic): `weekdays` không trùng phần tử; đúng một trong hai: `shift` hoặc cặp giờ tuỳ
chỉnh (như `SubjectInput` hiện tại); khoảng ngày nằm trong học kỳ của môn.

## Thay đổi: `class_sessions`

| Cột | Thay đổi | Ghi chú |
|-----|----------|---------|
| `schedule_id` | **thêm** `BIGINT NULL`, FK `subject_schedules.id` ON DELETE SET NULL, index | Quy tắc sinh ra buổi. NULL chỉ xảy ra với buổi được giữ lại sau khi quy tắc bị xoá (buổi đã qua hoặc có ngoại lệ, R9) |

Không đổi gì khác: ngoại lệ (`is_cancelled`, `time_overridden`, `room_overridden`, `original_date`) giữ nguyên ý nghĩa.

### Sinh buổi (tổng quát hoá `plan_regeneration`)

Đầu vào: buổi hiện có của môn; ánh xạ `ngày → (schedule_id, start_time, end_time, room)` lấy từ mọi quy tắc
(`generate_dates` cho từng quy tắc; ngày trùng thì quy tắc có `position` nhỏ hơn thắng và sinh cảnh báo); tham số
`keep_before: date | None`.

- Ngày mong muốn chưa có buổi → tạo (gắn `schedule_id`).
- Buổi khớp ngày (`lock_date`) → cập nhật giờ/phòng/`schedule_id` theo quy tắc, trừ phần đã sửa riêng; buổi đã huỷ
  giữ nguyên.
- Buổi không còn ngày mong muốn → xoá nếu không có ngoại lệ; có ngoại lệ → `exception_conflicts` (sửa tay: hỏi xác
  nhận như hiện nay; nhập PDF: giữ lại, `schedule_id = NULL`, cảnh báo).
- `keep_before` (chỉ nhập PDF dùng, bằng hôm nay): buổi có `date < keep_before` không bị tạo/sửa/xoá.

## Mới: `periods` (bảng tiết)

| Cột | Kiểu | Ràng buộc | Ghi chú |
|-----|------|-----------|---------|
| `number` | SMALLINT PK | `1 ≤ number ≤ 30` | Số tiết |
| `start_time`, `end_time` | TIME | `end_time > start_time` | |
| `is_manual` | BOOLEAN | mặc định `false` | `true` khi người dùng sửa tay; đổi giờ ca không ghi đè |
| `updated_at` | TIMESTAMPTZ | | |

Ràng buộc nghiệp vụ (service): tiết `n` kết thúc ≤ giờ bắt đầu tiết `n+1` nếu cả hai tồn tại (cảnh báo, không chặn).

Seed trong migration (từ ca hiện có lúc chạy migration, theo FR-012/FR-013):

| Tiết | Mặc định (với ca mặc định) |
|------|----------------------------|
| 1–3 (Ca 1 06:45–09:25) | 06:45–07:35, 07:40–08:30, 08:35–09:25 |
| 4–6 (Ca 2 09:30–12:10) | 09:30–10:20, 10:25–11:15, 11:20–12:10 |
| 7–9 (Ca 3 13:00–15:40) | 13:00–13:50, 13:55–14:45, 14:50–15:40 |
| 10–12 (Ca 4 15:45–18:25) | 15:45–16:35, 16:40–17:30, 17:35–18:25 |
| 13–15 | không có |
| 16–18 | 21:05–21:20, 21:20–21:40, 21:40–22:00 |

Ca có độ dài khác 160 phút: chia (độ dài − 10 phút) cho 3, làm tròn phút, tiết cuối kết thúc đúng giờ kết thúc ca.
Ca thứ k chỉ ứng với tiết 3k−2…3k khi k ≤ 4 (ca thêm sau không tự sinh tiết).

## Mới: `canonical_subject_names` (tên môn chuẩn)

| Cột | Kiểu | Ràng buộc | Ghi chú |
|-----|------|-----------|---------|
| `id` | BIGINT PK | | |
| `name` | TEXT | 1–200 ký tự; UNIQUE theo `lower(name)` (chỉ mục biểu thức, khớp `ci_key`) | Tên đúng như trong PDF |
| `course_code` | TEXT NULL | | |
| `created_at` | TIMESTAMPTZ | | |

Không có khoá ngoại tới `subjects`: tên vẫn giữ khi môn bị xoá (FR-028). Xoá toàn bộ trong Cài đặt.

## Thực thể tạm (không lưu): `TimetablePdfPreview`

Chỉ tồn tại trong bộ nhớ và trong phản hồi API; không có thông tin cá nhân (R6).

```text
TimetablePdfPreview
├── semester: {suggested_name, start_date, end_date,
│              choice: "use" | "extend" | "create" | "conflict", semester_id?, conflicts?}
├── subjects: [PreviewSubject]
└── warnings: [{code, message}]

PreviewSubject
├── course_code, name, class_code, credits
├── status: "new" | "unchanged" | "changed"; existing_subject_id?; diff: [{field, before, after}]
├── suggested_tags: ["e_learning"]?        # R/FR-027
├── selected: bool                          # unchanged → false
└── schedules: [PreviewSchedule]

PreviewSchedule
├── weekday (1–7), start_date, end_date
├── period_from, period_to
├── shift: {start_shift_id, end_shift_id} | null, start_time | null, end_time | null
├── room
├── session_count                           # số buổi sẽ tạo trong khoảng
├── problems: [{field, level: "error" | "warning", message}]
└── selected: bool
```

## Migration `0010_subject_schedules`

1. Tạo `subject_schedules`; thêm `subjects.course_code`, `subjects.credits`, `class_sessions.schedule_id`.
2. Với mỗi môn: chèn 1 quy tắc (`position = 0`) chép từ các cột lịch của môn; gán `schedule_id` cho mọi buổi của
   môn.
3. Xoá các cột lịch và CHECK cũ khỏi `subjects`.
4. `downgrade`: thêm lại cột, chép từ quy tắc `position` nhỏ nhất của mỗi môn (mất các quy tắc còn lại — ghi rõ
   trong docstring), xoá bảng và cột mới.

Bản sao lưu cũ khôi phục vào app mới: luồng khôi phục của feature 003 chạy `upgrade` sau khi nạp dump, nên
migration này tự áp dụng cho dữ liệu cũ.

## Migration `0011_periods_canonical_names`

Tạo `periods` (seed như bảng trên) và `canonical_subject_names`.
