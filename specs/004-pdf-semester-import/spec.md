# Feature Specification: Nhập học kỳ từ file PDF thời khoá biểu chính thức

**Feature Branch**: `004-pdf-semester-import`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Nhập học kỳ từ file PDF \"Thời khóa biểu chính thức\" của cổng sinh viên
Phenikaa (file mẫu: samples/tkb-hk2-2026.pdf).
- Người dùng kéo thả, chọn hoặc dán (⌘V) file PDF ở trang Môn học. PDF có chữ thật nên đọc trực tiếp
  nội dung chữ, chạy hoàn toàn trên máy, không dùng OCR.
- Mỗi dòng gồm mã học phần, tên lớp học phần (có mã lớp trong ngoặc), số tín chỉ, ô \"tiết + phòng\"
  nằm ở cột thứ tương ứng (Thứ 2 → CN), và khoảng ngày (bắt đầu – kết thúc). Một môn có thể có nhiều
  dòng với khoảng ngày, phòng hoặc thứ khác nhau; mỗi dòng là một quy tắc lặp hằng tuần riêng của
  cùng một môn. Một dòng có thể có nhiều thứ.
- Đổi tiết sang giờ bằng bảng tiết chỉnh được trong Cài đặt → Ca học: tiết 1–3 = Ca 1, 4–6 = Ca 2,
  7–9 = Ca 3, 10–12 = Ca 4; hỗ trợ khoảng tiết lẻ (ví dụ 1–2) và tiết ngoài 4 ca (ví dụ 16–18 =
  21:05–22:00). Giờ từng tiết mặc định suy từ các ca hiện có.
- Phòng có chữ \"ONLINE\" hoặc \"Elearning\" thì tự gắn nhãn E-Learning (để quy tắc tự tạo deadline
  áp dụng).
- Bỏ qua họ tên, mã sinh viên, khoá/lớp, học phí, chữ ký; không lưu ở đâu. File PDF chỉ xử lý trong
  bộ nhớ.
- Trước khi lưu luôn hiện bảng xem trước theo từng môn (các khoảng ngày, thứ, tiết/ca, giờ, phòng)
  để kiểm tra và sửa; không tạo trùng môn hoặc buổi đã có (cập nhật môn đã có nếu trùng mã lớp); tự
  tạo hoặc chọn học kỳ phù hợp với khoảng ngày.
- Tên môn đọc được từ PDF được dùng làm danh sách chuẩn để tự sửa tên môn khi nhập lịch từ ảnh sau
  này.
- Test bằng file PDF giả lập (tên, mã sinh viên giả); không đưa PDF thật vào git."

## Bối cảnh

Feature này bổ sung vào app macOS "Lịch Học Cá Nhân" đã có (feature `001-task-class-scheduler`,
`002-redesign-macos-app`, `003-backup-nl-recurring-search`). Mọi dữ liệu, quy tắc và chức năng hiện có
(học kỳ, môn học, buổi học, ca học, nhãn E-Learning, deadline tự tạo, nhập lịch từ ảnh, đồng bộ Lịch
và Lời nhắc, sao lưu) giữ nguyên; feature này chỉ thêm một cách nhập mới và những thay đổi tối thiểu
cần cho nó.

Nhập từ ảnh (feature 001) chỉ thấy một tuần và phụ thuộc OCR nên tên môn, giảng viên hay sai vài ký
tự. File PDF "Thời khóa biểu chính thức" có chữ thật và chứa cả học kỳ, nên đọc được chính xác toàn bộ
lịch trong một lần. Tên môn đọc từ PDF cũng giúp nhập ảnh về sau sửa tên cho đúng.

Đặc điểm của PDF mẫu (quan sát từ file thật, dùng để viết yêu cầu; không chép thông tin cá nhân):

- Phần đầu có tên trường, tiêu đề, "Học kỳ … Năm học … Đợt …", họ tên, mã sinh viên, khoá/lớp, ngành.
- Bảng có các cột: STT, Mã HP, Lớp học phần, Số TC, Thứ 2 … Thứ 7, CN, Thời gian, Học phí.
- Ô thứ ghi "tiết đầu - tiết cuối (phòng)", ví dụ "4 - 6 (Sân bóng đá)", "1 - 3 (A6-101.102 (PC))",
  "16 - 18 (ONLINE-Elearning)". Một dòng có thể có ô ở hai thứ với phòng khác nhau.
- Cột "Thời gian" ghi hai ngày: bắt đầu và kết thúc của dòng đó.
- Chữ trong ô thường bị ngắt dòng giữa chừng: mã HP ("FFS7010" / "69"), tên lớp học phần, phòng
  ("A6-1" / "01.102" / "(PC))").
- Cùng một lớp học phần xuất hiện ở nhiều dòng (STT giống nhau) với khoảng ngày khác nhau, ví dụ trước
  và sau kỳ nghỉ Tết, hoặc đổi phòng, đổi thứ, đổi số tiết (1–3 rồi 1–2) giữa học kỳ.
- Cùng một mã HP có thể có hai lớp học phần khác nhau (lý thuyết "N02" và thực hành "N02.TH1").
- Cuối bảng có "Tổng cộng", "Viết bằng chữ", ngày lập và chỗ ký.

## Clarifications

### Session 2026-11-10

- Q: Trong form sửa môn ở trang Môn học, người dùng có được thêm, sửa, xoá từng quy tắc lặp bằng tay
  không? → A: Có. Form sửa môn hiện danh sách quy tắc; thêm, sửa, xoá từng quy tắc bằng tay; môn tạo
  tay mặc định có 1 quy tắc.
- Q: Khi thả hoặc dán file PDF ở trang Môn học, bảng xem trước mở ở đâu? → A: Màn "Nhập từ ảnh" đổi
  thành "Nhập lịch", nhận cả ảnh lẫn PDF; thả/dán ở trang Môn học hay ở màn này đều mở cùng màn; PDF
  hiện bảng xem trước theo môn.
- Q: Trong mỗi ca 3 tiết, giờ từng tiết mặc định chia thế nào? → A: Mỗi tiết 50 phút, nghỉ 5 phút giữa
  các tiết (tiết 1 06:45–07:35, tiết 2 07:40–08:30, tiết 3 08:35–09:25).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhập cả học kỳ từ file PDF (Priority: P1)

Đầu học kỳ, người dùng tải file PDF "Thời khóa biểu chính thức" từ cổng sinh viên rồi kéo thả (hoặc
chọn, hoặc dán bằng ⌘V) vào trang Môn học hoặc màn "Nhập lịch". Ứng dụng mở màn "Nhập lịch", đọc file
trên máy và hiện bảng xem trước nhóm theo
từng môn (lớp học phần): mỗi môn liệt kê các quy tắc lặp hằng tuần gồm khoảng ngày, thứ, tiết, ca, giờ
và phòng. Người dùng kiểm tra, sửa nếu cần rồi bấm Lưu. Ứng dụng tạo các môn và toàn bộ buổi học của
học kỳ; học kỳ phù hợp được chọn sẵn hoặc tạo mới.

**Why this priority**: Đây là mục đích chính của feature: nhập đúng toàn bộ lịch học kỳ trong một
thao tác, thay cho việc nhập tay hoặc chụp từng tuần.

**Independent Test**: Kéo thả file PDF giả lập (cùng bố cục với file thật) vào trang Môn học trên dữ
liệu trống; kiểm tra bảng xem trước đúng số môn, số quy tắc, khoảng ngày, thứ, giờ, phòng; bấm Lưu và
kiểm tra lịch tuần hiện đúng các buổi, kể cả tuần nghỉ Tết không có buổi nào.

**Acceptance Scenarios**:

1. **Given** chưa có học kỳ nào, **When** người dùng kéo thả file PDF mẫu vào trang Môn học, **Then**
   bảng xem trước hiện 8 môn (lớp học phần) với tổng cộng 17 quy tắc lặp hằng tuần, và đề xuất tạo học
   kỳ mới có tên theo dòng "Học kỳ 2 Năm học 2026 - 2027" và khoảng ngày 30/11/2026 – 28/02/2027.
2. **Given** dòng "Bóng đá-2-2-26(N01)" ghi "4 - 6 (Sân bóng đá)" ở cột Thứ 2, khoảng 30/11/2026 –
   24/01/2027, **When** xem trước, **Then** môn "Bóng đá", mã lớp "2-2-26(N01)", mã học phần
   "FFS701069" (đã ghép phần bị ngắt dòng) có quy tắc: Thứ Hai, tiết 4–6 (Ca 2), 09:30–12:10, phòng
   "Sân bóng đá", từ 30/11/2026 đến 24/01/2027.
3. **Given** một dòng có ô ở cả Thứ 3 "4 - 6 (A6-203 (PC))" và Thứ 6 "4 - 6 (A6-702 (PC))", **When**
   xem trước, **Then** môn đó có hai quy tắc cùng khoảng ngày: Thứ Ba phòng A6-203 (PC) và Thứ Sáu phòng
   A6-702 (PC).
4. **Given** cùng một môn có quy tắc 30/11/2026 – 24/01/2027 và 15/02/2027 – 28/02/2027, **When** lưu,
   **Then** không có buổi học nào của môn đó trong khoảng 25/01/2027 – 14/02/2027.
5. **Given** bảng xem trước đang mở, **When** người dùng sửa phòng, giờ, thứ hoặc khoảng ngày của một
   quy tắc, bỏ chọn một quy tắc hoặc cả một môn rồi bấm Lưu, **Then** dữ liệu được lưu đúng như đã sửa
   và phần bỏ chọn không được tạo.
6. **Given** người dùng bấm Huỷ ở bảng xem trước, **When** quay lại trang Môn học, **Then** không có môn,
   buổi hay học kỳ nào được tạo.
7. **Given** file PDF đã đọc xong, **When** kiểm tra mọi dữ liệu ứng dụng lưu và hiển thị (bảng xem
   trước, môn, buổi, nhật ký), **Then** không có họ tên, mã sinh viên, khoá/lớp, ngành, học phí hay chữ
   ký của sinh viên.

---

### User Story 2 - Đổi tiết sang giờ theo bảng tiết chỉnh được (Priority: P1)

Cổng sinh viên ghi lịch theo tiết, còn ứng dụng làm việc theo giờ và ca. Trong Cài đặt → Ca học có thêm
bảng tiết: mỗi tiết có giờ bắt đầu và kết thúc, mặc định suy từ các ca hiện có (Ca 1 = tiết 1–3, Ca 2 =
tiết 4–6, Ca 3 = tiết 7–9, Ca 4 = tiết 10–12). Người dùng chỉnh được giờ từng tiết. Khi nhập PDF, khoảng
tiết trùng đúng một ca hoặc dãy ca liền nhau thì gắn với ca đó; khoảng tiết lẻ (1–2) hoặc ngoài 4 ca
(16–18) thì dùng giờ tuỳ chỉnh lấy từ bảng tiết.

**Why this priority**: Không đổi được tiết sang giờ thì không tạo được buổi học; đây là điều kiện để
User Story 1 hoạt động.

**Independent Test**: Mở Cài đặt → Ca học, kiểm tra bảng tiết mặc định khớp với 4 ca; đổi giờ một tiết;
nhập file PDF giả lập có tiết 1–2 và 16–18; kiểm tra giờ trong bảng xem trước theo bảng tiết.

**Acceptance Scenarios**:

1. **Given** ca mặc định (Ca 1 06:45–09:25, Ca 2 09:30–12:10, Ca 3 13:00–15:40, Ca 4 15:45–18:25),
   **When** mở bảng tiết, **Then** tiết 1 bắt đầu 06:45, tiết 3 kết thúc 09:25, tiết 4 bắt đầu 09:30,
   tiết 12 kết thúc 18:25, và mỗi ca chia thành 3 tiết liền nhau.
2. **Given** quy tắc "tiết 1 - 3", **When** xem trước, **Then** quy tắc gắn với Ca 1 và giờ 06:45–09:25.
3. **Given** quy tắc "tiết 1 - 2", **When** xem trước, **Then** quy tắc dùng giờ tuỳ chỉnh từ đầu tiết 1
   đến cuối tiết 2, ghi rõ "Tiết 1–2, không trọn ca".
4. **Given** bảng tiết có tiết 16–18 với giờ mặc định 21:05–22:00, **When** nhập quy tắc "16 - 18",
   **Then** quy tắc có giờ 21:05–22:00.
5. **Given** quy tắc dùng tiết chưa có giờ trong bảng tiết (ví dụ tiết 13), **When** xem trước, **Then**
   ô giờ tô vàng "Chưa có giờ cho tiết 13–15, hãy nhập giờ", nút Lưu bị chặn đến khi người dùng nhập giờ;
   người dùng có thể chọn lưu luôn giờ đó vào bảng tiết.
6. **Given** người dùng đổi giờ một ca trong Cài đặt, **When** mở bảng tiết, **Then** các tiết thuộc ca
   đó được cập nhật theo, trừ tiết đã được chỉnh tay riêng.

---

### User Story 3 - Nhập lại PDF không tạo trùng, cập nhật môn đã có (Priority: P2)

Giữa học kỳ trường đổi lịch (đổi phòng, đổi thứ, thêm đợt mới) và người dùng tải PDF mới rồi nhập lại.
Ứng dụng nhận ra các môn đã có theo mã lớp và cập nhật chúng thay vì tạo môn mới. Môn hoặc buổi đã tạo
trước đó từ ảnh chụp lịch tuần cũng được nhận ra, không bị nhân đôi.

**Why this priority**: Lịch đổi giữa kỳ là chuyện thường; nhập lại phải an toàn, không làm rối dữ liệu.
Nhưng lần nhập đầu (User Story 1) quan trọng hơn.

**Independent Test**: Nhập PDF giả lập, lưu; sửa file giả lập (đổi phòng một quy tắc, thêm một dòng)
rồi nhập lại; kiểm tra bảng xem trước đánh dấu đúng "Đã có", "Thay đổi", "Mới" và sau khi lưu số môn
không đổi, chỉ phần thay đổi được cập nhật.

**Acceptance Scenarios**:

1. **Given** đã nhập PDF và lưu, **When** nhập lại đúng file đó, **Then** mọi môn hiện "Đã có, không
   thay đổi", mặc định không chọn, và lưu không tạo thêm môn hay buổi nào.
2. **Given** đã có môn cùng mã lớp, **When** PDF mới đổi phòng của một quy tắc, **Then** bảng xem trước
   hiện môn đó là "Thay đổi" kèm phần khác (phòng cũ → phòng mới); sau khi lưu, các buổi chưa diễn ra
   đổi sang phòng mới, các buổi đã qua giữ nguyên.
3. **Given** một buổi học đã được người dùng sửa riêng hoặc huỷ, **When** nhập lại PDF làm thay đổi môn
   đó, **Then** buổi đã sửa riêng hoặc đã huỷ được giữ nguyên; nếu buổi đó nằm ngoài lịch mới thì vẫn được
   giữ (không hỏi xác nhận) và được nêu trong cảnh báo sau khi lưu (FR-022).
4. **Given** đã có môn tạo từ ảnh lịch tuần với cùng tên và cùng mã lớp (ví dụ "2-2-26(N01)"), **When**
   nhập PDF, **Then** môn đó được nhận là "Đã có" hoặc "Thay đổi", không tạo môn thứ hai, và tên môn
   được sửa theo tên trong PDF nếu khác.
5. **Given** một môn có trong ứng dụng nhưng không có trong PDF mới, **When** lưu, **Then** môn đó giữ
   nguyên (không tự xoá).

---

### User Story 4 - Gắn nhãn E-Learning cho buổi học trực tuyến (Priority: P2)

Quy tắc có phòng chứa chữ "ONLINE" hoặc "Elearning" (không phân biệt hoa thường, có hay không có dấu
gạch) được tự gắn nhãn E-Learning trong bảng xem trước, để quy tắc tự tạo deadline cho môn E-Learning
áp dụng như khi gắn tay.

**Why this priority**: Giúp không bỏ sót deadline môn học trực tuyến, nhưng người dùng vẫn có thể tự gắn
nhãn nên không chặn luồng chính.

**Independent Test**: Nhập PDF giả lập có quy tắc phòng "ONLINE-Elearning"; kiểm tra nhãn E-Learning được
chọn sẵn; lưu và kiểm tra deadline tự tạo xuất hiện như với môn gắn nhãn tay.

**Acceptance Scenarios**:

1. **Given** quy tắc "16 - 18 (ONLINE-Elearning)", **When** xem trước, **Then** môn đó có nhãn
   E-Learning được chọn sẵn và phòng hiển thị "ONLINE-Elearning".
2. **Given** người dùng bỏ nhãn E-Learning ở bảng xem trước, **When** lưu, **Then** môn không có nhãn.
3. **Given** phòng "A6-103 (PC)", **When** xem trước, **Then** không gắn nhãn E-Learning.

---

### User Story 5 - Tên môn từ PDF giúp sửa tên khi nhập ảnh (Priority: P3)

Sau khi đã nhập PDF, người dùng chụp ảnh lịch tuần (ví dụ có ô "Lịch thi") và nhập như trước. Tên môn
OCR đọc sai vài ký tự ("Glao dlen nguòi máy") được tự sửa thành tên chuẩn lấy từ PDF ("Giao diện người
máy").

**Why this priority**: Cải thiện chất lượng nhập ảnh mà không phải sửa OCR, nhưng phụ thuộc User Story 1
và không chặn luồng chính.

**Independent Test**: Nhập PDF giả lập, sau đó nhập khối chữ OCR của ảnh tuần mẫu (có tên môn đọc sai);
kiểm tra tên môn trong bảng xem trước được sửa theo danh sách tên chuẩn.

**Acceptance Scenarios**:

1. **Given** danh sách tên chuẩn có "Giao diện người máy", **When** nhập ảnh có tên đọc thành
   "Glao dlen nguòi máy", **Then** tên được sửa thành "Giao diện người máy" kèm ghi chú "Đã sửa theo thời
   khoá biểu".
2. **Given** ô "Lịch thi: Tal uuhóa" trong ảnh tuần và tên chuẩn chứa "Tối ưu hóa", **When** nhập ảnh,
   **Then** tên buổi thi được sửa thành "Tối ưu hóa".
3. **Given** tên đọc được không đủ giống tên chuẩn nào, **When** nhập ảnh, **Then** giữ nguyên tên đọc
   được và vẫn tô vàng như hiện nay.

---

### Edge Cases

- File không phải PDF, PDF hỏng hoặc có mật khẩu → báo lỗi tiếng Việt dễ hiểu, không tạo gì.
- PDF chỉ chứa ảnh quét (không có chữ thật) → báo "File PDF này không có chữ, hãy dùng nhập từ ảnh",
  không chạy OCR.
- PDF có chữ nhưng không phải thời khoá biểu (không tìm thấy bảng có cột Mã HP, Lớp học phần, Thứ 2…CN,
  Thời gian) → báo "Không tìm thấy bảng thời khoá biểu trong file".
- Bảng dài sang nhiều trang, có hoặc không lặp lại hàng tiêu đề → đọc nối tiếp đủ các dòng.
- Chữ trong ô bị ngắt dòng ở bất kỳ vị trí nào (mã HP, tên lớp học phần, phòng có ngoặc lồng nhau) →
  ghép lại đúng; không tách thành hai dòng.
- Dòng thiếu khoảng ngày, chỉ có một ngày, hoặc ngày kết thúc trước ngày bắt đầu → quy tắc đó tô đỏ, bắt
  sửa hoặc bỏ chọn trước khi lưu.
- Ô thứ có tiết nhưng không có phòng, hoặc có phòng mà không đọc được tiết → tô vàng, cho sửa.
- Khoảng ngày bắt đầu không rơi vào thứ của quy tắc (ví dụ bắt đầu Thứ Hai nhưng quy tắc là Thứ Sáu) →
  buổi đầu tiên là ngày đúng thứ đầu tiên trong khoảng.
- Khoảng ngày không chứa ngày nào đúng thứ của quy tắc → cảnh báo "Quy tắc không có buổi nào", mặc
  định bỏ chọn.
- Hai quy tắc của cùng một môn chồng nhau về ngày, thứ và giờ → không tạo buổi trùng; bảng xem trước
  cảnh báo.
- Hai môn khác nhau trùng giờ cùng ngày → vẫn cho lưu, cảnh báo như khi thêm môn hiện nay.
- Khoảng ngày của PDF nằm một phần trong học kỳ đã có → đề xuất mở rộng học kỳ đó hoặc tạo học kỳ mới;
  người dùng chọn trước khi lưu.
- Có nhiều học kỳ chứa được khoảng ngày → đề xuất học kỳ chứa trọn khoảng ngày và ngắn nhất; người dùng
  đổi được.
- Cột Học phí, dòng "Tổng cộng", "Viết bằng chữ", ngày lập, chữ ký → bỏ qua, không thành môn.
- Dán (⌘V) khi clipboard không có file PDF → thông báo nhẹ như khi dán ảnh không có ảnh.
- File rất lớn (trên giới hạn dung lượng nhập hiện có) → từ chối trước khi đọc, báo giới hạn.

## Requirements *(mandatory)*

### Functional Requirements

**Nhận file**

- **FR-001**: Người dùng PHẢI nhập được file PDF bằng ba cách: kéo thả, chọn file, và dán (⌘V) file PDF đã
  sao chép (ví dụ từ Finder), ở cả trang Môn học lẫn màn nhập. Màn "Nhập từ ảnh" PHẢI đổi tên thành "Nhập
  lịch" và nhận cả ảnh lẫn PDF; thả hoặc dán PDF ở trang Môn học PHẢI mở màn này với file đó, giống cách ảnh
  đang được chuyển sang. Ảnh vẫn đi luồng nhận diện ảnh như hiện nay; PDF hiện bảng xem trước theo môn
  (FR-016).
- **FR-002**: File PDF PHẢI được đọc hoàn toàn trên máy từ nội dung chữ có sẵn trong file, KHÔNG dùng
  OCR, KHÔNG gửi file hay dữ liệu ra ngoài máy, và KHÔNG ghi file xuống đĩa; file chỉ nằm trong bộ nhớ
  trong lúc xử lý.
- **FR-003**: Ứng dụng PHẢI từ chối file không phải PDF, PDF hỏng, PDF có mật khẩu, PDF không có chữ,
  và PDF vượt giới hạn dung lượng nhập hiện có, bằng thông báo tiếng Việt chỉ rõ lý do và cách khắc phục.

**Đọc bảng**

- **FR-004**: Ứng dụng PHẢI nhận ra bảng thời khoá biểu theo hàng tiêu đề (Mã HP, Lớp học phần, Số TC,
  Thứ 2…Thứ 7, CN, Thời gian) và đọc mọi dòng của bảng, kể cả khi bảng kéo dài nhiều trang.
- **FR-005**: Với mỗi dòng, ứng dụng PHẢI đọc: mã học phần, tên lớp học phần, số tín chỉ, các ô thứ có
  nội dung (tiết đầu, tiết cuối, phòng) và khoảng ngày (bắt đầu, kết thúc). Chữ bị ngắt dòng trong một ô
  PHẢI được ghép lại thành một giá trị.
- **FR-006**: Tên lớp học phần PHẢI được tách thành tên môn và mã lớp theo cùng quy ước với nhập ảnh
  (ví dụ "Xử lý ngôn ngữ tự nhiên-2-2-26(N01)" → tên "Xử lý ngôn ngữ tự nhiên", mã lớp "2-2-26(N01)").
- **FR-007**: Mỗi môn (lớp học phần) được xác định bởi mã học phần cùng mã lớp; các dòng có cùng mã học
  phần và mã lớp PHẢI được gộp vào một môn. Hai lớp học phần khác mã lớp (ví dụ "N02" và "N02.TH1") là
  hai môn riêng.
- **FR-008**: Mỗi ô thứ có nội dung của một dòng PHẢI trở thành một quy tắc lặp hằng tuần riêng của môn:
  thứ đó, khoảng tiết, phòng của ô đó và khoảng ngày của dòng. Một dòng có nhiều ô thứ tạo nhiều quy tắc.
- **FR-009**: Ứng dụng PHẢI bỏ qua và KHÔNG lưu, KHÔNG hiển thị, KHÔNG ghi nhật ký: họ tên, mã sinh viên,
  khoá/lớp, ngành, học phí, tổng cộng, số tiền bằng chữ, ngày lập và phần chữ ký.
- **FR-010**: Ứng dụng PHẢI đọc dòng "Học kỳ … Năm học …" (nếu có) để đề xuất tên học kỳ; không đọc được
  thì đề xuất tên theo khoảng ngày.

**Tiết và giờ**

- **FR-011**: Cài đặt → Ca học PHẢI có bảng tiết: mỗi tiết (đánh số từ 1) có giờ bắt đầu và giờ kết thúc,
  người dùng xem và chỉnh được.
- **FR-012**: Giờ tiết mặc định PHẢI suy từ các ca hiện có: ca thứ k ứng với tiết 3k−2 đến 3k; mỗi tiết
  50 phút, nghỉ 5 phút giữa hai tiết liền nhau, tính từ giờ bắt đầu ca (ví dụ Ca 1 06:45–09:25 → tiết 1
  06:45–07:35, tiết 2 07:40–08:30, tiết 3 08:35–09:25). Ca có thời lượng khác 160 phút thì chia thành 3
  tiết bằng nhau với 2 khoảng nghỉ 5 phút, sao cho tiết cuối kết thúc đúng giờ kết thúc ca. Đổi giờ một
  ca PHẢI cập nhật lại các tiết của ca đó, trừ tiết người dùng đã chỉnh tay.
- **FR-013**: Tiết ngoài các ca hiện có không có giờ mặc định, trừ tiết 16–18 có mặc định 21:05–22:00
  (tiết 16 21:05–21:20, tiết 17 21:20–21:40, tiết 18 21:40–22:00, khớp với giờ cổng sinh viên ghi cho
  "Tiết 16-17" và "Tiết 16-18").
- **FR-014**: Khoảng tiết của một quy tắc PHẢI được đổi sang giờ: bắt đầu = giờ bắt đầu tiết đầu, kết thúc
  = giờ kết thúc tiết cuối. Nếu khoảng tiết trùng đúng một ca hoặc dãy ca liền nhau thì quy tắc gắn với
  (các) ca đó; ngược lại dùng giờ tuỳ chỉnh và ghi rõ khoảng tiết.
- **FR-015**: Quy tắc có tiết chưa có giờ PHẢI bị tô vàng kèm lý do và chặn Lưu đến khi người dùng nhập
  giờ; người dùng PHẢI có lựa chọn lưu giờ vừa nhập vào bảng tiết.

**Xem trước và chỉnh sửa**

- **FR-016**: Trước khi lưu, ứng dụng PHẢI luôn hiển thị bảng xem trước nhóm theo môn: tên môn, mã học
  phần, mã lớp, số tín chỉ, nhãn đề xuất, trạng thái (Mới / Đã có / Thay đổi); dưới mỗi môn là các quy
  tắc với khoảng ngày, thứ, tiết, ca, giờ, phòng và số buổi sẽ tạo.
- **FR-017**: Người dùng PHẢI sửa được tên môn, phòng, thứ, giờ (hoặc ca), khoảng ngày của từng quy tắc,
  thêm hoặc bỏ nhãn, bỏ chọn từng quy tắc hoặc cả môn; Huỷ thì không lưu gì.
- **FR-018**: Bảng xem trước PHẢI hiện học kỳ sẽ dùng: học kỳ đã có chứa trọn khoảng ngày của mọi quy tắc
  được chọn (nếu có nhiều, chọn học kỳ ngắn nhất), hoặc đề xuất tạo học kỳ mới với tên theo FR-010 và
  khoảng ngày từ ngày sớm nhất đến ngày muộn nhất của các quy tắc. Người dùng đổi được lựa chọn, kể cả
  mở rộng học kỳ đã có.
- **FR-019**: Quy tắc có lỗi (thiếu ngày, ngày kết thúc trước ngày bắt đầu, thiếu giờ) PHẢI tô đỏ hoặc
  vàng kèm lý do; nút Lưu chỉ bật khi mọi quy tắc được chọn đều hợp lệ.

**Lưu, chống trùng và cập nhật**

- **FR-020**: Mỗi môn có thể có nhiều quy tắc lặp hằng tuần; buổi học PHẢI được tạo cho mọi ngày đúng thứ
  trong khoảng ngày của từng quy tắc, với giờ và phòng của quy tắc đó. Ngày nằm ngoài mọi quy tắc (ví dụ
  kỳ nghỉ Tết) KHÔNG có buổi.
- **FR-020a**: Form thêm/sửa môn ở trang Môn học PHẢI hiện danh sách quy tắc lặp của môn và cho người dùng
  thêm, sửa (thứ, khoảng ngày, ca hoặc giờ, phòng), xoá từng quy tắc bằng tay; môn PHẢI còn ít nhất một
  quy tắc. Môn tạo tay mặc định có 1 quy tắc. Lưu thay đổi quy tắc cập nhật buổi học theo cách sửa môn
  hiện có của feature 001 (FR-013 của 001): buổi đã huỷ hoặc đã sửa riêng được giữ; buổi có ngoại lệ nằm
  ngoài lịch mới thì hỏi xác nhận trước khi xoá. (Quy tắc giữ buổi khi nhập PDF ở FR-022 không áp dụng cho
  sửa tay.)
- **FR-021**: Môn đã có được nhận ra trong học kỳ được chọn để nhập, khi trùng mã lớp (không phân biệt hoa
  thường) và (trùng mã học phần hoặc trùng tên môn không phân biệt hoa thường và dấu). Môn đã có PHẢI được
  cập nhật (tên, mã học phần, số tín chỉ, quy tắc) thay vì tạo môn mới.
- **FR-022**: Khi nhập PDF cập nhật môn đã có: buổi đã qua (ngày trước hôm nay) PHẢI giữ nguyên; buổi
  người dùng đã sửa riêng hoặc đã huỷ PHẢI giữ nguyên; buổi có ngoại lệ nằm ngoài lịch mới PHẢI được giữ lại
  (không hỏi xác nhận) và nêu trong cảnh báo sau khi lưu; các buổi chưa diễn ra còn lại được tạo, đổi hoặc
  xoá theo quy tắc mới.
- **FR-023**: Ứng dụng KHÔNG ĐƯỢC tạo buổi học trùng: hai buổi cùng môn, cùng ngày, cùng giờ bắt đầu chỉ
  được có một, kể cả khi hai quy tắc chồng nhau hoặc buổi đã có từ lần nhập ảnh trước.
- **FR-024**: Môn có trong ứng dụng nhưng không có trong PDF PHẢI được giữ nguyên.
- **FR-025**: Lưu PHẢI là một thao tác trọn vẹn: lỗi giữa chừng thì không có thay đổi nào được ghi.
- **FR-026**: Sau khi lưu, ứng dụng PHẢI báo số môn tạo mới, số môn cập nhật, số buổi tạo, số buổi bỏ qua
  vì đã có; các chức năng gắn với buổi học (deadline tự tạo, nhắc lịch, đồng bộ Lịch và Lời nhắc, sao
  lưu) áp dụng cho buổi mới như khi thêm môn bằng tay.

**Nhãn E-Learning**

- **FR-027**: Quy tắc có phòng chứa "ONLINE" hoặc "Elearning" / "E-Learning" (không phân biệt hoa thường)
  PHẢI làm môn được đề xuất nhãn E-Learning (chọn sẵn, bỏ được); khi lưu, môn có nhãn này được áp dụng
  quy tắc tự tạo deadline cho môn E-Learning hiện có.

**Tên môn chuẩn cho nhập ảnh**

- **FR-028**: Tên môn của mọi môn được lưu từ PDF PHẢI được ghi vào danh sách tên môn chuẩn (giữ cả khi
  môn bị xoá sau này, cho đến khi người dùng xoá danh sách trong Cài đặt).
- **FR-029**: Khi nhập lịch học hoặc lịch thi từ ảnh, tên đọc được PHẢI được so với danh sách tên chuẩn
  (không phân biệt dấu, hoa thường); đủ giống thì sửa thành tên chuẩn và ghi chú "Đã sửa theo thời khoá
  biểu"; không đủ giống thì giữ nguyên như hiện nay.

**Dữ liệu thử**

- **FR-030**: Test tự động PHẢI dùng file PDF giả lập cùng bố cục (họ tên, mã sinh viên, khoá/lớp giả);
  file PDF thật KHÔNG ĐƯỢC đưa vào git (thư mục mẫu PHẢI chặn file PDF).

### Key Entities

- **Môn học (lớp học phần)**: đã có; bổ sung mã học phần và số tín chỉ. Được xác định bởi mã học phần +
  mã lớp khi nhập PDF. Có một hoặc nhiều quy tắc lặp.
- **Quy tắc lặp hằng tuần của môn**: thuộc một môn; gồm thứ, khoảng ngày (bắt đầu, kết thúc), giờ bắt
  đầu/kết thúc hoặc ca (dãy ca), khoảng tiết gốc (nếu có), phòng. Sinh ra buổi học. Môn tạo theo cách cũ
  tương đương một môn có các quy tắc cùng khoảng ngày, giờ và phòng. Thêm, sửa, xoá được bằng tay trong
  form môn (FR-020a).
- **Tiết**: số thứ tự, giờ bắt đầu, giờ kết thúc, đánh dấu đã chỉnh tay hay suy từ ca.
- **Tên môn chuẩn**: tên môn, mã học phần (nếu có), thời điểm thêm; dùng để sửa tên khi nhập ảnh.
- **Bản xem trước nhập PDF** (chỉ trong bộ nhớ, không lưu): tên học kỳ đề xuất, khoảng ngày, danh sách môn
  với trạng thái và các quy tắc; không chứa thông tin cá nhân của sinh viên.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Với file PDF mẫu (bản thật trên máy và bản giả lập trong test), 100% môn, quy tắc, thứ,
  khoảng tiết, khoảng ngày, phòng và mã lớp trong bảng xem trước khớp đáp án viết tay (8 môn, 17 quy tắc).
- **SC-002**: Từ lúc thả file đến khi bảng xem trước hiện ra mất dưới 3 giây với file 1–3 trang.
- **SC-003**: Người dùng nhập xong cả học kỳ (thả file, xem, lưu) trong dưới 2 phút khi không cần sửa gì.
- **SC-004**: Sau khi lưu file mẫu, số buổi học tạo ra đúng bằng số ngày đúng thứ trong các khoảng ngày
  (không thiếu, không thừa, không có buổi trong kỳ nghỉ Tết).
- **SC-005**: Nhập lại cùng một file lần thứ hai tạo 0 môn và 0 buổi mới.
- **SC-006**: Không có họ tên, mã sinh viên, khoá/lớp, ngành hay học phí của sinh viên trong bất kỳ dữ liệu
  nào ứng dụng lưu, hiển thị hoặc ghi nhật ký (kiểm tra tự động bằng giá trị giả trong file thử).
- **SC-007**: Sau khi đã nhập PDF mẫu, nhập lại khối chữ OCR của ảnh tuần 30/11–06/12/2026: 100% tên môn
  của các buổi đọc được khớp tên chuẩn (hiện nay tên đúng ≥ 85% chỉ ở 2/7 buổi).

## Assumptions

- Bố cục PDF theo mẫu "Thời khóa biểu chính thức" của cổng sinh viên Phenikaa (Học kỳ 2, 2026–2027). Bố
  cục của trường khác hay dạng xuất khác ngoài phạm vi.
- PDF do cổng xuất có chữ thật; PDF quét ảnh không được hỗ trợ (người dùng dùng nhập từ ảnh).
- Mỗi ca hiện có gồm đúng 3 tiết; tiết 1–12 ứng với Ca 1–4. Khoảng nghỉ giữa các tiết trong ca là 5 phút
  (khớp 3 × 50 phút + 2 × 5 phút = 160 phút của mỗi ca mặc định). Tiết 13–15 chưa có giờ mặc định.
- Ca hiện có giữ nguyên ý nghĩa; quy tắc khớp đúng ca thì vẫn gắn ca để đổi giờ ca sau này cập nhật được
  buổi học như hiện nay.
- Ngày trong PDF theo dạng dd/mm/yyyy, giờ theo múi giờ Việt Nam như toàn ứng dụng.
- Môn tạo từ ảnh trước đây chỉ có mã lớp (không có mã học phần), nên việc nhận ra môn đã có dựa trên mã
  lớp kèm tên môn (FR-021).
- Dán (⌘V) file PDF hoạt động khi clipboard chứa file PDF (sao chép từ Finder); nếu môi trường không cho
  đọc file từ clipboard thì vẫn còn kéo thả và chọn file.
- Giới hạn dung lượng file dùng chung với nhập ảnh (20 MB).
- File PDF thật của người dùng nằm trong `samples/` trên máy, không đưa vào git; file giả lập trong test
  được tạo lại từ script trong repo.
