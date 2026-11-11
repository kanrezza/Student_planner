# Implementation Plan: Nhập học kỳ từ file PDF thời khoá biểu chính thức

**Branch**: `004-pdf-semester-import` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-pdf-semester-import/spec.md`

## Summary

Cho người dùng thả/chọn/dán file PDF "Thời khóa biểu chính thức" để nhập cả học kỳ, giữ nguyên kiến trúc (Flask +
PostgreSQL trong Docker, React, app Tauri). Cách làm:

- **Đọc PDF trong backend bằng `pdfplumber`**, hoàn toàn trên máy, file chỉ nằm trong bộ nhớ. Tách từ với
  `x_tolerance=1.5`; xác định **cột thứ bằng toạ độ chữ ở hàng tiêu đề** (khớp vào đường kẻ dọc nếu có), hàng theo
  đường kẻ ngang; ghép chữ ngắt dòng theo luật riêng của từng cột; bỏ mọi vùng có thông tin cá nhân ngay sau khi trích
  từ ([R1–R6](research.md)). Spike trên file thật: 1 bảng 18 × 13 ô, 0,07 giây.
- **Một môn nhiều quy tắc lặp**: bảng mới `subject_schedules`, `class_sessions.schedule_id`, migration chuyển môn
  cũ thành 1 quy tắc; `plan_regeneration` tổng quát hoá cho nhiều quy tắc; form môn sửa được danh sách quy tắc
  ([R7](research.md), [data-model](data-model.md)).
- **Bảng tiết** `periods` suy từ ca (50 phút/tiết, nghỉ 5 phút; 16–18 = 21:05–22:00), sửa được trong Cài đặt → Ca
  học; hàm thuần đổi khoảng tiết sang ca/giờ ([R8](research.md)).
- **Bản xem trước theo môn** trên màn "Nhập lịch" (đổi từ "Nhập từ ảnh"); khớp môn đã có theo mã lớp + (mã HP hoặc
  tên), cập nhật mà không đụng buổi đã qua và buổi sửa riêng; chọn/mở rộng/tạo học kỳ; đề xuất nhãn E-Learning
  ([R9, R10, R13](research.md)).
- **Tên môn chuẩn** lưu khi nhập PDF, dùng để sửa tên khi nhập ảnh ([R11](research.md)).
- **Test bằng PDF giả lập** sinh bởi script (reportlab, chỉ dùng lúc phát triển), commit file đã sinh
  ([R12](research.md)).

Triển khai theo thứ tự: bảng tiết → mô hình nhiều quy tắc → đọc PDF + xem trước + lưu → nhập lại → tên chuẩn
([R15](research.md)).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5 + React 18 (frontend), Python 3.11 (agent), Rust stable
(Tauri) — giữ nguyên.

**Primary Dependencies**:
- Backend: thêm `pdfplumber>=0.11,<0.12` (kéo theo `pdfminer.six`, `pypdfium2`); dev: `reportlab` (chỉ cho script
  sinh PDF giả lập). Image backend thêm gói `fonts-dejavu-core` cho script đó.
- Frontend, agent, desktop: không thêm thư viện.

**Storage**: PostgreSQL 16; migration `0010_subject_schedules` (bảng quy tắc, chuyển dữ liệu môn), `0011_periods_
canonical_names`. File PDF không bao giờ ghi ra đĩa.

**Testing**: pytest (hàm thuần đọc PDF trên PDF giả lập, luật ghép ô, `periods_to_time`, `choose_semester`, khớp môn,
sinh buổi nhiều quy tắc, migration trên dữ liệu cũ, API preview/commit/periods/canonical-names, quyền riêng tư);
Vitest (bảng xem trước PDF, form nhiều quy tắc, bảng tiết, chuyển file PDF từ trang Môn học); tất cả qua
`./scripts/test.sh`. Bộ test OCR thật (`--ocr`) thêm kiểm tra SC-007 trên `real-week-02`.

**Target Platform**: macOS 14+ (Apple Silicon), app Tauri + Docker cục bộ.

**Project Type**: ứng dụng web cục bộ (backend + frontend trong Docker) + app Tauri + agent macOS.

**Performance Goals**: bản xem trước PDF < 3 giây cho file 1–3 trang (SC-002; spike 0,07 giây); lưu một học kỳ
(~8 môn, ~250 buổi) < 2 giây.

**Constraints**: chỉ kết nối `127.0.0.1`; không OCR cho PDF; không lưu/ghi log thông tin cá nhân của sinh viên;
giới hạn file 20 MB, 20 trang; tiếng Việt toàn bộ.

**Scale/Scope**: 1 người dùng; 1 học kỳ ~8–12 môn, ~20 quy tắc, ~250 buổi; 5 user story, 30 FR.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Áp dụng trong feature | Kết quả |
|------------|----------------------|---------|
| **I. Code dễ đọc** | Bộ đọc PDF tách thành hàm thuần nhỏ: `extract_words`, `find_header`, `column_ranges`, `split_rows`, `join_cell_lines` (theo loại cột), `parse_day_cell`, `group_subjects`; `periods_to_time`, `choose_semester`, `match_existing`, `plan_regeneration` | PASS |
| **II. Test chức năng chính** | Mỗi hàm thuần có test; PDF giả lập phủ ngắt dòng, tràn trang, 5 loại lỗi; migration test trên dữ liệu cũ có ngoại lệ; test API end-to-end; một lệnh `./scripts/test.sh` | PASS |
| **III. Giao diện đơn giản** | Dùng chung màn "Nhập lịch" cho ảnh và PDF; bảng xem trước theo môn; bảng tiết nằm trong mục Ca học có sẵn; không thư viện UI mới | PASS |
| **IV. Offline trên Mac** | `pdfplumber` chạy trong container, không gọi mạng; file chỉ trong bộ nhớ; bỏ họ tên/mã SV/lớp/học phí trước mọi xử lý và không ghi log (R6) | PASS |
| **V. Dữ liệu bền vững** | Commit nhập PDF trong một transaction; migration 0010 chuyển dữ liệu có test và có `downgrade`; bản sao lưu cũ được nâng cấp khi khôi phục (luồng 003 chạy `upgrade`) | PASS |
| **VI. Tiếng Việt** | Mọi thông báo, lỗi PDF, nhãn bảng tiết qua `i18n/vi.ts`; ngày DD/MM/YYYY, giờ 24h | PASS |
| Ràng buộc bổ sung: YAGNI, ít phụ thuộc | 1 phụ thuộc runtime (`pdfplumber`) + 1 dev (`reportlab`) + 1 gói phông; lý do ở Complexity Tracking | PASS |

**Re-check sau Phase 1**: data-model thêm 3 bảng (`subject_schedules`, `periods`, `canonical_subject_names`), 3 cột
(`subjects.course_code`, `subjects.credits`, `class_sessions.schedule_id`) và bỏ các cột lịch phẳng của `subjects`;
contracts chỉ thêm endpoint localhost; không có kênh ra ngoài máy. Vẫn PASS.

## Project Structure

### Documentation (this feature)

```text
specs/004-pdf-semester-import/
├── plan.md                         # File này
├── research.md                     # Phase 0 (R1–R15)
├── data-model.md                   # Phase 1
├── quickstart.md                   # Phase 1 — kịch bản A1–A15 + kiểm tra tay
├── contracts/
│   ├── rest-api.md                 # môn nhiều quy tắc, /periods, /imports/timetable-pdf/*, /canonical-names
│   ├── timetable-pdf-format.md     # định dạng PDF được hỗ trợ + đáp án file giả lập
│   └── ui.md                       # màn Nhập lịch, form môn, bảng tiết, tên chuẩn
├── checklists/requirements.md
└── tasks.md                        # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                  # + pdfplumber; dev + reportlab
├── Dockerfile                      # + fonts-dejavu-core
├── migrations/versions/
│   ├── 0010_subject_schedules.py
│   └── 0011_periods_canonical_names.py
├── app/
│   ├── models/{subject_schedule,period,canonical_name}.py   # mới; subject.py, class_session.py đổi
│   ├── pdfimport/                  # mới — hàm thuần, không đụng CSDL
│   │   ├── reader.py               # mở PDF trong bộ nhớ, kiểm tra lỗi, trích từ + đường kẻ
│   │   ├── layout.py               # hàng tiêu đề, khoảng cột theo toạ độ chữ, chia hàng, bỏ vùng cá nhân
│   │   ├── cells.py                # ghép dòng theo loại cột, đọc ô thứ, ngày, học kỳ
│   │   └── preview.py              # gộp môn, đổi tiết → giờ, khớp môn đã có, chọn học kỳ → TimetablePdfPreview
│   ├── services/
│   │   ├── periods.py              # mới: bảng tiết, periods_to_time, tính lại khi đổi ca
│   │   ├── timetable_import.py     # mới: preview (dựng ngữ cảnh từ CSDL) + commit một transaction
│   │   ├── canonical_names.py      # mới
│   │   ├── recurrence.py           # plan_regeneration nhiều quy tắc + keep_before
│   │   ├── subjects.py, semesters.py, shifts.py, digest.py, task_recurrence.py, imports.py   # đọc lịch từ quy tắc
│   ├── schemas/{subjects,timetable_import,periods}.py
│   ├── api/{periods,timetable_import,canonical_names}.py     # mới; subjects.py đổi
│   └── ocr/preview.py              # nguồn tên chuẩn + lý do "Đã sửa theo thời khoá biểu"
└── tests/
    ├── fixtures/timetables/tkb-synthetic-01.pdf, tkb-synthetic-2pages.pdf, tkb-*.pdf (file lỗi)
    ├── unit/test_pdf_{layout,cells,preview}.py, test_periods.py, test_recurrence_schedules.py, test_choose_semester.py
    └── integration/test_timetable_import_api.py, test_periods_api.py, test_subject_schedules_api.py,
        test_migration_0010.py, test_canonical_names.py

samples/synthetic/make_timetable_pdf.py   # sinh PDF giả lập (reportlab + DejaVu)

frontend/src/
├── api/{subjects,periods,timetableImport,canonicalNames}.ts
├── features/imports/ImportScreen.tsx, TimetablePreview.tsx (mới), timetablePreviewState.ts (mới),
│   pendingFile.ts (đổi từ pendingImage.ts), usePasteFile.ts (đổi từ usePasteImage.ts)
├── features/subjects/SubjectForm.tsx (danh sách quy tắc), ScheduleRows.tsx (mới), SubjectsScreen.tsx, BulkSubjectForm.tsx
├── features/settings/ShiftsSettings.tsx + PeriodsTable.tsx (mới), CanonicalNamesSettings.tsx (mới)
└── i18n/vi.ts
frontend/tests/ — timetablePreview.test.tsx, scheduleRows.test.tsx, periodsTable.test.tsx, importScreen.test.tsx (PDF)
```

**Structure Decision**: Giữ cấu trúc web cục bộ hiện có (`backend/`, `frontend/`, `desktop/`, `mac-agent/`). Bộ đọc
PDF là gói mới `backend/app/pdfimport/` gồm hàm thuần (giống `backend/app/ocr/` của nhập ảnh), service mỏng nối với
CSDL. Agent macOS và app Tauri không đổi.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Thêm phụ thuộc `pdfplumber` (+ `pdfminer.six`, `pypdfium2`) | Cần toạ độ từ và đường kẻ bảng để gán cột thứ (yêu cầu của người dùng); spike đọc đúng bảng trong 0,07 giây | `pypdf` không có toạ độ từ tiện dùng; PyMuPDF giấy phép AGPL; camelot/tabula cần Java/Ghostscript |
| Thêm dev `reportlab` + gói `fonts-dejavu-core` trong image | Sinh PDF giả lập có chữ tiếng Việt và đường kẻ để test mà không đưa PDF thật vào git | Che dữ liệu trên PDF thật dễ sót dữ liệu ẩn; vẽ PDF thủ công bằng chuỗi lệnh PDF thô thì khó đọc và khó sửa |
| Đổi mô hình môn sang nhiều quy tắc (bảng mới + migration chuyển dữ liệu) | Kỳ nghỉ Tết, đổi phòng/thứ giữa kỳ và một dòng hai thứ hai phòng không biểu diễn được bằng một quy tắc; người dùng chọn sửa quy tắc bằng tay | Tách thành nhiều môn trùng tên làm nhân đôi môn/deadline/màu; ngoại lệ từng tuần không biểu diễn được hai thứ khác phòng |
