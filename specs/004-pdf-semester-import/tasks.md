---

description: "Task list — Nhập học kỳ từ file PDF thời khoá biểu chính thức"
---

# Tasks: Nhập học kỳ từ file PDF thời khoá biểu chính thức

**Input**: Design documents from `specs/004-pdf-semester-import/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Bắt buộc — spec FR-030 (test bằng PDF giả lập) và constitution Nguyên tắc II. Viết test trước, chạy thấy
đỏ, rồi mới cài đặt.

**Organization**: Theo user story của spec. Mọi lệnh test chạy qua `./scripts/test.sh` (backend trong Docker, mount
code hiện tại). Cuối mỗi phase: `./scripts/test.sh` xanh → commit (không thêm dòng Co-Authored-By hay "Generated
with Claude Code", xem `CLAUDE.md`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: chạy song song được (khác file, không phụ thuộc task chưa xong)
- **[Story]**: US1…US5 theo spec
- Đường dẫn tính từ gốc repo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Phụ thuộc mới và dữ liệu thử giả lập.

- [X] T001 Thêm `"pdfplumber>=0.11,<0.12"` vào `dependencies` và `"reportlab>=4"` vào `optional-dependencies.dev` trong `backend/pyproject.toml`
- [X] T002 Thêm gói `fonts-dejavu-core` vào bước `apt-get install` trong `backend/Dockerfile` (chỉ để script sinh PDF giả lập có phông tiếng Việt), rồi `docker compose build backend`
- [X] T003 Viết script sinh PDF giả lập `samples/synthetic/make_timetable_pdf.py` bằng reportlab + DejaVu Sans: dựng đúng bố cục ở `specs/004-pdf-semester-import/contracts/timetable-pdf-format.md` (phần đầu có trường, tiêu đề, dòng "Học kỳ 2 Năm học 2026 - 2027 Đợt 2", họ tên `Nguyễn Văn Test`, mã sinh viên `21010999`, lớp `K99-TEST_1`, ngành; bảng có đường kẻ, cột STT, Mã HP, Lớp học phần, Số TC, Thứ 2…CN, Thời gian, Học phí; 17 hàng với cùng nội dung lịch như bảng đáp án; chữ ngắt dòng giữa mã HP "FFS7010/69", phòng "A6-1/03/(PC))", "A6-301.30/2 (PC))", "Sân/bóng đá", "ONLINE-/Elearning"; dòng "Tổng cộng", "Viết bằng chữ", ngày lập, chữ ký); tham số sinh thêm bản 2 trang (bảng tràn sang trang 2, không lặp tiêu đề) và các file lỗi: PDF chỉ có ảnh (không chữ), PDF có mật khẩu, PDF có chữ nhưng không phải thời khoá biểu
- [X] T004 Chạy script trong container, commit kết quả vào `backend/tests/fixtures/timetables/` với tên `tkb-synthetic-01.pdf`, `tkb-synthetic-2pages.pdf`, `tkb-no-text.pdf`, `tkb-encrypted.pdf`, `tkb-not-timetable.pdf`; ghi đáp án máy đọc được vào `backend/tests/fixtures/timetables/tkb-synthetic-01.expected.json` (8 môn, 17 quy tắc, `must_not_appear: ["Nguyễn Văn Test", "21010999", "K99-TEST_1"]`); thêm mục mô tả vào `samples/synthetic/README.md`
- [X] T005 [P] Thêm hàm `load_pdf(name)` (đọc bytes fixture PDF) vào `backend/tests/ocr_helpers.py`

**Checkpoint**: image có pdfplumber; fixture PDF giả lập sẵn sàng; không có PDF thật trong git (`git ls-files samples` chỉ có `samples/synthetic/`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Môn nhiều quy tắc lặp (R7, FR-020, FR-020a) và lõi bảng tiết (R8). Mọi user story phụ thuộc phase này.

**⚠️ CRITICAL**: Giữ toàn bộ test hiện có xanh sau phase này (mọi chỗ đọc lịch của môn chuyển sang quy tắc).

### Tests (viết trước)

- [X] T006 [P] Test hàm thuần sinh buổi nhiều quy tắc trong `backend/tests/unit/test_recurrence_schedules.py`: hai quy tắc khác khoảng ngày (kỳ nghỉ ở giữa không có buổi); hai quy tắc trùng ngày → quy tắc `position` nhỏ hơn thắng + cảnh báo; buổi đã huỷ/sửa giờ/sửa phòng/đã dời giữ như cũ; buổi ngoài lịch mới có ngoại lệ → `exception_conflicts`; `keep_before` không tạo/sửa/xoá buổi có ngày nhỏ hơn
- [X] T007 [P] Test migration trong `backend/tests/integration/test_migration_0010.py`: dựng dữ liệu ở revision `0009_ca2_default` (môn 2 thứ gắn ca, môn giờ tuỳ chỉnh có phòng, buổi đã huỷ, buổi đã dời, buổi sửa phòng), `upgrade` → mỗi môn đúng 1 quy tắc chép đủ trường, mọi buổi có `schedule_id` đúng, ngoại lệ giữ nguyên; `downgrade` → cột cũ có lại giá trị
- [X] T008 [P] Test API môn nhiều quy tắc trong `backend/tests/integration/test_subject_schedules_api.py`: POST với 2 quy tắc sinh đúng buổi; PATCH thay danh sách (giữ `id` → cập nhật, thiếu → xoá, mới → tạo); không cho 0 quy tắc (400 `schedules`); lỗi theo vị trí `schedules[1].end_time`; quy tắc ngoài học kỳ → 400; bulk mỗi dòng 1 quy tắc; phản hồi có `course_code`, `credits`, `schedules`
- [X] T009 [P] Test bảng tiết trong `backend/tests/unit/test_periods.py`: tiết mặc định từ 4 ca mặc định khớp bảng ở `data-model.md` (tiết 1 06:45–07:35, tiết 2 07:40–08:30, tiết 3 08:35–09:25, tiết 4 09:30–10:20 … tiết 12 17:35–18:25; 16–18 = 21:05–21:20, 21:20–21:40, 21:40–22:00); ca dài khác 160 phút chia đều, tiết cuối kết thúc đúng giờ ca; `periods_to_time` cho 1–3 → Ca 1, 4–6 → Ca 2, 1–6 → Ca 1–2, 1–2 → 06:45–08:30 tuỳ chỉnh có `period_from/to`, 16–18 → 21:05–22:00, 13–15 → lỗi "Chưa có giờ cho tiết 13–15"; đổi giờ ca tính lại tiết `is_manual = false`, giữ tiết `is_manual = true`

### Implementation

- [X] T010 Tạo model `SubjectSchedule` trong `backend/app/models/subject_schedule.py` đúng [data-model](data-model.md#mới-subject_schedules-quy-tắc-lặp-hằng-tuần): `subject_id` FK `subjects.id` ON DELETE CASCADE; `position` SMALLINT "≥ 0, UNIQUE (`subject_id`, `position`)"; `weekdays` SMALLINT[] "≥ 1 phần tử, ⊆ {1…7}"; `start_date`, `end_date` "`end_date >= start_date`"; `start_shift_id`, `end_shift_id` "FK `shifts.id` ON DELETE SET NULL; cả hai cùng NULL hoặc cùng có"; `start_time`, `end_time` "`end_time > start_time`"; `period_from`, `period_to` "cả hai cùng NULL hoặc `1 ≤ period_from ≤ period_to ≤ 30`"; `room` TEXT NULL; đăng ký trong `backend/app/models/__init__.py`
- [X] T011 Sửa `backend/app/models/subject.py`: thêm `course_code` TEXT NULL, `credits` SMALLINT NULL "CHECK `credits BETWEEN 0 AND 30`", quan hệ `schedules` (order_by `position`, cascade delete-orphan); bỏ các cột lịch phẳng và CHECK `ck_subjects_weekdays`, `ck_subjects_shift_pair`, `ck_subjects_times`, `ck_subjects_dates`; thêm property `date_span` (min/max ngày của quy tắc). Sửa `backend/app/models/class_session.py`: thêm `schedule_id` BIGINT NULL FK `subject_schedules.id` ON DELETE SET NULL, index
- [X] T012 Viết migration `backend/migrations/versions/0010_subject_schedules.py` (down_revision `0009_ca2_default`) theo [data-model › Migration 0010](data-model.md#migration-0010_subject_schedules): tạo bảng, thêm cột, chép mỗi môn thành 1 quy tắc `position = 0`, gán `schedule_id` cho buổi, xoá cột/CHECK cũ; `downgrade` chép ngược từ quy tắc `position` nhỏ nhất (ghi rõ mất các quy tắc khác trong docstring)
- [X] T013 Tổng quát hoá `plan_regeneration` trong `backend/app/services/recurrence.py`: nhận `desired: dict[date, DesiredSession(schedule_id, start_time, end_time, room)]` và `keep_before: date | None`; thêm hàm thuần `desired_sessions(schedules) -> (dict, warnings)` (gọi `generate_dates` cho từng quy tắc, quy tắc đứng trước thắng khi trùng ngày); `SessionUpdate` thêm `schedule_id`
- [X] T014 Sửa `backend/app/services/subjects.py`: `resolve_subject` / `create_subject` / `create_bulk` / `create_many` / `update_subject` nhận `schedules` (giải ca hoặc giờ cho từng quy tắc bằng `resolve_times`, ngày bằng `resolve_dates` theo học kỳ, lỗi theo `schedules[i].field`), PATCH thay danh sách theo `id`, bắt buộc ≥ 1 quy tắc; `regenerate_sessions(subject, force=False, keep_before=None)` dùng `desired_sessions` và gán `schedule_id` khi tạo/cập nhật; `find_time_conflicts` duyệt theo buổi như cũ
- [X] T015 [P] Sửa `backend/app/schemas/subjects.py`: thêm `ScheduleIn` (`id?`, `weekdays` không trùng, `start_date?`, `end_date?`, `shift?`, `start_time?`, `end_time?`, `period_from?`, `period_to?`, `room?`) và `ScheduleOut`; `SubjectFields`/`SubjectIn`/`SubjectPatch` thay trường lịch phẳng bằng `schedules: list[ScheduleIn]` (`min_length=1`), thêm `course_code`, `credits` (`ge=0, le=30`); serializer môn trong `backend/app/schemas/subjects.py` / `backend/app/api/subjects.py` trả `schedules`, `course_code`, `credits`; serializer **buổi học** (`backend/app/schemas/subjects.py`, chỗ đang gọi `shift_label(subject.start_shift, subject.end_shift)`) lấy nhãn ca từ quy tắc của buổi (`session.schedule`, `None` khi `schedule_id` rỗng hoặc buổi đã sửa giờ)
- [X] T016 [P] Chuyển các chỗ đọc lịch phẳng của môn sang quy tắc: `backend/app/services/semesters.py` (kiểm tra/clamp khoảng ngày môn khi sửa học kỳ dùng `date_span` và clamp từng quy tắc), `backend/app/services/shifts.py` (môn dùng ca = có quy tắc dùng ca; đổi giờ ca cập nhật `start_time/end_time` của quy tắc rồi `regenerate_sessions`; xoá ca chuyển quy tắc sang giờ tuỳ chỉnh), `backend/app/services/digest.py` (nhãn ca của buổi trong bản tóm tắt lấy từ `session.schedule` thay cho `subject.start_shift/end_shift`). Kiểm tra bằng `grep -rnE "subject\.(room|weekdays|start_date|end_date|start_time|end_time|start_shift|end_shift)" backend/app` không còn kết quả ngoài model
- [X] T017 Sửa commit nhập ảnh `_commit_week` trong `backend/app/services/imports.py` để mỗi dòng tạo item có `schedules: [một quy tắc]` (thứ, khoảng ngày theo `repeat`, ca hoặc giờ, phòng); `backend/tests/integration/test_imports_api.py` và `backend/tests/integration/test_imports_week_exam_api.py` PHẢI xanh với dạng `schedules` (sửa các chỗ kiểm tra trường lịch phẳng của môn, ví dụ `weekdays`, `start_date`, thành kiểm tra `schedules[0]`); sửa `backend/scripts_validate.py` gọi API dạng mới
- [X] T018 Tạo model `Period` trong `backend/app/models/period.py` ("`number` SMALLINT PK `1 ≤ number ≤ 30`", "`end_time > start_time`", `is_manual` mặc định `false`, `updated_at`) và model `CanonicalSubjectName` trong `backend/app/models/canonical_name.py` ("`name` 1–200 ký tự; UNIQUE theo `lower(name)`", `course_code` NULL, `created_at`); migration `backend/migrations/versions/0011_periods_canonical_names.py` tạo hai bảng và seed tiết 1–12 từ ca hiện có (theo FR-012) + 16–18 (FR-013)
- [X] T019 Tạo `backend/app/services/periods.py`: hàm thuần `default_periods(shifts)`, `periods_to_time(period_from, period_to, periods, shifts) -> ShiftRef | (start, end) | lỗi`; hàm `recompute_for_shift(shift)` cập nhật tiết `is_manual = false` của ca (gọi trong `update_shift` ở `backend/app/services/shifts.py`, cùng transaction)
- [X] T020 [P] Frontend: cập nhật kiểu `Subject`/`SubjectInput` có `schedules`, `course_code`, `credits` trong `frontend/src/api/types.ts` và `frontend/src/api/subjects.ts`; hàm thuần `describeSchedules(subject)` trong `frontend/src/lib/format.ts` (một quy tắc → "T2 · Ca 2 · Sân bóng đá"; nhiều quy tắc → "3 lịch · 30/11/2026 – 28/02/2027") dùng ở `frontend/src/features/subjects/SubjectsScreen.tsx`
- [X] T021 Frontend (FR-020a): thành phần `frontend/src/features/subjects/ScheduleRows.tsx` (mỗi hàng: `WeekdayPicker`, từ ngày–đến ngày, `ShiftPicker` hoặc giờ tuỳ chỉnh, phòng, nút xoá ẩn khi còn 1 hàng, nút "Thêm lịch" chép hàng cuối, lỗi `schedules[i].…` dưới hàng); dùng trong `frontend/src/features/subjects/SubjectForm.tsx` (thêm ô mã HP, số tín chỉ); `frontend/src/features/subjects/BulkSubjectForm.tsx` gửi `schedules: [một quy tắc]`; chuỗi trong `frontend/src/i18n/vi.ts`
- [X] T022 [P] Test Vitest `frontend/tests/scheduleRows.test.tsx`: thêm/xoá/sửa hàng, không xoá được hàng cuối, gửi đúng `schedules`, hiện lỗi theo hàng; cập nhật test hiện có của form môn và màn Môn học cho dạng mới

**Checkpoint**: `./scripts/test.sh` xanh (kể cả test cũ); app chạy như trước, form môn có danh sách lịch. Commit.

---

## Phase 3: User Story 1 - Nhập cả học kỳ từ file PDF (Priority: P1) 🎯 MVP

**Goal**: Thả/chọn/dán PDF → màn "Nhập lịch" hiện bảng xem trước theo môn → Lưu tạo môn, quy tắc, buổi và học kỳ.

**Independent Test**: Trên DB trống, gửi `tkb-synthetic-01.pdf` tới preview → 8 môn, 17 quy tắc khớp đáp án; commit →
số buổi đúng, không buổi nào trong 25/01–14/02/2027; không có giá trị cá nhân giả ở bất kỳ đâu.

### Tests for User Story 1

- [ ] T023 [P] [US1] Test luật ghép và đọc ô trong `backend/tests/unit/test_pdf_cells.py` theo bảng ví dụ của `contracts/timetable-pdf-format.md`: mã HP nối liền ("FFS7010"+"69" → "FFS701069"); lớp học phần nối bằng dấu cách rồi tách tên/mã lớp; ô thứ "1 - 3"/"(A6-1"/"03"/"(PC))" → (1, 3, "A6-103 (PC)"), "A6-301.30"/"2 (PC))" → "A6-301.302 (PC)", "Sân"/"bóng đá)" → "Sân bóng đá", "(ONLINE-"/"Elearning)" → "ONLINE-Elearning"; ô thiếu phòng; ô không đọc được tiết; ngày: 2 ngày, 1 ngày, kết thúc < bắt đầu; dòng học kỳ "Học kỳ 2 Năm học 2026 - 2027 Đợt 2" → "HK2 2026–2027"
- [ ] T024 [P] [US1] Test bố cục trong `backend/tests/unit/test_pdf_layout.py` trên `tkb-synthetic-01.pdf` và `tkb-synthetic-2pages.pdf`: tìm hàng tiêu đề, khoảng x của 7 cột thứ theo toạ độ chữ tiêu đề, 17 hàng dữ liệu, dừng trước "Tổng cộng", bản 2 trang đủ hàng; từ thuộc phần đầu (họ tên, mã SV, lớp) và cột Học phí không có trong kết quả
- [ ] T025 [P] [US1] Test bản xem trước trong `backend/tests/unit/test_pdf_preview.py`: gộp hàng thành 8 môn theo (`course_code`, `class_code`), 17 quy tắc khớp `tkb-synthetic-01.expected.json`; "N02" và "N02.TH1" là 2 môn; tiết → ca/giờ qua `periods_to_time`; `session_count` đúng; `choose_semester` (hàm thuần): chứa trọn → `use` (chọn học kỳ ngắn nhất), không chồng → `create` với tên "HK2 2026–2027" và khoảng 30/11/2026–28/02/2027, chồng một phần một học kỳ → `extend`, chồng hai → `conflict`
- [ ] T026 [P] [US1] Test API trong `backend/tests/integration/test_timetable_import_api.py`: preview `tkb-synthetic-01.pdf` (8 môn, 17 quy tắc, không ghi gì vào CSDL); mã lỗi đúng contract cho file > 20 MB (413 `file_too_large`), không phải PDF (415 `unsupported_file`), `tkb-encrypted.pdf` (422 `pdf_encrypted`), PDF hỏng (422 `pdf_unreadable`), > 20 trang (422 `pdf_too_long`), `tkb-no-text.pdf` (422 `pdf_no_text`), `tkb-not-timetable.pdf` (422 `pdf_not_timetable`); commit `choice: create` → đúng số môn, số buổi (= số ngày đúng thứ trong các khoảng), 0 buổi trong 25/01–14/02/2027, học kỳ mới; commit lỗi giữa chừng (một quy tắc sai) → 400 với `subjects[i].schedules[j].field` và CSDL không đổi (FR-025); bỏ chọn quy tắc/môn thì không tạo; commit hai môn trùng giờ cùng ngày → 200 kèm cảnh báo trùng giờ trong `warnings` (như khi thêm môn bằng tay)
- [ ] T027 [P] [US1] Test quyền riêng tư trong `backend/tests/integration/test_timetable_import_privacy.py`: sau preview + commit, `must_not_appear` không có trong JSON phản hồi, trong log đã bắt (`caplog`), và trong mọi cột văn bản của CSDL (SC-006); không có file mới trong `/tmp` sau khi xử lý

### Implementation for User Story 1

- [ ] T028 [P] [US1] `backend/app/pdfimport/reader.py`: mở PDF từ `bytes` trong bộ nhớ, kiểm tra theo thứ tự R14 (`%PDF-`, mật khẩu, hỏng, > 20 trang, không có ký tự) và ném lỗi có mã; trả danh sách trang gồm từ (`extract_words(x_tolerance=1.5)`) và đường kẻ dọc/ngang; không ghi đĩa, không log nội dung
- [ ] T029 [US1] `backend/app/pdfimport/layout.py`: `find_header` (đủ 7 cột thứ + "Thời gian", so khớp bỏ dấu, chịu ngắt dòng), `column_ranges` (theo toạ độ chữ tiêu đề, khớp vào đường kẻ dọc gần nhất), `split_rows` (theo đường kẻ ngang; dự phòng theo STT/cặp ngày), gán từ vào ô theo tâm, dừng ở "Tổng cộng", bỏ cột STT/Học phí; `find_semester_line` chỉ trả dòng "Học kỳ … Năm học …"; mọi từ khác ở phần đầu bị bỏ ngay (R6)
- [ ] T030 [US1] `backend/app/pdfimport/cells.py`: `join_cell_lines(lines, kind)` theo R4 cho `course_code`, `class_label`, `day_cell`, `dates`; `parse_day_cell` (regex `^(\d{1,2})\s*-\s*(\d{1,2})\s*\((.*)\)$`, chuẩn hoá " (PC)"); `parse_dates`; `parse_semester_name`; dùng lại `split_class_label` của `backend/app/ocr/fields.py`
- [ ] T031 [US1] `backend/app/pdfimport/preview.py`: hàm thuần `build_timetable_preview(rows, semester_line, ctx)` → `TimetablePdfPreview` đúng [data-model](data-model.md#thực-thể-tạm-không-lưu-timetablepdfpreview): gộp môn, quy tắc (1 thứ mỗi ô), đổi tiết bằng `periods_to_time`, `session_count`, `problems` (error: thiếu/ngược ngày, thiếu giờ; warning: thiếu phòng, không có buổi nào → `selected = false`, hai quy tắc trùng ngày-giờ), `choose_semester`; ở US1 mọi môn là `new`
- [ ] T032 [US1] Schema `backend/app/schemas/timetable_import.py` (preview out, commit in theo `contracts/rest-api.md`: `semester.choice` ∈ `use`/`extend`/`create`, chỉ môn/quy tắc được chọn) và service `backend/app/services/timetable_import.py`: `preview(data)` dựng ngữ cảnh (ca, tiết, học kỳ) rồi gọi các hàm thuần; `commit(payload)` trong một transaction: tạo/mở rộng/dùng học kỳ, tạo môn qua `create_many` với `schedules`, `bump_revision`, trả `{semester_id, created_subjects, updated_subjects, created_sessions, updated_sessions, skipped_sessions, kept_exception_sessions, warnings}`
- [ ] T033 [US1] API `backend/app/api/timetable_import.py`: `POST /imports/timetable-pdf/preview` (multipart `file`, giới hạn 20 MB dùng chung `MAX_IMAGE_BYTES`, đọc vào bộ nhớ) và `POST /imports/timetable-pdf/commit`; ánh xạ lỗi reader sang mã/HTTP của contract; đăng ký blueprint trong `backend/app/api/__init__.py`; thêm mục vào `specs/001-task-class-scheduler/contracts/rest-api.md` trỏ tới contract 004
- [ ] T034 [P] [US1] Frontend API `frontend/src/api/timetableImport.ts` (kiểu `TimetablePdfPreview`, `usePreviewTimetablePdf`, `useCommitTimetablePdf`) và hàm thuần trạng thái `frontend/src/features/imports/timetablePreviewState.ts` (chọn/bỏ môn, quy tắc; sửa ô; `canSaveTimetable` = có phần được chọn và không còn lỗi; dựng commit payload chỉ gồm phần được chọn)
- [ ] T035 [US1] Frontend `frontend/src/features/imports/TimetablePreview.tsx` theo `contracts/ui.md`: dải học kỳ (đổi lựa chọn), khối môn (ô chọn, tên sửa được, mã HP, mã lớp, tín chỉ, nhãn, huy hiệu trạng thái), bảng quy tắc (Thứ, Từ–Đến DD/MM/YYYY, Tiết, Ca/Giờ qua `ShiftPicker`, Phòng, Số buổi) với ô đỏ/vàng kèm lý do; chuỗi trong `frontend/src/i18n/vi.ts`
- [ ] T036 [US1] Đổi màn nhập thành "Nhập lịch" trong `frontend/src/features/imports/ImportScreen.tsx`: nhận `application/pdf` (định dạng "PNG, JPEG, HEIC hoặc PDF, tối đa 20 MB"), PDF → preview PDF và `TimetablePreview`, ảnh → luồng cũ; lưu PDF → thông báo "Đã tạo X môn, cập nhật Y môn (Z buổi học), bỏ qua W buổi đã có."; đổi tên mục điều hướng/nút "Nhập từ ảnh" → "Nhập lịch" ở `frontend/src/i18n/vi.ts` và chỗ dùng
- [ ] T037 [US1] Đổi `frontend/src/features/imports/pendingImage.ts` → `pendingFile.ts` và `usePasteImage.ts` → `usePasteFile.ts` (nhận ảnh và PDF từ `clipboardData.files`); trang Môn học `frontend/src/features/subjects/SubjectsScreen.tsx` nhận thả/dán PDF → chuyển sang màn "Nhập lịch" với file chờ; cập nhật `frontend/tests/pasteImage.test.tsx`
- [ ] T038 [P] [US1] Test Vitest `frontend/tests/timetablePreview.test.tsx` (hiện 8 môn từ dữ liệu mẫu, bỏ chọn quy tắc, sửa phòng, nút Lưu tắt khi có lỗi, payload chỉ gồm phần chọn) và bổ sung `frontend/tests/importScreen.test.tsx` (thả PDF gọi endpoint PDF, ảnh vẫn gọi endpoint ảnh, thông báo lỗi `pdf_no_text`; ⌘V khi clipboard không có ảnh hay PDF → thông báo nhẹ, không gọi API)

**Checkpoint**: US1 chạy độc lập trên DB trống (quickstart A1–A4, A7, A15). Commit.

---

## Phase 4: User Story 2 - Đổi tiết sang giờ theo bảng tiết chỉnh được (Priority: P1)

**Goal**: Xem/sửa bảng tiết trong Cài đặt → Ca học; tiết chưa có giờ được nhập ngay ở bản xem trước và lưu vào bảng tiết.

**Independent Test**: Mở bảng tiết thấy tiết 1–12, 16–18 đúng mặc định; sửa tiết 2 → preview "Tiết 1–2" ra giờ mới; PDF có tiết 13–15 bị chặn Lưu cho tới khi nhập giờ.

### Tests for User Story 2

- [ ] T039 [P] [US2] Test API trong `backend/tests/integration/test_periods_api.py`: GET thứ tự theo `number` kèm `shift_id`; PUT tạo/sửa đặt `is_manual = true`, 400 khi `end_time ≤ start_time` hoặc `number` ngoài 1–30, cảnh báo khi chồng tiết kề; POST reset (tiết thuộc ca về giờ suy từ ca; 16–18 về mặc định; tiết khác bị xoá); DELETE chỉ cho tiết không thuộc ca; PATCH `/shifts/{id}` tính lại tiết chưa sửa tay
- [ ] T040 [P] [US2] Test commit có `save_periods` trong `backend/tests/integration/test_timetable_import_api.py`: quy tắc tiết 13–15 thiếu giờ → preview có lỗi; commit kèm giờ nhập tay và `schedules[j].save_periods: true` → tạo tiết 13–15 trong `periods` (chia theo luật FR-012) và quy tắc dùng giờ đó

### Implementation for User Story 2

- [ ] T041 [US2] API `backend/app/api/periods.py` (`GET /periods`, `PUT /periods/{number}`, `POST /periods/{number}/reset`, `DELETE /periods/{number}`) + schema `backend/app/schemas/periods.py`; đăng ký blueprint; dùng `backend/app/services/periods.py`
- [ ] T042 [US2] Commit nhập PDF nhận cờ `schedules[j].save_periods` (contract REST) cho quy tắc có giờ nhập tay ứng với khoảng tiết chưa có giờ: ghi tiết vào `periods` (`is_manual = true`) trong cùng transaction, trong `backend/app/services/timetable_import.py` và `backend/app/schemas/timetable_import.py`
- [ ] T043 [P] [US2] Frontend `frontend/src/api/periods.ts` và `frontend/src/features/settings/PeriodsTable.tsx` (Tiết · Bắt đầu · Kết thúc · Thuộc ca; dấu "đã chỉnh" + "Về mặc định"; "Thêm tiết" cho 13–30; ghi chú "Dùng để đổi tiết trong file PDF sang giờ."), gắn dưới bảng ca trong `frontend/src/features/settings/ShiftsSettings.tsx`; chuỗi trong `frontend/src/i18n/vi.ts`
- [ ] T044 [US2] Trong `frontend/src/features/imports/TimetablePreview.tsx`: quy tắc thiếu giờ hiện ô vàng "Chưa có giờ cho tiết 13–15", ô nhập giờ và ô chọn "Lưu giờ này vào bảng tiết"; gửi `save_periods`
- [ ] T045 [P] [US2] Test Vitest `frontend/tests/periodsTable.test.tsx` (hiện bảng, sửa giờ gọi PUT, về mặc định gọi reset, lỗi giờ kết thúc trước giờ bắt đầu) và bổ sung `frontend/tests/timetablePreview.test.tsx` cho ô thiếu giờ

**Checkpoint**: Quickstart A5, A6 và kiểm tra tay bước 5. Commit.

---

## Phase 5: User Story 3 - Nhập lại PDF không tạo trùng, cập nhật môn đã có (Priority: P2)

**Goal**: Nhập lại nhận ra môn đã có (kể cả môn tạo từ ảnh), chỉ cập nhật phần khác, không đụng buổi đã qua và buổi sửa riêng.

**Independent Test**: Nhập `tkb-synthetic-01.pdf`, lưu; nhập lại → 0 môn/0 buổi mới; nhập bản đổi phòng → buổi tương lai đổi phòng, buổi đã qua và buổi sửa riêng giữ nguyên.

### Tests for User Story 3

- [ ] T046 [P] [US3] Test hàm thuần `match_existing` và `diff_subject` trong `backend/tests/unit/test_pdf_preview.py`: khoá "cùng `ci_key(class_code)` và (cùng `course_code` hoặc cùng `fold_key(name)`)"; hai môn cùng mã lớp "2-2-26(N01)" khác tên không khớp nhầm; trạng thái `unchanged` (mặc định bỏ chọn) / `changed` với danh sách khác biệt (phòng, thứ, giờ, khoảng ngày, thêm/bớt quy tắc)
- [ ] T047 [P] [US3] Test API trong `backend/tests/integration/test_timetable_reimport.py` (đặt `timeutil.now` cố định giữa học kỳ): nhập lại cùng file → 0 môn, 0 buổi mới (SC-005); bản đổi phòng (dựng bằng cách sửa preview trước khi commit) → buổi ngày ≥ hôm nay đổi phòng, buổi < hôm nay giữ, buổi `room_overridden`/đã huỷ giữ, buổi có ngoại lệ ngoài lịch mới được giữ với `schedule_id = NULL` và có trong cảnh báo; môn tạo từ ảnh (nhập `real-week-02` trước) được khớp `changed`, không tạo môn thứ hai, được bổ sung `course_code`, `credits`, tên theo PDF; môn không có trong PDF giữ nguyên; `existing_subject_id` sai khoá → 400

### Implementation for User Story 3

- [ ] T048 [US3] Thêm `match_existing(preview_subject, existing_subjects)` và `diff_subject(existing, preview_subject)` vào `backend/app/pdfimport/preview.py`; service preview nạp môn của học kỳ đích (kèm quy tắc) vào ngữ cảnh và gắn `status`, `existing_subject_id`, `diff`, `selected`
- [ ] T049 [US3] Commit cập nhật môn đã có trong `backend/app/services/timetable_import.py`: tính lại khớp ở server (không tin client), thay quy tắc, cập nhật `name`/`course_code`/`credits`, `regenerate_sessions(subject, force=False, keep_before=timeutil.today())` với nhánh nhập PDF giữ buổi có ngoại lệ ngoài lịch mới (`schedule_id = NULL`, cảnh báo) thay vì 409; đếm `updated_subjects`, `updated_sessions`, `skipped_sessions`, `kept_exception_sessions`
- [ ] T050 [US3] Frontend: huy hiệu "Đã có" (chữ mờ, bỏ chọn sẵn) và "Thay đổi" kèm danh sách "Phòng: A6-501 (PC) → A6-203 (PC)" trong `frontend/src/features/imports/TimetablePreview.tsx`; bổ sung `frontend/tests/timetablePreview.test.tsx`

**Checkpoint**: Quickstart A8–A10. Commit.

---

## Phase 6: User Story 4 - Gắn nhãn E-Learning cho buổi học trực tuyến (Priority: P2)

**Goal**: Phòng có "ONLINE"/"Elearning"/"E-Learning" → đề xuất nhãn E-Learning (chọn sẵn, bỏ được) → deadline tự tạo áp dụng.

**Independent Test**: Preview `tkb-synthetic-01.pdf` → môn "Tích hợp và phân tích dữ liệu lớn (COUR01)" có `suggested_tags: ["e_learning"]`; lưu → môn có nhãn và deadline tự tạo như gắn tay; bỏ nhãn trước khi lưu → không có nhãn.

- [ ] T051 [P] [US4] Test trong `backend/tests/unit/test_pdf_preview.py` (phòng "ONLINE-Elearning", "Elearning", "E-Learning", "online" → đề xuất; "A6-103 (PC)" → không) và `backend/tests/integration/test_timetable_import_api.py` (commit với `tag_ids` chứa nhãn hệ thống E-Learning → môn có nhãn, `auto_deadlines` tạo deadline cho buổi của môn; commit không có nhãn → không)
- [ ] T052 [US4] Đề xuất nhãn trong `backend/app/pdfimport/preview.py` (dùng `is_e_learning` của `backend/app/ocr/fields.py`, bổ sung khớp "Elearning" liền chữ); commit gắn `tag_ids` cho môn trong `backend/app/services/timetable_import.py` và gọi `auto_deadlines.reconcile` cho môn mới/cập nhật
- [ ] T053 [US4] Frontend: ô nhãn E-Learning chọn sẵn theo `suggested_tags` và gửi `tag_ids` trong `frontend/src/features/imports/TimetablePreview.tsx` + `frontend/src/features/imports/timetablePreviewState.ts`; bổ sung `frontend/tests/timetablePreview.test.tsx`

**Checkpoint**: Quickstart kiểm tra tay bước 3 (nhãn + deadline). Commit.

---

## Phase 7: User Story 5 - Tên môn từ PDF giúp sửa tên khi nhập ảnh (Priority: P3)

**Goal**: Lưu tên chuẩn khi nhập PDF; nhập ảnh sửa tên theo tên chuẩn với lý do "Đã sửa theo thời khoá biểu".

**Independent Test**: Sau khi lưu `tkb-synthetic-01.pdf`, nhập khối chữ `real-week-02` → 7/7 tên môn khớp tên chuẩn (SC-007); buổi thi "Tal uuhóa" thành "Tối ưu hóa" khi tên chuẩn có môn đó.

- [ ] T054 [P] [US5] Test trong `backend/tests/integration/test_canonical_names.py`: commit PDF ghi tên chuẩn (không trùng theo `lower(name)`, giữ khi môn bị xoá); `GET /canonical-names`, `DELETE /canonical-names`; preview ảnh `real-week-02` với tên chuẩn từ fixture → 7/7 tên khớp, `reason` = "Đã sửa theo thời khoá biểu"; tên không đủ giống giữ nguyên và vẫn tô vàng
- [ ] T055 [US5] `backend/app/services/canonical_names.py` (ghi khi commit PDF, liệt kê, xoá hết) + API `backend/app/api/canonical_names.py` (`GET`/`DELETE /canonical-names`), đăng ký blueprint; gọi ghi tên trong `backend/app/services/timetable_import.py`
- [ ] T056 [US5] Nhập ảnh dùng tên chuẩn: `build_context()` trong `backend/app/services/imports.py` thêm `canonical_names`; `PreviewContext` trong `backend/app/ocr/preview.py` thêm trường đó; `_week_row` và `_exam_cell_row` thử khớp tên chuẩn trước (so không dấu, ngưỡng 70, hơn ứng viên thứ hai ≥ 15 điểm, áp dụng cả khi OCR tự tin — R11) và đặt lý do "Đã sửa theo thời khoá biểu"
- [ ] T057 [P] [US5] Frontend `frontend/src/features/settings/CanonicalNamesSettings.tsx` (danh sách tên · mã HP · ngày thêm, nút "Xoá danh sách" có xác nhận, ghi chú "Dùng để tự sửa tên môn khi nhập lịch từ ảnh."), gắn vào `frontend/src/features/settings/SettingsScreen.tsx`, API `frontend/src/api/canonicalNames.ts`; test `frontend/tests/canonicalNames.test.tsx`

**Checkpoint**: Quickstart A13. Commit.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T058 [P] Cập nhật `README.md`: mục "Nhập lịch" (ảnh và PDF thời khoá biểu), bảng tiết, danh sách tên chuẩn, ghi chú file PDF chỉ xử lý trong bộ nhớ và thư mục `samples/` không đưa vào git
- [ ] T059 [P] Cập nhật `specs/001-task-class-scheduler/contracts/rest-api.md` (SubjectInput dạng `schedules`, trỏ tới contract 004) và `specs/001-task-class-scheduler/data-model.md` (ghi chú môn chuyển sang nhiều quy tắc ở feature 004)
- [ ] T060 Kiểm tra hiệu năng SC-002 trong `backend/tests/integration/test_timetable_import_api.py`: preview `tkb-synthetic-2pages.pdf` < 3 giây
- [ ] T061 Chạy `./scripts/test.sh --ocr` toàn bộ; sửa mọi lỗi
- [ ] T062 Kiểm tra tay theo `specs/004-pdf-semester-import/quickstart.md` (gồm ⌘V file PDF trong app Tauri và file thật `samples/tkb-hk2-2026.pdf`), ghi kết quả vào `specs/004-pdf-semester-import/validation.md`; build lại Docker (`docker compose build backend web && docker compose up -d`)
- [ ] T063 Kiểm tra riêng tư trước khi commit cuối: `git ls-files samples` chỉ có `samples/synthetic/`; `git grep` không có họ tên/mã sinh viên thật; cập nhật **Status** trong `specs/004-pdf-semester-import/spec.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → các user story.
- **US1 (Phase 3)** cần Phase 2 (quy tắc, `periods_to_time`).
- **US2 (Phase 4)** cần Phase 2; phần bản xem trước (T040, T042, T044) cần US1.
- **US3 (Phase 5)** cần US1 (bản xem trước + commit).
- **US4 (Phase 6)** cần US1.
- **US5 (Phase 7)** cần US1 (commit ghi tên chuẩn); độc lập với US2–US4.
- **Polish (Phase 8)** sau các story đã chọn làm.

### Within Each Story

- Test viết trước và chạy thấy đỏ → hàm thuần → service → API → frontend.
- Commit sau mỗi checkpoint khi `./scripts/test.sh` xanh.

### Parallel Opportunities

- Phase 1: T005 song song với T003–T004.
- Phase 2: T006–T009 song song; T015, T016, T020 song song sau T010–T013; T022 song song với T021 khi API đã xong.
- US1: T023–T027 song song; T028 song song với T034; T038 sau T035–T037.
- Sau US1: US3, US4, US5 có thể làm song song (khác file chủ yếu; cùng sửa `timetable_import.py`/`TimetablePreview.tsx` thì làm tuần tự).

---

## Parallel Example: User Story 1

```text
# Viết test cùng lúc:
T023 backend/tests/unit/test_pdf_cells.py
T024 backend/tests/unit/test_pdf_layout.py
T025 backend/tests/unit/test_pdf_preview.py
T026 backend/tests/integration/test_timetable_import_api.py
T027 backend/tests/integration/test_timetable_import_privacy.py

# Rồi song song:
T028 backend/app/pdfimport/reader.py
T034 frontend/src/api/timetableImport.ts + timetablePreviewState.ts
```

---

## Implementation Strategy

### MVP First (US1, kèm Phase 1–2)

1. Phase 1 (setup + PDF giả lập) → Phase 2 (nhiều quy tắc + lõi bảng tiết; giữ test cũ xanh) → US1.
2. **Dừng và kiểm tra**: nhập `tkb-synthetic-01.pdf` và file thật trên DB trống, lịch tuần đúng, không có thông tin
   cá nhân. Bảng tiết dùng giá trị mặc định (chưa có giao diện sửa).

### Incremental Delivery

1. MVP (US1) → 2. US2 (sửa bảng tiết, tiết thiếu giờ) → 3. US3 (nhập lại an toàn) → 4. US4 (E-Learning) →
5. US5 (tên chuẩn cho nhập ảnh) → 6. Polish. Mỗi bước thêm giá trị mà không làm hỏng bước trước.
