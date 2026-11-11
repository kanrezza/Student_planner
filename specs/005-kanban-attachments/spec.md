# Feature Specification: Bảng Kanban cho công việc và đính kèm file

**Feature Branch**: `005-kanban-attachments`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Thêm bảng Kanban và đính kèm file.
(1) Bảng Kanban: thêm chế độ xem dạng bảng ở trang Công việc (chuyển qua lại với dạng danh sách), mặc định 3 cột
Chưa làm / Đang làm / Xong. Task có thêm trạng thái "Đang làm". Kéo thả thẻ giữa các cột để đổi trạng thái và kéo
lên xuống để sắp thứ tự trong cột; kéo sang "Xong" tương đương tick hoàn thành (task lặp vẫn sinh lần kế tiếp ở cột
Chưa làm). Lọc bảng theo danh sách, nhãn, môn học. Thẻ hiện tiêu đề, hạn chót, nhãn màu, dấu Quan trọng, số file
đính kèm. Cột Xong mặc định chỉ hiện task xong trong 7 ngày gần nhất. Có thể dùng bàn phím để chuyển thẻ giữa các
cột.
(2) Đính kèm file: gắn file (PDF, ảnh, Word, PowerPoint, Excel, ...) vào task, môn học hoặc buổi học bằng kéo thả,
chọn file hoặc dán ⌘V. Mỗi file tối đa 50 MB (chỉnh được trong Cài đặt). Xem trước ảnh và PDF ngay trong app; các
loại khác mở bằng ứng dụng mặc định của macOS; tải về hoặc xoá được. File lưu trên máy, không phụ thuộc thư mục dự
án hay ổ SSD rời, và nằm trong sao lưu tự động (cảnh báo nếu tổng dung lượng sao lưu lớn). File trùng nội dung chỉ
lưu một bản. Xoá task vào Thùng rác thì file đi theo và khôi phục được; xoá hẳn thì file bị xoá nếu không còn chỗ
nào dùng. Tên file tìm được bằng ⌘F. Trong Cài đặt có mục xem tổng dung lượng file đính kèm.
Mọi dữ liệu chạy trên máy, giao diện tiếng Việt theo phong cách hiện tại."

## Bối cảnh

Trang Công việc hiện chỉ có dạng danh sách; task có hai trạng thái (chưa xong / đã xong qua dấu tick), thuộc một
danh sách, có thể có nhãn, hạn chót, mức Quan trọng, có thể lặp (feature 003) và có thể do app tự tạo từ buổi học
(deadline tự tạo). Xoá task đưa vào Thùng rác 30 ngày rồi mới xoá hẳn. ⌘F tìm trong task, môn, buổi học, lịch thi.
Sao lưu tự động (feature 003) chép toàn bộ dữ liệu ra thư mục người dùng chọn. App chạy trên máy, dữ liệu nằm trên
ổ trong của Mac, không phụ thuộc ổ SSD chứa mã nguồn.

Feature này thêm hai thứ độc lập với nhau: (1) chế độ xem bảng Kanban cho task, kèm trạng thái "Đang làm" và thứ tự
thủ công; (2) đính kèm file vào task, môn học, buổi học và buổi thi.

## Clarifications

### Session 2026-11-11

- Q: Buổi thi có gắn được file đính kèm không? → A: Có — buổi thi gắn được file (đề cương, đề cũ) giống môn học;
  các giả định khác giữ nguyên.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Xem và chuyển task trên bảng Kanban (Priority: P1)

Ở trang Công việc, người dùng bấm chuyển sang dạng "Bảng". Bảng có 3 cột Chưa làm / Đang làm / Xong. Người dùng kéo
thẻ "Làm báo cáo NLP" từ Chưa làm sang Đang làm khi bắt đầu, rồi sang Xong khi làm xong; kéo lên xuống để xếp việc
nào làm trước. Chuyển lại dạng "Danh sách" thì thấy cùng task với trạng thái đã đổi.

**Why this priority**: Đây là giá trị cốt lõi của phần Kanban: nhìn được việc đang dở và đổi trạng thái nhanh.

**Independent Test**: Tạo 3 task; mở dạng Bảng; kéo một thẻ sang Đang làm, một thẻ sang Xong, đổi thứ tự trong cột
Chưa làm; tải lại trang → trạng thái và thứ tự còn nguyên; dạng Danh sách hiện task "Xong" là đã tick.

**Acceptance Scenarios**:

1. **Given** trang Công việc ở dạng Danh sách, **When** bấm nút chuyển "Bảng", **Then** hiện 3 cột Chưa làm, Đang
   làm, Xong với đúng task theo trạng thái; app nhớ dạng xem đã chọn cho lần mở sau.
2. **Given** thẻ ở cột Chưa làm, **When** kéo sang cột Đang làm, **Then** task có trạng thái "Đang làm", thẻ nằm ở
   vị trí đã thả, và dạng Danh sách hiện dấu "Đang làm" cạnh task đó.
3. **Given** thẻ ở cột Đang làm, **When** kéo sang cột Xong, **Then** task được đánh dấu hoàn thành giống hệt khi
   tick ở dạng Danh sách (ghi thời điểm hoàn thành, gỡ nhắc, cập nhật bản sao trong Lời nhắc nếu đang đồng bộ).
4. **Given** task lặp hằng tuần ở cột Chưa làm, **When** kéo sang Xong, **Then** lần kế tiếp của chuỗi được sinh ra
   và xuất hiện ở cột Chưa làm.
5. **Given** thẻ ở cột Xong, **When** kéo về Chưa làm hoặc Đang làm, **Then** task bỏ trạng thái hoàn thành như khi
   bỏ tick (lần kế tiếp của task lặp đã sinh thì vẫn giữ, như hành vi bỏ tick hiện có).
6. **Given** cột Chưa làm có thẻ A, B, C, **When** kéo C lên trên A, **Then** thứ tự thành C, A, B và giữ nguyên
   sau khi tải lại.
7. **Given** cột Xong có task xong hôm nay và task xong 10 ngày trước, **When** mở bảng, **Then** chỉ thấy task xong
   hôm nay; bấm "Hiện tất cả" ở cột Xong thì thấy cả task cũ.

---

### User Story 2 - Lọc bảng và đọc nhanh thông tin trên thẻ (Priority: P1)

Người dùng lọc bảng chỉ còn task của danh sách "Học tập", nhãn "Gấp", hoặc của môn "Xử lý ngôn ngữ tự nhiên". Mỗi
thẻ cho biết tiêu đề, hạn chót, nhãn màu, dấu Quan trọng và số file đính kèm, không cần mở chi tiết.

**Why this priority**: Không lọc thì bảng gộp mọi task của mọi danh sách, khó dùng khi có nhiều việc.

**Independent Test**: Tạo task ở hai danh sách, có nhãn và gắn môn khác nhau; lọc theo từng tiêu chí → chỉ còn task
khớp; thẻ hiện đủ các thông tin đã nêu.

**Acceptance Scenarios**:

1. **Given** task thuộc nhiều danh sách, **When** chọn lọc danh sách "Học tập", **Then** cả 3 cột chỉ còn task của
   danh sách đó; bỏ lọc thì hiện lại tất cả.
2. **Given** bộ lọc nhãn "Gấp" và môn "Xử lý ngôn ngữ tự nhiên" cùng bật, **When** xem bảng, **Then** chỉ hiện task
   thoả cả hai điều kiện.
3. **Given** task có hạn chót quá hạn, nhãn màu, mức Quan trọng và 2 file đính kèm, **When** xem thẻ, **Then** thẻ
   hiện tiêu đề, hạn chót tô màu quá hạn, chấm/nhãn màu, dấu Quan trọng và biểu tượng kẹp giấy kèm số 2.
4. **Given** đang lọc, **When** kéo thẻ sang cột khác, **Then** thẻ đổi trạng thái và vẫn hiện (vì vẫn khớp bộ lọc).
5. **Given** bộ lọc đã chọn, **When** rời trang rồi quay lại, **Then** bộ lọc vẫn giữ.

---

### User Story 3 - Dùng bảng bằng bàn phím (Priority: P2)

Người dùng chọn một thẻ bằng phím mũi tên, nhấn phím tắt để chuyển thẻ sang cột bên trái/phải hoặc lên/xuống trong
cột, không cần chuột.

**Why this priority**: Nhanh hơn với người hay dùng phím tắt (app đã có hệ phím tắt) và cần cho trợ năng.

**Independent Test**: Chỉ dùng bàn phím: di chuyển chọn giữa các thẻ, chuyển một thẻ sang Đang làm rồi Xong, đổi thứ
tự trong cột; kết quả giống kéo thả.

**Acceptance Scenarios**:

1. **Given** bảng đang mở, **When** nhấn mũi tên, **Then** vùng chọn đi qua các thẻ (trái/phải đổi cột, lên/xuống
   trong cột) và thẻ đang chọn có viền rõ.
2. **Given** thẻ đang chọn ở Chưa làm, **When** nhấn ⌘→ (hoặc ⌥→), **Then** thẻ sang Đang làm, vẫn được chọn; nhấn
   tiếp thì sang Xong (hoàn thành).
3. **Given** thẻ đang chọn, **When** nhấn ⌘↑ / ⌘↓, **Then** thẻ đổi chỗ với thẻ trên/dưới trong cột.
4. **Given** thẻ đang chọn, **When** nhấn Enter, **Then** mở bảng chi tiết task như khi bấm vào thẻ.
5. **Given** dùng trình đọc màn hình, **When** chuyển thẻ, **Then** có thông báo "Đã chuyển … sang Đang làm".

---

### User Story 4 - Đính kèm file vào task, môn học, buổi học, buổi thi (Priority: P1)

Người dùng kéo file "De_cuong_NLP.pdf" vào bảng chi tiết của môn "Xử lý ngôn ngữ tự nhiên", kéo slide bài 3 vào buổi
học thứ Ba, kéo đề cương ôn tập và đề thi năm trước vào buổi thi cuối kỳ của môn đó, và dán (⌘V) ảnh chụp đề bài
vào task "Làm bài tập tuần 5". Mỗi nơi hiện danh sách file đã gắn.

**Why this priority**: Giá trị cốt lõi của phần đính kèm: tài liệu nằm cạnh việc cần làm.

**Independent Test**: Gắn 1 file vào mỗi loại (task, môn, buổi học, buổi thi) bằng 3 cách (kéo thả, chọn file, ⌘V); tải lại app →
file vẫn còn, đúng tên, đúng dung lượng, mở ra đúng nội dung.

**Acceptance Scenarios**:

1. **Given** bảng chi tiết task đang mở, **When** kéo một file PDF 3 MB vào, **Then** file xuất hiện trong mục "File
   đính kèm" với tên, loại, dung lượng, ngày thêm; số file trên thẻ Kanban tăng 1.
2. **Given** bảng chi tiết môn học, **When** bấm "Thêm file" và chọn 3 file cùng lúc, **Then** cả 3 được gắn.
3. **Given** đã chép một file trong Finder (hoặc ảnh chụp màn hình trong clipboard), **When** mở chi tiết buổi học và
   nhấn ⌘V, **Then** file/ảnh được gắn vào buổi học đó.
4. **Given** file 60 MB và giới hạn 50 MB, **When** gắn, **Then** từ chối với thông báo "File vượt quá 50 MB (giới
   hạn trong Cài đặt → File đính kèm)", không lưu gì.
5. **Given** gắn cùng một file (cùng nội dung) vào task và vào môn học, **When** xem tổng dung lượng, **Then** file
   chỉ được tính và lưu một lần, nhưng hiện ở cả hai nơi.
6. **Given** gắn file trùng tên khác nội dung vào cùng một task, **When** lưu, **Then** cả hai đều được giữ, tên hiển
   thị phân biệt bằng hậu tố "(2)".
7. **Given** bảng chi tiết buổi thi "Xử lý ngôn ngữ tự nhiên – lần 1", **When** kéo vào "De_cuong_on_tap.pdf" và
   "De_thi_2025.pdf", **Then** cả hai hiện trong mục "File đính kèm" của buổi thi; dòng buổi thi ở trang Lịch thi hiện
   biểu tượng kẹp giấy kèm số 2.
8. **Given** đang gắn file lớn, **When** chờ, **Then** có thanh tiến trình; lỗi giữa chừng thì báo lỗi và không để lại
   file dở.

---

### User Story 5 - Xem, mở, tải về và xoá file đính kèm (Priority: P1)

Người dùng bấm vào file ảnh hoặc PDF để xem ngay trong app; bấm vào file Word/PowerPoint/Excel thì mở bằng ứng dụng
mặc định của macOS; tải file về thư mục Tải về; xoá file không cần nữa.

**Why this priority**: Gắn file mà không xem/mở được thì không có giá trị.

**Independent Test**: Gắn một ảnh, một PDF, một file .docx; xem trước ảnh và PDF trong app; mở .docx bằng ứng dụng mặc
định; tải PDF về; xoá ảnh → biến khỏi danh sách và tổng dung lượng giảm.

**Acceptance Scenarios**:

1. **Given** file ảnh (PNG/JPEG/HEIC/GIF/WebP), **When** bấm vào, **Then** mở khung xem trước trong app, phóng to/thu
   nhỏ được, Esc để đóng; có nút chuyển sang file kế tiếp cùng nơi gắn.
2. **Given** file PDF nhiều trang, **When** bấm vào, **Then** xem trước trong app, cuộn được qua các trang.
3. **Given** file .docx/.pptx/.xlsx hoặc loại khác, **When** bấm "Mở", **Then** file mở bằng ứng dụng mặc định của
   macOS (ví dụ Pages/Word, Keynote/PowerPoint, Numbers/Excel); máy không có ứng dụng phù hợp thì macOS hỏi chọn.
4. **Given** bất kỳ file nào, **When** bấm "Tải về", **Then** file được lưu vào thư mục Tải về với tên gốc (trùng tên
   thì macOS thêm hậu tố).
5. **Given** file đang gắn, **When** bấm "Xoá" và xác nhận, **Then** file biến khỏi nơi đó; nội dung chỉ bị xoá khỏi
   máy nếu không còn nơi nào khác dùng.
6. **Given** đang dùng app trên trình duyệt (không phải app macOS), **When** bấm "Mở" với file .docx, **Then** file
   được tải về để người dùng tự mở (trình duyệt không mở thẳng được bằng ứng dụng macOS).

---

### User Story 6 - File đi theo Thùng rác, sao lưu và tìm kiếm (Priority: P2)

Người dùng xoá task có file vào Thùng rác rồi khôi phục: file vẫn còn. Xoá hẳn: file biến mất (nếu không nơi nào
khác dùng). Sao lưu tự động có cả file; khôi phục bản sao lưu thì file trở lại. ⌘F gõ "de cuong" tìm ra file
"Đề cương NLP.pdf" và đưa tới nơi đang gắn file đó.

**Why this priority**: Đảm bảo không mất file và tìm lại được; phụ thuộc vào US4.

**Independent Test**: Gắn file vào task → xoá vào Thùng rác → khôi phục → file còn; xoá hẳn → file mất khỏi tổng dung
lượng; sao lưu rồi khôi phục vào máy khác (hoặc sau khi xoá dữ liệu) → file mở được; ⌘F tìm theo tên không dấu.

**Acceptance Scenarios**:

1. **Given** task có 2 file, **When** xoá task vào Thùng rác, **Then** file không hiện ở nơi khác và vẫn được giữ;
   **When** khôi phục task, **Then** 2 file trở lại đầy đủ.
2. **Given** task trong Thùng rác, **When** xoá hẳn (hoặc hết 30 ngày tự xoá), **Then** file của task bị xoá khỏi máy
   trừ file cùng nội dung đang được nơi khác dùng.
3. **Given** môn học có file, **When** xoá môn học (cùng các buổi học của nó), **Then** file của môn và các buổi bị xoá
   theo quy tắc trên; hộp xác nhận xoá môn ghi rõ số file sẽ bị xoá.
4. **Given** buổi thi có file, **When** xoá buổi thi, **Then** hộp xác nhận ghi rõ số file sẽ bị xoá; xác nhận thì file
   bị xoá theo quy tắc trên (buổi thi không có Thùng rác).
5. **Given** sao lưu tự động đang bật, **When** đến lần sao lưu, **Then** bản sao lưu chứa cả file đính kèm; khôi phục
   bản đó thì mọi file trở lại, mở được.
6. **Given** tổng dung lượng file đính kèm vượt ngưỡng cảnh báo (mặc định 1 GB), **When** sao lưu chạy hoặc mở Cài
   đặt → Sao lưu, **Then** có cảnh báo nhẹ kèm dung lượng ước tính của mỗi bản sao lưu; sao lưu vẫn chạy.
7. **Given** file "Đề cương NLP.pdf" gắn vào môn học, **When** nhấn ⌘F và gõ "de cuong", **Then** kết quả có nhóm
   "File" hiện tên file, nơi gắn (môn "Xử lý ngôn ngữ tự nhiên"); chọn kết quả thì mở chi tiết môn đó và tô sáng file.

---

### User Story 7 - Quản lý dung lượng và giới hạn trong Cài đặt (Priority: P3)

Người dùng mở Cài đặt → File đính kèm: thấy tổng dung lượng, số file, file lớn nhất; đổi giới hạn mỗi file.

**Why this priority**: Cần nhưng không chặn việc dùng hằng ngày.

**Independent Test**: Gắn vài file; mở mục Cài đặt → số liệu khớp; đổi giới hạn thành 10 MB → gắn file 20 MB bị từ
chối.

**Acceptance Scenarios**:

1. **Given** có file đính kèm, **When** mở Cài đặt → File đính kèm, **Then** thấy tổng dung lượng (đã tính gộp bản trùng
   nội dung), số file, và danh sách 10 file lớn nhất kèm nơi gắn; bấm vào một dòng thì mở nơi gắn file đó.
2. **Given** giới hạn 50 MB, **When** đổi thành 10 MB, **Then** áp dụng cho file gắn sau đó; file đã gắn không bị ảnh
   hưởng.
3. **Given** giá trị giới hạn ngoài 1–500 MB, **When** lưu, **Then** báo lỗi ngay dưới ô.

---

### Edge Cases

- Task tự tạo từ buổi học (deadline tự tạo) hiện trên bảng như task thường; kéo sang Xong là hoàn thành nó.
- Task lặp: chỉ lần đang chờ hiện ở Chưa làm/Đang làm; các lần đã xong hiện ở Xong theo quy tắc 7 ngày.
- Task "Đang làm" có hạn chót đã qua: vẫn ở cột Đang làm, hạn chót tô màu quá hạn.
- Kéo thẻ sang Xong rồi bấm "Hoàn tác" trên thông báo: task trở lại cột và vị trí cũ (lần kế tiếp của task lặp vừa
  sinh bị xoá nếu chưa bị sửa).
- Task mới tạo (ở Danh sách, thêm nhanh, tự tạo) vào cột Chưa làm ở đầu cột; task bỏ tick ở Danh sách quay về Chưa
  làm (không nhớ trạng thái Đang làm cũ).
- Task trong danh sách bị ẩn bởi bộ lọc vẫn giữ vị trí; đổi thứ tự khi đang lọc chỉ sắp lại tương đối giữa các thẻ
  đang hiện.
- Cột rỗng hiện chỗ trống có chữ "Kéo thẻ vào đây".
- Hơn 200 thẻ trong một cột: bảng vẫn cuộn mượt.
- Bản sao trong Lời nhắc của macOS không có trạng thái "Đang làm": chỉ đồng bộ hoàn thành/chưa hoàn thành như hiện nay.
- Gắn file 0 byte: được (một số tài liệu trống hợp lệ); file không đọc được (quyền, file iCloud chưa tải): báo lỗi rõ.
- Gắn thư mục (kéo thả cả thư mục): từ chối, báo "Chỉ gắn được file, không gắn thư mục".
- Tên file có ký tự đặc biệt, dấu tiếng Việt dạng tổ hợp (NFD từ Finder): hiển thị và tìm kiếm đúng; tải về giữ tên.
- Đổi tên file đính kèm: đổi được tên hiển thị, không đổi nội dung.
- Buổi học bị xoá do sửa lịch môn (đổi thứ, đổi khoảng ngày) mà có file: file chuyển sang môn học tương ứng kèm thông
  báo, không mất.
- Ổ trong của Mac gần đầy: gắn file thất bại với thông báo "Ổ đĩa không đủ chỗ", không để lại file dở.
- Hai cửa sổ cùng mở (app và trình duyệt): thay đổi ở một nơi hiện ở nơi kia sau khi làm mới dữ liệu như các thay đổi
  khác.
- File trùng nội dung bị xoá ở một nơi trong khi nơi khác vẫn dùng: nội dung còn nguyên.
- Khôi phục bản sao lưu cũ (trước feature này): không có file đính kèm, app chạy bình thường.
- Xem trước PDF có mật khẩu hoặc hỏng: báo "Không xem trước được", vẫn mở bằng ứng dụng mặc định / tải về được.
- File có thể chứa mã độc (ví dụ .app, .command, .exe): không mở trực tiếp từ app mà chỉ cho tải về, kèm cảnh báo.

## Requirements *(mandatory)*

### Functional Requirements

**Trạng thái và thứ tự task**

- **FR-001**: Task PHẢI có một trong ba trạng thái: Chưa làm, Đang làm, Xong. "Xong" là trạng thái hoàn thành hiện có
  (có thời điểm hoàn thành); task hiện có khi nâng cấp mang trạng thái Chưa làm hoặc Xong theo dấu tick.
- **FR-002**: Chuyển một task sang Xong (bằng kéo thả, bàn phím, hay tick) PHẢI có cùng hệ quả với tick hoàn thành
  hiện nay: ghi thời điểm hoàn thành, tắt nhắc, đồng bộ Lời nhắc (nếu bật), sinh lần kế tiếp của task lặp.
- **FR-003**: Chuyển một task từ Xong về Chưa làm/Đang làm PHẢI có cùng hệ quả với bỏ tick hiện nay.
- **FR-004**: Dạng Danh sách PHẢI hiện dấu "Đang làm" cho task ở trạng thái đó và cho phép đổi trạng thái này trong
  bảng chi tiết task (ngoài kéo thả trên bảng).
- **FR-005**: Mỗi task PHẢI có vị trí trong cột của trạng thái mình; thứ tự do người dùng sắp PHẢI được lưu ngay và giữ
  sau khi khởi động lại. Thứ tự này chỉ áp dụng cho dạng Bảng; dạng Danh sách giữ cách sắp xếp hiện có.
- **FR-006**: Task mới hoặc vừa chuyển sang một cột mà không chỉ rõ vị trí PHẢI nằm đầu cột đó.

**Bảng Kanban**

- **FR-007**: Trang Công việc PHẢI có nút chuyển giữa "Danh sách" và "Bảng"; lựa chọn PHẢI được nhớ trên máy.
- **FR-008**: Bảng PHẢI có đúng 3 cột theo thứ tự Chưa làm, Đang làm, Xong, mỗi cột hiện số thẻ đang hiển thị.
- **FR-009**: Kéo thả thẻ giữa các cột và trong một cột PHẢI đổi trạng thái/thứ tự, kèm vị trí chèn được hiển thị
  trong khi kéo; thay đổi PHẢI được lưu ngay, lỗi lưu thì thẻ trở về chỗ cũ và có thông báo.
- **FR-010**: Cột Xong mặc định chỉ hiện task hoàn thành trong 7 ngày gần nhất (tính theo ngày lịch, giờ Việt Nam) và
  có nút "Hiện tất cả" / "Chỉ 7 ngày gần nhất"; cột Xong sắp theo thời điểm hoàn thành mới nhất trước nếu người dùng
  chưa sắp tay.
- **FR-011**: Bảng PHẢI lọc được theo danh sách (một hoặc nhiều), nhãn (một hoặc nhiều, khớp bất kỳ) và môn học (task
  gắn với môn qua buổi học tự tạo hoặc gắn tay); các bộ lọc khác loại kết hợp theo "và"; bộ lọc được nhớ trên máy.
- **FR-012**: Thẻ PHẢI hiện tiêu đề, hạn chót (định dạng Việt Nam, tô màu khi quá hạn hoặc hôm nay), nhãn màu, dấu
  Quan trọng, biểu tượng lặp nếu là task lặp, và số file đính kèm khi > 0; bấm thẻ mở bảng chi tiết task hiện có.
- **FR-013**: Bảng PHẢI dùng được hoàn toàn bằng bàn phím: mũi tên để di chuyển vùng chọn; ⌘← / ⌘→ chuyển thẻ sang cột
  kề; ⌘↑ / ⌘↓ đổi thứ tự; Enter mở chi tiết; phím X đánh dấu Xong/bỏ Xong (Space dành cho nhấc/thả thẻ khi kéo bằng bàn phím). Các phím này PHẢI có trong bảng phím tắt
  của app và có thông báo cho trình đọc màn hình.
- **FR-014**: Sau khi chuyển một thẻ sang Xong PHẢI có thông báo kèm nút "Hoàn tác" trong vài giây.
- **FR-015**: Bảng không hiện task trong Thùng rác; tạo task nhanh ngay trên đầu cột Chưa làm (và Đang làm) bằng ô
  "+ Thêm" dùng cùng cách gõ nhanh hiện có.

**Đính kèm file**

- **FR-016**: Người dùng PHẢI gắn được file vào task, môn học, buổi học và buổi thi bằng kéo thả vào bảng chi tiết, nút "Thêm
  file" (chọn nhiều file), và ⌘V (file đã chép trong Finder hoặc ảnh trong clipboard) khi bảng chi tiết đang mở.
- **FR-017**: Mọi loại file PHẢI gắn được; giới hạn mỗi file mặc định 50 MB, chỉnh được trong Cài đặt trong khoảng
  1–500 MB; vượt giới hạn thì từ chối với thông báo nêu giới hạn và chỗ đổi.
- **FR-018**: Mỗi file gắn PHẢI lưu tên gốc (đổi tên hiển thị được), loại, dung lượng, thời điểm thêm, nơi gắn.
- **FR-019**: Nội dung file PHẢI được lưu trên ổ trong của Mac cùng chỗ với dữ liệu app, không nằm trong thư mục dự
  án hay ổ rời; việc ghi PHẢI an toàn trước sự cố (không bao giờ để lại file dở được ghi nhận là đã gắn).
- **FR-020**: File cùng nội dung PHẢI chỉ lưu một bản; mỗi nơi gắn là một mục riêng (tên hiển thị riêng); nội dung chỉ
  bị xoá khỏi máy khi không còn mục nào (kể cả trong Thùng rác) trỏ tới.
- **FR-021**: Ảnh (PNG, JPEG, HEIC, GIF, WebP) và PDF PHẢI xem trước được trong app; các loại khác mở bằng ứng dụng
  mặc định của macOS (trong app macOS) hoặc được tải về (khi dùng trình duyệt).
- **FR-022**: Mọi file PHẢI tải về được với tên hiển thị; file thực thi (.app, .command, .sh, .exe, .pkg, .dmg …) chỉ
  tải về được, không mở trực tiếp, kèm cảnh báo.
- **FR-023**: Xoá một file đính kèm PHẢI hỏi xác nhận; xoá task vào Thùng rác giữ file và khôi phục task thì file trở
  lại; xoá hẳn task (bằng tay hay tự xoá sau 30 ngày) xoá các mục đính kèm của nó theo FR-020.
- **FR-024**: Xoá môn học PHẢI xoá mục đính kèm của môn và của các buổi học của môn (theo FR-020), hộp xác nhận nêu số
  file; buổi học bị xoá do sửa lịch môn PHẢI chuyển file của buổi sang môn học, kèm thông báo. Xoá buổi thi PHẢI
  xoá mục đính kèm của buổi thi (theo FR-020), hộp xác nhận nêu số file. Xoá học kỳ, hoặc thu hẹp học kỳ làm môn bị xoá,
  mà có file đính kèm PHẢI hỏi xác nhận nêu số file trước khi xoá. Nhập lại lịch thi từ ảnh mà buổi thi đã có
  (trùng) thì giữ nguyên file của buổi thi đó.
- **FR-025**: Sao lưu tự động và sao lưu tay PHẢI chứa cả nội dung file đính kèm; khôi phục PHẢI đưa file trở lại; bản
  sao lưu cũ không có file vẫn khôi phục được.
- **FR-026**: Khi tổng dung lượng file đính kèm vượt ngưỡng (mặc định 1 GB, chỉnh được), Cài đặt → Sao lưu và thông báo
  sau lần sao lưu tự động (tối đa một lần mỗi ngày) PHẢI cảnh báo nhẹ kèm dung lượng ước tính mỗi bản sao lưu; không chặn sao lưu.
- **FR-027**: ⌘F PHẢI tìm theo tên file (không phân biệt hoa thường, không dấu), hiện nhóm "File" với tên và nơi gắn;
  chọn kết quả mở nơi gắn và tô sáng file. File của task trong Thùng rác không xuất hiện.
- **FR-028**: Cài đặt PHẢI có mục "File đính kèm": tổng dung lượng (tính một lần cho nội dung trùng), số file, 10 file
  lớn nhất kèm nơi gắn, ô giới hạn mỗi file, ô ngưỡng cảnh báo sao lưu.
- **FR-029**: Nội dung file KHÔNG được gửi ra ngoài máy; xem trước và tìm kiếm chạy hoàn toàn trên máy; tìm kiếm chỉ
  theo tên file, không đọc nội dung file.
- **FR-030**: Bảng chi tiết task, môn học, buổi học, buổi thi PHẢI có mục "File đính kèm" (danh sách, nút Thêm file,
  vùng thả); thẻ Kanban, dòng task ở dạng Danh sách, dòng môn học và dòng buổi thi PHẢI hiện số file khi > 0.

### Key Entities

- **Task (mở rộng)**: thêm trạng thái (Chưa làm / Đang làm / Xong) và vị trí trên bảng trong cột của trạng thái.
- **Nội dung file**: một bản nội dung duy nhất trên máy, nhận biết theo dấu vân tay nội dung; có dung lượng, loại.
- **Mục đính kèm**: liên kết một nội dung file với đúng một nơi gắn (task, môn học, buổi học hoặc buổi thi); có tên hiển thị,
  thời điểm thêm; theo task vào/ra Thùng rác.
- **Cài đặt đính kèm**: giới hạn mỗi file, ngưỡng cảnh báo dung lượng sao lưu.
- **Tuỳ chọn xem (trên máy)**: dạng xem Danh sách/Bảng, bộ lọc bảng, trạng thái "Hiện tất cả" của cột Xong.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Chuyển một task sang trạng thái khác trên bảng mất ≤ 1 thao tác kéo thả hoặc 1 phím tắt, và thay đổi
  hiện ở dạng Danh sách ngay khi chuyển dạng xem.
- **SC-002**: Với 300 task, mở dạng Bảng và áp dụng một bộ lọc hiện kết quả trong dưới 1 giây.
- **SC-003**: 100% thao tác đổi trạng thái/thứ tự còn nguyên sau khi khởi động lại app hoặc tắt máy đột ngột.
- **SC-004**: Kéo sang Xong cho kết quả giống hệt tick hoàn thành trong 100% trường hợp đã kiểm thử (task thường, task
  lặp, task tự tạo, task có nhắc).
- **SC-005**: Gắn một file 50 MB hoàn tất trong dưới 5 giây; xem trước ảnh/PDF dưới 10 MB mở trong dưới 2 giây.
- **SC-006**: Gắn cùng một file vào 5 nơi chỉ làm tổng dung lượng tăng đúng một lần dung lượng file.
- **SC-007**: Sau khi khôi phục một bản sao lưu, 100% file đính kèm mở được và khớp nội dung gốc.
- **SC-008**: Không có file nội dung nào còn trên máy mà không được mục đính kèm nào (kể cả trong Thùng rác) dùng, sau
  khi xoá hẳn hoặc dọn Thùng rác.
- **SC-009**: Tìm tên file bằng ⌘F (gõ không dấu) trả kết quả trong dưới 1 giây với 1.000 file.
- **SC-010**: App vẫn chạy đầy đủ khi tháo ổ SSD chứa mã nguồn, kể cả xem và gắn file.

## Assumptions

- Bảng có đúng 3 cột cố định; thêm/đổi tên/ẩn cột, giới hạn số thẻ mỗi cột (WIP limit) nằm ngoài phạm vi.
- Bảng hiện task của mọi danh sách (không phân trang); lọc theo danh sách để thu hẹp. Task không hạn chót vẫn hiện.
- "Môn học" của task: task tự tạo từ buổi học thuộc môn của buổi đó; task thường không có môn trừ khi người dùng gắn
  môn trong chi tiết task (thêm ô chọn môn tuỳ chọn trong bảng chi tiết task).
- Trạng thái "Đang làm" không có nhắc riêng và không đồng bộ sang Lời nhắc (Lời nhắc chỉ có hoàn thành / chưa).
- Phím tắt cụ thể có thể điều chỉnh khi lập kế hoạch nếu trùng phím tắt hiện có; yêu cầu là có đủ thao tác bằng phím.
- File đính kèm cho task, môn học, buổi học và buổi thi; danh sách, học kỳ không có đính kèm trong feature này.
- Không có xem trước cho Word/PowerPoint/Excel trong app (dùng ứng dụng mặc định); không đọc nội dung file để tìm kiếm.
- Không giới hạn tổng dung lượng; chỉ giới hạn mỗi file và cảnh báo khi lớn (dung lượng ổ là giới hạn thực tế).
- Mở bằng ứng dụng mặc định chỉ có trong app macOS; trên trình duyệt thì tải về.
- Khôi phục từ Thùng rác áp dụng cho task (môn học, buổi học và buổi thi hiện không có Thùng rác; xoá môn hoặc buổi thi
  là xoá hẳn có xác nhận).
- Ngưỡng cảnh báo sao lưu mặc định 1 GB tổng dung lượng file đính kèm.
