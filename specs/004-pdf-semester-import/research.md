# Research: Nhập học kỳ từ file PDF thời khoá biểu chính thức

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-10

Mọi quyết định giữ kiến trúc hiện tại (Flask + PostgreSQL trong Docker, React, agent macOS, app Tauri). Spike
chạy trên file PDF thật trong `samples/` (không đưa vào git), kết quả ghi dưới đây không chứa thông tin cá nhân.

## R1. Thư viện đọc PDF

- **Decision**: `pdfplumber` 0.11 (MIT), dựa trên `pdfminer.six` (MIT) và `pypdfium2` (Apache-2.0/BSD), chạy
  trong backend, cài vào image Docker như các phụ thuộc khác; không gọi mạng.
- **Rationale**: Cho toạ độ từng ký tự/từ và đường kẻ bảng, đúng thứ cần để xác định cột thứ (yêu cầu của người
  dùng). Spike trên file thật: 1 trang, 1.636 ký tự, `find_tables()` nhận ra 1 bảng 18 dòng × 13 cột (1 dòng tiêu
  đề + 17 dòng dữ liệu), toàn bộ đọc trong **0,07 giây** (SC-002 cần < 3 giây).
- **Alternatives considered**:
  - `pypdf`: chỉ trích chữ theo luồng, không có toạ độ từ tiện dùng → khó gán cột.
  - PyMuPDF (`fitz`): nhanh nhưng giấy phép AGPL → loại.
  - camelot / tabula: cần Ghostscript hoặc Java → nặng, thêm phụ thuộc hệ thống.
  - `pdftotext -layout` (poppler): phải cài thêm gói hệ thống và vẫn phải đoán cột từ khoảng trắng.

## R2. Tách từ: độ nhạy `x_tolerance`

- **Decision**: Trích từ và trích ô với `x_tolerance=1.5`.
- **Rationale**: Khoảng cách giữa hai từ trong file thật ≈ 2,1 pt; giá trị mặc định 3 pt dính chữ ("Bóngđá",
  "Tíchhợpvàphântíchdữ", "Thứ2", "Thờigian"). Spike với 1,5 / 1 / 0,5 đều cho đúng "Tích hợp và phân tích dữ",
  "Thứ 2", "Thời gian"; chọn 1,5 để còn chịu được ký tự sát nhau trong cùng từ.
- **Alternatives considered**: tự ghép ký tự theo khoảng cách → trùng việc pdfplumber đã làm.

## R3. Xác định cột thứ và hàng bằng toạ độ

- **Decision**:
  1. Tìm hàng tiêu đề: các từ "Mã", "HP", "Lớp học phần", "Thứ 2"…"Thứ 7", "CN", "Thời gian" nằm cùng một dải
     dọc (sai lệch ≤ 1 dòng chữ). Bắt buộc có đủ 7 cột thứ và cột "Thời gian"; thiếu → "Không tìm thấy bảng thời
     khoá biểu trong file".
  2. **Cột**: khoảng x của mỗi cột tính từ toạ độ chữ tiêu đề (từ mép trái chữ tiêu đề cột này tới mép trái chữ
     tiêu đề cột kế tiếp, trừ một khoảng đệm), rồi **khớp vào đường kẻ dọc gần nhất** của bảng nếu có. Spike: x
     của "Thứ" = 190, 235, 280, 324, 369, 405; "CN" = 436; "Thời" = 460.
  3. **Hàng**: theo đường kẻ ngang của bảng (`find_tables()` → `rows[i].bbox`). Nếu file không có đường kẻ, dùng
     dự phòng: mỗi hàng bắt đầu ở một số STT hoặc ở cặp ngày của cột "Thời gian".
  4. Mỗi từ thuộc ô có chứa tâm của từ; các từ trong một ô sắp theo dòng rồi theo x.
  5. Dừng ở hàng có chữ "Tổng cộng"; mọi thứ phía dưới (số tiền bằng chữ, ngày lập, chữ ký) bị bỏ.
- **Rationale**: Gán cột theo chữ tiêu đề không phụ thuộc độ rộng cột cố định, nên chịu được PDF xuất ở khổ giấy
  hay phông khác; đường kẻ giúp ranh giới chính xác khi có.
- **Alternatives considered**: dùng thẳng `table.extract()` theo ô của đường kẻ — chạy tốt trên file mẫu nhưng
  hỏng nếu thiếu đường kẻ; giữ làm cách kiểm tra chéo trong test.

## R4. Ghép chữ bị ngắt dòng trong ô

Spike cho thấy ô bị ngắt cả giữa từ lẫn giữa mã: mã HP "FFS7010 | 69", phòng "A6-1 | 03 | (PC))",
"A6-301.30 | 2 (PC))", "Sân | bóng đá", "ONLINE- | Elearning", tên lớp học phần "Tích hợp và phân tích dữ | liệu |
lớn-2-2-26(COUR01.LT2)".

- **Decision**: luật ghép theo loại cột:
  - **Mã HP**: nối liền, không dấu cách ("FFS701069", "CSE703016").
  - **Lớp học phần** (tên + mã lớp): nối bằng dấu cách (cổng xuất ngắt ở ranh giới từ cho phần tên); sau đó tách
    tên và mã lớp bằng `split_class_label` sẵn có của nhập ảnh ("…-2-2-26(N01)").
  - **Ô thứ** ("tiết - tiết (phòng)"): nối dòng **không** dấu cách khi dòng trước kết thúc bằng chữ số, `.` hoặc
    `-`, hoặc dòng sau bắt đầu bằng chữ số hay `.`; ngược lại nối bằng dấu cách. Sau đó chuẩn hoá "(PC)" về dạng
    " (PC)". Kết quả spike mong đợi: "A6-103 (PC)", "A6-301.302 (PC)", "Sân bóng đá", "ONLINE-Elearning".
  - **Thời gian**: lấy mọi ngày `dd/mm/yyyy` theo thứ tự xuất hiện.
- **Rationale**: Mỗi loại cột có kiểu ngắt riêng; luật theo loại cột đơn giản và kiểm thử được bằng bảng ví dụ.
- **Alternatives considered**: một luật chung theo độ rộng ô (dòng trước "đầy" thì nối liền) — sai với tên môn
  ("Tích hợp và phân tích dữ" cũng đầy dòng nhưng cần dấu cách).

## R5. Đọc ô thứ, ngày, học kỳ

- **Decision**:
  - Ô thứ: `^(\d{1,2})\s*-\s*(\d{1,2})\s*\((.*)\)$` sau khi ghép (phòng có thể chứa ngoặc lồng nhau "A6-103 (PC)").
    Có tiết mà thiếu phòng → phòng rỗng, quy tắc tô vàng; không đọc được tiết → tô vàng, cho nhập.
  - Ngày: đúng 2 ngày → (bắt đầu, kết thúc); 1 hoặc 0 ngày, hay kết thúc < bắt đầu → quy tắc tô đỏ (FR-019).
  - Học kỳ: dòng phía trên bảng khớp `Học kỳ (\d+) Năm học (\d{4}) - (\d{4})` → tên đề xuất "HK2 2026–2027".
- **Rationale**: Định dạng do cổng sinh ra, ổn định; regex nhỏ và có test.

## R6. Không giữ thông tin cá nhân

- **Decision**: Bộ đọc chỉ đi qua hai vùng: (a) dòng "Học kỳ … Năm học …", (b) bảng từ hàng tiêu đề tới trước
  "Tổng cộng", **bỏ cột Học phí và cột STT**. Mọi từ khác (họ tên, mã sinh viên, khoá/lớp, ngành, tổng tiền, chữ
  ký) bị loại ngay sau bước trích từ, không vào bản xem trước, không ghi log, không lưu. File chỉ nằm trong bộ
  nhớ (đọc từ request vào `BytesIO`), không ghi ra đĩa, kể cả file tạm.
- **Rationale**: Đúng FR-002, FR-009, SC-006 và nguyên tắc IV của constitution.
- **Kiểm chứng**: test dùng PDF giả lập chứa họ tên, mã sinh viên, lớp, học phí giả; khẳng định không giá trị nào
  xuất hiện trong JSON trả về, trong log đã bắt, hay trong CSDL sau khi lưu (giống `student_values_must_not_appear`
  của nhập lịch thi).

## R7. Một môn nhiều quy tắc lặp

- **Decision**: Thêm bảng `subject_schedules` (quy tắc lặp hằng tuần); chuyển các cột lịch đang nằm ở `subjects`
  (`weekdays`, `start_date`, `end_date`, `start_shift_id`, `end_shift_id`, `start_time`, `end_time`, `room`) sang
  bảng mới. `class_sessions` thêm `schedule_id`. Migration chuyển mỗi môn cũ thành 1 quy tắc và gán `schedule_id`
  cho buổi của nó. Chi tiết ở [data-model.md](data-model.md).
- **Sinh buổi**: tổng quát hoá `plan_regeneration` từ "một tập ngày + một giờ + một phòng" sang "ánh xạ ngày →
  (quy tắc, giờ, phòng)" của cả môn; buổi hiện có vẫn khớp theo `lock_date` như cũ, nên buổi đã dời/huỷ/sửa riêng
  được giữ đúng như feature 001/002. Hai quy tắc cùng môn rơi vào cùng ngày: lấy quy tắc đứng trước, cảnh báo
  (FR-023).
- **API**: `SubjectInput` có `schedules: [ScheduleInput, …]` (≥ 1) thay cho các trường lịch phẳng; phản hồi môn có
  `schedules`. Form một môn (FR-020a), form nhập nhiều môn (mỗi dòng 1 quy tắc) và nhập ảnh đều gửi dạng mới.
- **Rationale**: Mô hình cũ không biểu diễn được kỳ nghỉ Tết, đổi phòng/đổi thứ giữa kỳ, hay một dòng có hai thứ
  với hai phòng; người dùng đã chọn cho sửa quy tắc bằng tay (Clarification Q1).
- **Alternatives considered**:
  - Tách mỗi quy tắc thành một môn riêng trùng tên → nhân đôi môn trong danh sách, deadline, màu, nhãn; loại.
  - Giữ một quy tắc và ghi "ngoại lệ" cho từng tuần nghỉ/đổi phòng → không biểu diễn được hai thứ khác phòng; sửa
    tay rất rối; loại.
  - Giữ cột phẳng ở `subjects` làm "quy tắc chính" + bảng phụ → hai nguồn sự thật; loại.

## R8. Bảng tiết

- **Decision**: Bảng `periods` (số tiết, giờ bắt đầu, giờ kết thúc, `is_manual`). Migration tạo tiết 1–12 từ 4 ca
  theo FR-012 (mỗi tiết 50 phút, nghỉ 5 phút, chia đều nếu ca khác 160 phút) và tiết 16–18 theo FR-013 (21:05–21:20,
  21:20–21:40, 21:40–22:00). Đổi giờ ca k (PATCH `/shifts`) tính lại các tiết 3k−2…3k có `is_manual = false` trong
  cùng transaction. Người dùng sửa một tiết → `is_manual = true`; có nút "Về mặc định".
- **Khoảng tiết → giờ** (hàm thuần `periods_to_time`): bắt đầu tiết đầu → kết thúc tiết cuối; trùng đúng một ca
  hoặc dãy ca liền nhau (tiết 3k−2 … 3m) → gắn ca như nhập ảnh hiện nay; còn lại giờ tuỳ chỉnh và giữ `period_from`
  / `period_to` để hiển thị "Tiết 1–2".
- **Rationale**: Clarification Q3; giữ gắn ca để đổi giờ ca vẫn cập nhật buổi (FR-040 của 001).
- **Alternatives considered**: lưu giờ tiết trong `settings` dạng JSON → khó kiểm tra ràng buộc, khó sửa từng
  tiết; loại.

## R9. Nhận ra môn đã có và cập nhật khi nhập lại

- **Decision**:
  - Khoá khớp (FR-021): cùng học kỳ đích, `ci_key(class_code)` bằng nhau **và** (`course_code` bằng nhau **hoặc**
    `fold_key(name)` bằng nhau). Môn tạo từ ảnh không có `course_code` nên khớp theo tên + mã lớp; khi lưu thì được
    bổ sung `course_code`, `credits` và tên chuẩn từ PDF.
  - Trạng thái trong bản xem trước: `new`, `unchanged` (mọi quy tắc trùng hệt; mặc định bỏ chọn), `changed` kèm
    danh sách khác biệt (phòng, thứ, giờ, khoảng ngày, thêm/bớt quy tắc).
  - Lưu môn `changed`: thay toàn bộ quy tắc của môn bằng quy tắc từ PDF rồi sinh lại buổi với tham số mới
    `keep_before = hôm nay`: buổi có ngày < hôm nay không bị sửa hay xoá; buổi có ngoại lệ giữ như cũ; buổi có
    ngoại lệ nằm ngoài lịch mới → giữ lại (không hỏi xác nhận, khác với sửa tay) và liệt kê trong cảnh báo.
  - Môn không có trong PDF: không đụng tới (FR-024).
- **Rationale**: Nhập lại phải an toàn và không cần hộp thoại xác nhận cho từng môn.
- **Alternatives considered**: khớp theo tên đơn thuần → hai lớp "N02" và "N02.TH1" cùng tên bị gộp nhầm; loại.

## R10. Chọn hoặc tạo học kỳ

- **Decision** (hàm thuần `choose_semester`): khoảng cần = [ngày sớm nhất, ngày muộn nhất] của các quy tắc được
  chọn.
  1. Có học kỳ chứa trọn khoảng → dùng học kỳ ngắn nhất trong số đó.
  2. Không có, và khoảng không chồng học kỳ nào → đề xuất tạo mới (tên theo R5, khoảng = khoảng cần).
  3. Khoảng chồng một phần đúng một học kỳ → đề xuất **mở rộng** học kỳ đó cho đủ khoảng (vì học kỳ không được
     chồng nhau, FR-036 của 001); chồng nhiều học kỳ → báo lỗi trong bản xem trước, người dùng tự sửa học kỳ hoặc
     bỏ chọn quy tắc.
  Người dùng đổi được lựa chọn (chọn học kỳ khác nếu chứa trọn khoảng).
- **Rationale**: FR-018; giữ ràng buộc không chồng học kỳ hiện có.

## R11. Danh sách tên môn chuẩn

- **Decision**: Bảng `canonical_subject_names` (tên, mã HP, thời điểm thêm), duy nhất theo `ci_key(name)`. Ghi khi
  lưu nhập PDF; xoá được toàn bộ trong Cài đặt. `build_context()` của nhập ảnh gộp tên chuẩn vào `subject_names`
  và đánh dấu nguồn; khi `_fix_name` / `_fix_weak_name` sửa theo tên chuẩn thì lý do là "Đã sửa theo thời khoá
  biểu". Với tên chuẩn, so khớp không dấu (ngưỡng 70, hơn ứng viên thứ hai ≥ 15 điểm) áp dụng cả khi OCR tự tin
  (vd. "Xử lý ngón ngữ tự nhlên", độ tin cậy 0,61), vì tên chuẩn là nguồn đúng. Kiểm chứng SC-007 bằng khối chữ OCR
  `real-week-02` đã có trong fixtures.
- **Rationale**: Dùng lại cơ chế sửa tên đã có của feature 003, chỉ thêm nguồn tên.

## R12. File PDF giả lập cho test

- **Decision**: Script `samples/synthetic/make_timetable_pdf.py` dựng PDF cùng bố cục (kẻ bảng, tiêu đề, phần đầu
  có họ tên/mã SV giả, chữ ngắt dòng giữa mã và phòng như file thật) bằng `reportlab` (phụ thuộc dev) với phông
  DejaVu Sans (gói `fonts-dejavu-core`, giấy phép tự do). File sinh ra được commit vào
  `backend/tests/fixtures/timetables/tkb-synthetic-01.pdf` (vài chục KB) để test không cần chạy lại script; thêm một
  file thứ hai 2 trang (bảng tràn trang) và các file lỗi (không có chữ, có mật khẩu, không phải thời khoá biểu).
- **Rationale**: Đúng yêu cầu "test bằng PDF giả lập, không đưa PDF thật vào git"; `.gitignore` đã chặn mọi file
  trong `samples/` trừ `samples/synthetic/`.
- **Alternatives considered**: che thông tin trên PDF thật (sửa nội dung PDF) → dễ sót dữ liệu ẩn trong file; loại.

## R13. Giao diện: màn "Nhập lịch"

- **Decision**: Màn "Nhập từ ảnh" đổi tên "Nhập lịch", vùng thả nhận ảnh và `application/pdf`. Theo loại file gọi
  endpoint nhận diện ảnh hoặc endpoint PDF; PDF hiện bảng xem trước theo môn (thành phần mới
  `TimetablePreview`). Trang Môn học: thả/dán PDF → lưu file chờ (mở rộng `pendingImage` thành `pendingFile`) rồi
  chuyển sang màn "Nhập lịch", giống ảnh hiện nay (Clarification Q2). `usePasteImage` mở rộng thành `usePasteFile`
  nhận cả PDF trong `clipboardData.files`.
- **Rủi ro**: dán file PDF sao chép từ Finder trong WKWebView (app Tauri) có thể không cho `File` qua clipboard; nếu
  không được thì vẫn có kéo thả và chọn file (đã ghi ở Assumptions của spec). Kiểm tra tay ở quickstart.

## R14. Giới hạn và lỗi

- **Decision**: Kiểm tra theo thứ tự, mỗi lỗi một thông báo tiếng Việt (FR-003): dung lượng > 20 MB (dùng chung
  giới hạn nhập ảnh) → 413; không bắt đầu bằng `%PDF-` → 415; pdfminer báo mã hoá/mật khẩu → 422 `pdf_encrypted`;
  hỏng → 422 `pdf_unreadable`; > 20 trang → 422 `pdf_too_long`; không có ký tự chữ → 422 `pdf_no_text` ("hãy dùng
  nhập từ ảnh"); không tìm thấy hàng tiêu đề → 422 `pdf_not_timetable`.

## R15. Thứ tự triển khai

1. Bảng tiết + `periods_to_time` (US2) — độc lập, cần cho mọi bước sau.
2. Mô hình nhiều quy tắc (migration, service, API môn, form môn có danh sách quy tắc, nhập ảnh dùng dạng mới) —
   rủi ro cao nhất nên làm sớm, giữ toàn bộ test hiện có xanh.
3. Bộ đọc PDF (hàm thuần trên từ/đường kẻ) + PDF giả lập + bản xem trước + lưu (US1, US4).
4. Nhập lại/cập nhật (US3).
5. Tên chuẩn cho nhập ảnh (US5).
