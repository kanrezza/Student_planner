# Feature Specification: Quản lý công việc và lịch học cá nhân

**Feature Branch**: `001-task-class-scheduler`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Xây ứng dụng quản lý công việc và lịch học cá nhân. Công việc (task):
tạo, sửa, xoá, đánh dấu hoàn thành; mỗi task có tiêu đề, ghi chú, hạn chót, mức ưu tiên
(cao/trung bình/thấp) và thuộc một danh sách (ví dụ: Học tập, Cá nhân, Công việc). Lịch học: thêm
môn học với thứ trong tuần, giờ bắt đầu, giờ kết thúc, phòng học, ngày bắt đầu và ngày kết thúc học
kỳ; môn học tự lặp lại hàng tuần trong khoảng thời gian đó. Có thể nhập nhiều môn cùng lúc cho cả
tháng hoặc cả học kỳ. Có thể sửa hoặc huỷ một buổi học riêng lẻ (ví dụ nghỉ lễ) mà không ảnh hưởng
các buổi khác. Xem lịch: chế độ xem theo ngày, tuần và tháng, hiển thị cả task (theo hạn chót) và
buổi học; màu sắc khác nhau theo môn học hoặc danh sách. Trang "Hôm nay" liệt kê các buổi học và
task của ngày hôm nay. Thông báo nhắc trước buổi học và trước hạn chót của task (thời gian nhắc có
thể chỉnh). Ngoài phạm vi: không cần đồng bộ nhiều thiết bị, không chia sẻ với người khác, không
cần đăng nhập."

## Clarifications

### Session 2026-11-04

- Q: Khi nhận diện ảnh chạy hoàn toàn trên máy, mức độ chính xác nào là đủ? → A: 80% buổi học
  đúng hoàn toàn với ảnh rõ nét; mọi trường sai phải được đánh dấu hoặc dễ phát hiện.
- Q: Có lưu "Học kỳ" thành mục riêng hay mỗi môn tự có khoảng ngày? → A: Có mục "Học kỳ" (tên,
  ngày bắt đầu, ngày kết thúc); mỗi môn thuộc một học kỳ, mặc định dùng khoảng ngày của học kỳ và
  vẫn sửa được riêng.
- Q: Thông báo nhắc có cần hiện khi ứng dụng hoặc Mac đã tắt không? → A: Có, nhắc cả trên iPhone:
  ứng dụng ghi lời nhắc vào Lịch/Lời nhắc của macOS để iCloud đồng bộ sang iPhone, iPhone nhắc
  đúng giờ kể cả khi Mac tắt (constitution v2.2.0, Nguyên tắc IV). Thông báo của trình duyệt chỉ
  dùng làm dự phòng khi người dùng chưa bật đồng bộ.
- Q: Task chỉ có ngày hạn chót (không có giờ) thì nhắc lúc nào? → A: 08:00 sáng ngày hạn chót, giờ
  này chỉnh được trong cài đặt.
- Q: Có cần bản tóm tắt mỗi sáng và mức "Quan trọng" cho nhắc không? → A: Có (bổ sung vào US7):
  thông báo tổng hợp hằng ngày (mặc định 05:00, bật/tắt được, ngày trống không gửi, tạo sẵn trước
  nhiều ngày trong Lịch để iPhone nhận khi Mac gập); công tắc "Quan trọng" cho task, buổi học, buổi
  thi; mục quan trọng nhắc nhiều mốc (mặc định 1 ngày, 3 giờ, 1 giờ, 15 phút), buổi thi mặc định
  quan trọng và thêm mốc 7 ngày (FR-065 đến FR-070).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quản lý công việc (task) theo danh sách (Priority: P1)

Người dùng tạo task với tiêu đề, ghi chú, hạn chót, mức ưu tiên và chọn danh sách (Học tập, Cá nhân,
Công việc hoặc danh sách tự tạo). Người dùng có thể sửa, xoá task và đánh dấu hoàn thành / bỏ hoàn
thành. Task được nhóm theo danh sách và vẫn còn nguyên sau khi tắt và mở lại ứng dụng.

**Why this priority**: Đây là chức năng dùng hằng ngày và tự nó đã đủ giá trị để thay thế một
ứng dụng ghi chú việc cần làm; không phụ thuộc vào lịch học.

**Independent Test**: Tạo vài task ở các danh sách khác nhau, sửa một task, hoàn thành một task,
xoá một task, rồi tắt và mở lại ứng dụng để kiểm tra mọi thay đổi còn nguyên.

**Acceptance Scenarios**:

1. **Given** ứng dụng đang mở, **When** người dùng tạo task "Nộp bài tập Toán" với hạn chót
   10/11/2026 17:00, ưu tiên Cao, danh sách Học tập, **Then** task xuất hiện trong danh sách Học
   tập với đầy đủ thông tin đã nhập.
2. **Given** một task chưa hoàn thành, **When** người dùng đánh dấu hoàn thành, **Then** task hiển
   thị trạng thái đã hoàn thành và có thể bỏ đánh dấu để trở lại chưa hoàn thành.
3. **Given** một task đã tồn tại, **When** người dùng sửa tiêu đề, hạn chót, ưu tiên hoặc danh
   sách, **Then** thay đổi được lưu và hiển thị ngay.
4. **Given** một task đã tồn tại, **When** người dùng chọn xoá và xác nhận, **Then** task biến mất
   khỏi mọi nơi trong ứng dụng.
5. **Given** người dùng vừa tạo/sửa task, **When** tắt ứng dụng rồi mở lại, **Then** dữ liệu task
   giống hệt trước khi tắt.
6. **Given** người dùng để trống tiêu đề, **When** bấm lưu, **Then** ứng dụng không lưu và hiển thị
   thông báo lỗi tiếng Việt yêu cầu nhập tiêu đề.

---

### User Story 2 - Thêm lịch học lặp lại hàng tuần (Priority: P1)

Người dùng thêm môn học với tên môn, thứ trong tuần, giờ bắt đầu, giờ kết thúc, phòng học, ngày bắt
đầu và ngày kết thúc. Ứng dụng tự tạo các buổi học lặp lại mỗi tuần vào đúng thứ đó trong khoảng
thời gian đã chọn. Người dùng có thể nhập nhiều môn cùng lúc cho cả tháng hoặc cả học kỳ.

**Why this priority**: Lịch học là lý do chính của ứng dụng; nhập một lần cho cả học kỳ giúp người
dùng không phải tạo từng buổi.

**Independent Test**: Nhập 3 môn cho một học kỳ 15 tuần trong một lần, kiểm tra mỗi môn có đúng số
buổi, đúng thứ, đúng giờ trong khoảng ngày đã chọn.

**Acceptance Scenarios**:

1. **Given** chưa có môn học nào, **When** người dùng thêm môn "Giải tích" vào Thứ Hai, 07:30–09:30,
   phòng A101, từ 07/09/2026 đến 20/12/2026, **Then** ứng dụng tạo một buổi học vào mỗi Thứ Hai trong
   khoảng đó (buổi đầu tiên 07/09/2026, buổi cuối 14/12/2026).
2. **Given** màn hình nhập nhiều môn, **When** người dùng điền nhiều dòng môn học dùng chung một
   khoảng ngày (cả tháng hoặc cả học kỳ) và lưu một lần, **Then** tất cả các môn được tạo với buổi
   học lặp lại tương ứng.
3. **Given** một môn học cần học nhiều buổi trong tuần (ví dụ Thứ Hai và Thứ Năm), **When** người
   dùng chọn nhiều thứ cho môn đó, **Then** buổi học được tạo cho từng thứ đã chọn.
4. **Given** người dùng nhập giờ kết thúc sớm hơn hoặc bằng giờ bắt đầu, hoặc ngày kết thúc trước
   ngày bắt đầu, **When** bấm lưu, **Then** ứng dụng không lưu và chỉ rõ trường bị sai.
5. **Given** khi nhập nhiều môn có một dòng bị lỗi, **When** bấm lưu, **Then** ứng dụng chỉ rõ dòng
   lỗi và không làm mất dữ liệu đã nhập ở các dòng khác.

---

### User Story 3 - Trang "Hôm nay" (Priority: P1)

Khi mở ứng dụng, người dùng thấy trang "Hôm nay" liệt kê các buổi học trong ngày theo thứ tự thời
gian và các task có hạn chót hôm nay, kèm các task đã quá hạn chưa hoàn thành.

**Why this priority**: Đây là màn hình người dùng xem nhiều nhất mỗi ngày để biết hôm nay cần làm
gì và học gì.

**Independent Test**: Tạo buổi học và task cho hôm nay, ngày mai và hôm qua; kiểm tra trang Hôm nay
chỉ hiện đúng mục của hôm nay và nhóm "Quá hạn".

**Acceptance Scenarios**:

1. **Given** hôm nay có 2 buổi học và 3 task hạn hôm nay, **When** người dùng mở trang Hôm nay,
   **Then** thấy 2 buổi học xếp theo giờ bắt đầu (kèm giờ, phòng) và 3 task (kèm ưu tiên, danh sách).
2. **Given** có task chưa hoàn thành với hạn chót đã qua, **When** mở trang Hôm nay, **Then** task
   đó xuất hiện trong nhóm "Quá hạn" riêng.
3. **Given** một buổi học hôm nay đã bị huỷ, **When** mở trang Hôm nay, **Then** buổi đó hiển thị
   rõ là "Đã huỷ" hoặc không được tính là buổi cần đi học.
4. **Given** người dùng đánh dấu hoàn thành một task trên trang Hôm nay, **Then** trạng thái được
   cập nhật ngay ở mọi màn hình khác.
5. **Given** hôm nay không có buổi học hay task nào, **When** mở trang Hôm nay, **Then** hiển thị
   thông báo thân thiện rằng hôm nay trống lịch.

---

### User Story 4 - Sửa hoặc huỷ một buổi học riêng lẻ (Priority: P2)

Người dùng thay đổi một buổi học cụ thể (đổi giờ, đổi phòng) hoặc huỷ buổi đó (ví dụ nghỉ lễ) mà
các buổi khác của môn học không bị ảnh hưởng.

**Why this priority**: Lịch học thực tế thường có ngoại lệ; thiếu tính năng này lịch sẽ sai, nhưng
có thể dùng ứng dụng mà chưa cần nó.

**Independent Test**: Huỷ buổi Giải tích ngày 16/11/2026 và đổi phòng buổi 23/11/2026; kiểm tra hai
buổi đó thay đổi đúng còn các buổi khác giữ nguyên.

**Acceptance Scenarios**:

1. **Given** môn học có các buổi lặp lại, **When** người dùng huỷ buổi ngày 16/11/2026, **Then** chỉ
   buổi đó được đánh dấu "Đã huỷ", các buổi khác không đổi.
2. **Given** một buổi đã huỷ, **When** người dùng khôi phục buổi đó, **Then** buổi học trở lại bình
   thường.
3. **Given** một buổi học, **When** người dùng đổi giờ hoặc phòng riêng cho buổi đó, **Then** chỉ
   buổi đó hiển thị thông tin mới.
4. **Given** người dùng sửa thông tin chung của môn học (ví dụ phòng học), **When** lưu, **Then** các
   buổi chưa bị sửa riêng được cập nhật, còn các buổi đã sửa riêng hoặc đã huỷ giữ nguyên ngoại lệ.
5. **Given** người dùng xoá cả môn học, **When** xác nhận, **Then** toàn bộ buổi học của môn đó bị
   xoá.

---

### User Story 5 - Xem lịch theo ngày, tuần, tháng (Priority: P2)

Người dùng xem lịch ở chế độ ngày, tuần hoặc tháng; lịch hiển thị cả buổi học (theo giờ) và task
(theo hạn chót), với màu khác nhau theo môn học hoặc danh sách.

**Why this priority**: Giúp người dùng nhìn tổng quan và lên kế hoạch, nhưng trang Hôm nay và danh
sách task đã đáp ứng nhu cầu tối thiểu.

**Independent Test**: Với dữ liệu mẫu gồm 3 môn và 5 task, chuyển qua lại giữa ba chế độ xem, di
chuyển tới tuần/tháng sau và trước, kiểm tra mục hiện đúng ngày và đúng màu.

**Acceptance Scenarios**:

1. **Given** có buổi học và task trong tuần này, **When** người dùng chọn chế độ xem tuần, **Then**
   thấy 7 ngày (Thứ Hai đến Chủ Nhật) với buổi học đặt đúng khung giờ và task đặt ở ngày hạn chót.
2. **Given** chế độ xem tháng, **When** một ngày có nhiều mục hơn chỗ hiển thị, **Then** ngày đó
   hiện số mục còn lại (ví dụ "+3") và người dùng có thể mở xem chi tiết ngày đó.
3. **Given** bất kỳ chế độ xem nào, **When** người dùng bấm "Trước", "Sau" hoặc "Hôm nay", **Then**
   lịch chuyển sang khoảng thời gian tương ứng.
4. **Given** hai môn học khác nhau và hai danh sách khác nhau, **When** xem lịch, **Then** mỗi môn
   và mỗi danh sách có màu riêng, nhất quán ở mọi chế độ xem.
5. **Given** người dùng bấm vào một buổi học hoặc task trên lịch, **Then** thấy chi tiết và có thể
   mở để sửa.

---

### User Story 6 - Nhập lịch học từ ảnh (Priority: P2)

Người dùng kéo thả hoặc chọn ảnh chụp màn hình thời khoá biểu từ cổng thông tin sinh viên (thường
là ảnh chụp toàn màn hình, có cả thanh menu, trình duyệt và các phần thừa khác). Hệ thống nhận diện ngay trên máy các buổi học (tên môn, mã lớp, ngày, thứ, giờ bắt đầu/kết
thúc, phòng, giảng viên) và tự xác định tháng/năm từ các dấu hiệu trong ảnh như lịch tháng thu nhỏ,
tiêu đề tuần hoặc ngày giờ hệ thống trên thanh menu. Kết quả luôn hiện trong bảng xem trước để
người dùng kiểm tra, sửa, chọn lặp hàng tuần đến ngày nào hoặc chỉ một lần, rồi mới lưu.

**Why this priority**: Nhập tay cả học kỳ tốn thời gian và dễ sai; nhập từ ảnh giúp tiết kiệm phần
lớn công sức. Tuy vậy người dùng vẫn có thể nhập tay (User Story 2), nên đây không phải P1.

**Independent Test**: Dùng một ảnh chụp toàn màn hình thời khoá biểu tuần có 5 buổi học: kéo thả
vào ứng dụng, kiểm tra bảng xem trước có đủ 5 buổi với thông tin đúng, sửa một ô, đặt lặp hàng tuần
đến cuối học kỳ cho 4 buổi và chỉ một lần cho 1 buổi, lưu rồi kiểm tra lịch tuần. Nhập lại cùng ảnh
và kiểm tra không có buổi học nào bị tạo trùng.

**Acceptance Scenarios**:

1. **Given** người dùng mở chức năng nhập ảnh, **When** kéo thả hoặc chọn một ảnh, **Then** ứng
   dụng hiển thị ảnh và bắt đầu nhận diện ngay trên máy, có báo đang xử lý.
2. **Given** ảnh chụp toàn màn hình thời khoá biểu rõ nét, **When** nhận diện xong, **Then** bảng
   xem trước liệt kê mỗi buổi học một dòng với tên môn, mã lớp, ngày, thứ, giờ bắt đầu, giờ kết
   thúc, phòng và giảng viên.
3. **Given** ảnh chỉ ghi thứ (không ghi ngày) nhưng có lịch tháng thu nhỏ hoặc ngày giờ hệ thống,
   **When** nhận diện, **Then** ứng dụng suy ra ngày cụ thể của từng buổi và cho biết đã dựa vào
   dấu hiệu nào để xác định tháng/năm.
4. **Given** ảnh bị mờ, bị cắt hoặc thiếu thông tin (ví dụ không xác định được tháng/năm, không đọc
   rõ phòng), **When** nhận diện, **Then** các ô chưa chắc chắn được đánh dấu nổi bật kèm lý do, và
   người dùng phải xác nhận hoặc sửa các ô bắt buộc còn chưa chắc chắn trước khi lưu.
5. **Given** bảng xem trước, **When** người dùng sửa ô bất kỳ, bỏ chọn một dòng, hoặc chọn cho từng
   dòng "chỉ một lần" hay "lặp hàng tuần đến ngày ...", **Then** chỉ các dòng được chọn được lưu,
   đúng theo lựa chọn lặp của từng dòng.
6. **Given** một buổi học trong ảnh đã có sẵn trong lịch (cùng môn, cùng ngày, cùng giờ bắt đầu),
   **When** hiện bảng xem trước, **Then** dòng đó được đánh dấu "Đã có trong lịch" và mặc định không
   được chọn; khi lưu, ứng dụng không tạo buổi học trùng.
7. **Given** ảnh không chứa thời khoá biểu, **When** nhận diện, **Then** ứng dụng báo không tìm thấy
   buổi học nào và không lưu gì.

---

### User Story 7 - Thông báo nhắc (Priority: P3)

Ứng dụng nhắc trước khi buổi học bắt đầu và trước hạn chót của task, trên cả Mac và iPhone. Người
dùng không luôn mang theo Mac, nên khi bật "Đồng bộ với Lịch và Lời nhắc", ứng dụng ghi buổi học và
task (kể cả task deadline tự tạo) kèm giờ báo trước vào ứng dụng Lịch và Lời nhắc của Apple; iCloud
tự đồng bộ sang iPhone, nên iPhone vẫn nhắc đúng giờ khi Mac đang gập hoặc tắt. Mọi thay đổi trong
ứng dụng được cập nhật sang Lịch/Lời nhắc. Khi chưa bật đồng bộ, ứng dụng nhắc bằng thông báo của
trình duyệt trong lúc tab ứng dụng đang mở. Người dùng chỉnh được thời gian nhắc mặc định và chỉnh
riêng cho từng môn học hoặc từng task, hoặc tắt nhắc.

Mỗi sáng (mặc định 05:00) người dùng nhận một **thông báo tổng hợp** tóm tắt ngày hôm đó: buổi thi
(nếu có, đứng đầu), các buổi học (ca, tên môn, phòng), rồi tối đa 3 task (đến hạn hôm nay trước,
rồi quá hạn) kèm "+N việc khác" nếu còn.
Bản tóm tắt được tạo sẵn cho nhiều ngày tới trong Lịch của Apple và tự cập nhật khi dữ liệu đổi, nên
iPhone vẫn nhận đúng giờ khi Mac đang gập. Người dùng đánh dấu **"Quan trọng"** cho task, buổi học
hoặc buổi thi: mục quan trọng được nhắc nhiều mốc và hiển thị nổi bật; buổi thi mặc định là quan
trọng và có thêm mốc nhắc trước 7 ngày.

**Why this priority**: Hữu ích nhưng người dùng vẫn dùng được ứng dụng bằng cách tự xem trang Hôm
nay.

**Independent Test**: Bật đồng bộ, đặt nhắc 5 phút trước một buổi học và 10 phút trước hạn chót một
task trong tương lai gần, đóng tab ứng dụng và gập Mac; kiểm tra iPhone hiện thông báo đúng thời
điểm với nội dung tiếng Việt. Sau đó huỷ buổi học trong ứng dụng và kiểm tra lời nhắc biến mất khỏi
Lịch trên cả Mac và iPhone. Đặt giờ tổng hợp sau vài phút, gập Mac và kiểm tra iPhone nhận bản tóm
tắt; đánh dấu một task là Quan trọng và kiểm tra lời nhắc của nó có đủ các mốc.

**Acceptance Scenarios**:

1. **Given** nhắc mặc định cho buổi học là 15 phút, **When** còn 15 phút tới giờ học, **Then** hiện
   thông báo gồm tên môn, giờ bắt đầu và phòng học.
2. **Given** task có hạn chót và thời gian nhắc, **When** tới thời điểm nhắc, **Then** hiện thông báo
   gồm tiêu đề task và hạn chót.
3. **Given** người dùng đổi thời gian nhắc của một task hoặc môn học, **Then** thông báo hiện theo
   thời gian mới thay vì mặc định.
4. **Given** buổi học đã bị huỷ hoặc task đã hoàn thành/đã xoá, **When** tới thời điểm nhắc, **Then**
   không có thông báo nào.
5. **Given** người dùng tắt nhắc cho một mục, **Then** mục đó không gửi thông báo.
6. **Given** đồng bộ đã bật và iCloud đã đồng bộ xong, **When** Mac đang gập hoặc tắt và tới thời
   điểm nhắc, **Then** iPhone hiện thông báo gồm tên môn, giờ bắt đầu, phòng (buổi học) hoặc tiêu đề,
   hạn chót (task).
7. **Given** đồng bộ đã bật, **When** người dùng thêm, sửa giờ, huỷ, khôi phục buổi học, hoặc thêm,
   sửa, hoàn thành, xoá task (kể cả task deadline tự tạo), **Then** bản trong Lịch/Lời nhắc được
   thêm, cập nhật hoặc xoá tương ứng.
8. **Given** đồng bộ đã bật, **When** tab ứng dụng đã đóng nhưng Mac đang mở, **Then** Mac vẫn hiện
   thông báo qua Lịch/Lời nhắc, và mỗi lời nhắc chỉ hiện một lần trên mỗi thiết bị.
9. **Given** người dùng tắt đồng bộ, **Then** ứng dụng xoá lịch và danh sách lời nhắc nó đã tạo, và
   chuyển sang nhắc bằng thông báo của trình duyệt.
10. **Given** chưa bật đồng bộ và tab ứng dụng đang mở, **When** tới thời điểm nhắc, **Then** trình
    duyệt hiện thông báo (sau khi người dùng cho phép); khi tab đã đóng thì không nhắc, và các nhắc
    đã lỡ không hiện dồn khi mở lại.
11. **Given** thông báo tổng hợp đang bật lúc 05:00 và ngày mai có 1 buổi thi, 2 buổi học, 2 task đến
    hạn và 3 task quá hạn, **When** tới 05:00 ngày mai, **Then** có một thông báo liệt kê buổi thi
    trước (giờ, phòng), rồi từng buổi học (ca, tên môn, phòng), rồi tiêu đề 2 task đến hạn và 1 task
    quá hạn (quá hạn lâu nhất), rồi "+2 việc khác".
12. **Given** một ngày không có buổi thi, buổi học, task đến hạn hay task quá hạn, **When** tới giờ
    tổng hợp, **Then** không có thông báo nào.
13. **Given** đồng bộ đang bật và bản tóm tắt của 3 ngày tới đã có trên iPhone, **When** người dùng
    huỷ một buổi học của ngày kia, **Then** bản tóm tắt của ngày đó được cập nhật (bỏ buổi đã huỷ)
    trên Mac và iPhone; Mac gập suốt 3 ngày thì iPhone vẫn nhận đủ 3 bản tóm tắt đúng giờ.
14. **Given** người dùng tắt thông báo tổng hợp hoặc đổi giờ sang 06:30, **Then** các bản tóm tắt đã
    tạo bị xoá hoặc chuyển sang 06:30.
15. **Given** một task có giờ hạn chót được bật "Quan trọng" với cài đặt mặc định, **Then** task được
    nhắc 1 ngày, 3 giờ, 1 giờ và 15 phút trước hạn; tắt "Quan trọng" thì quay về 1 mốc như cũ.
16. **Given** một buổi thi mới, **Then** buổi thi mặc định là Quan trọng và được nhắc trước 7 ngày,
    1 ngày, 3 giờ, 1 giờ và 15 phút.
17. **Given** một mục quan trọng, **When** xem lịch hoặc trang Hôm nay, **Then** mục đó hiện nổi
    bật (dấu ★ và viền đậm) so với mục thường.
18. **Given** một ngày chỉ có task quá hạn (không có buổi thi, buổi học hay task đến hạn), **When** tới
    giờ tổng hợp, **Then** có bản tóm tắt nếu tuỳ chọn "Gửi tóm tắt khi chỉ có việc quá hạn" đang
    bật (mặc định), và không có nếu đã tắt.

---

### User Story 8 - Ca học cố định (Priority: P2)

Trường học xếp lịch theo ca cố định. Ứng dụng có bảng cấu hình ca học, mặc định Ca 1 06:45–09:25,
Ca 2 09:35–12:10, Ca 3 13:00–15:40, Ca 4 15:45–18:25; người dùng chỉnh được giờ. Khi thêm môn học
hoặc nhập từ ảnh, người dùng chọn ca thay vì gõ giờ; giờ đọc được từ ảnh được đối chiếu với ca
tương ứng.

**Why this priority**: Giúp nhập lịch nhanh và giờ học luôn chính xác, nhưng vẫn có thể nhập giờ
thủ công nếu chưa có tính năng này.

**Independent Test**: Thêm một môn chọn "Ca 2" và kiểm tra giờ là 09:35–12:10; đổi giờ Ca 2 trong
cài đặt và kiểm tra môn đó cập nhật theo; nhập một ảnh có giờ 13:00–15:40 và kiểm tra bảng xem
trước hiện "Ca 3".

**Acceptance Scenarios**:

1. **Given** lần đầu mở ứng dụng, **When** người dùng mở bảng ca học, **Then** thấy 4 ca mặc định
   với đúng giờ như trên.
2. **Given** màn hình thêm môn học (một môn hoặc nhiều môn), **When** người dùng chọn "Ca 1", **Then**
   giờ bắt đầu/kết thúc được điền 06:45–09:25; người dùng vẫn chọn được "Giờ tuỳ chỉnh" để gõ tay.
3. **Given** một môn học kéo dài hai ca liền nhau, **When** người dùng chọn "Ca 1–2", **Then** giờ là
   06:45–12:10.
4. **Given** có môn học đang dùng Ca 2, **When** người dùng đổi giờ Ca 2 và xác nhận, **Then** các buổi
   học của môn đó cập nhật giờ mới, trừ các buổi đã sửa giờ riêng.
5. **Given** ảnh thời khoá biểu ghi giờ 09:35–12:10 hoặc ghi "Ca 2", **When** nhận diện, **Then** bảng
   xem trước gán "Ca 2" cho dòng đó với giờ theo bảng ca.
6. **Given** giờ trong ảnh không khớp ca nào, **When** nhận diện, **Then** dòng đó giữ giờ đọc được,
   ghi "Giờ tuỳ chỉnh" và có ghi chú "không khớp ca nào" để người dùng kiểm tra.

---

### User Story 9 - Nhãn có màu (Priority: P2)

Người dùng tạo nhãn riêng với tên và màu (ví dụ "Họp" màu đỏ, "Gấp" màu đỏ) và gắn nhiều nhãn cho
task và buổi học. Trên lịch, mục có nhãn hiển thị theo màu nhãn. Người dùng lọc lịch và danh sách
theo nhãn.

**Why this priority**: Giúp phân loại và tìm nhanh những việc quan trọng xuyên suốt các danh sách và
môn học, nhưng không bắt buộc cho luồng cơ bản.

**Independent Test**: Tạo nhãn "Gấp" màu đỏ, gắn cho 2 task và 1 buổi học, kiểm tra 3 mục hiện màu
đỏ trên lịch tuần; lọc theo "Gấp" và kiểm tra chỉ 3 mục đó còn hiện.

**Acceptance Scenarios**:

1. **Given** màn hình quản lý nhãn, **When** người dùng tạo nhãn "Họp" chọn màu đỏ, **Then** nhãn được
   lưu và dùng được ngay khi sửa task hoặc buổi học.
2. **Given** một task, **When** người dùng gắn nhãn "Họp" và "Gấp", **Then** task hiển thị cả hai nhãn
   trong danh sách và trên lịch.
3. **Given** một môn học, **When** người dùng gắn nhãn cho môn, **Then** mọi buổi học của môn có nhãn
   đó; người dùng cũng gắn thêm được nhãn riêng cho một buổi học mà không ảnh hưởng buổi khác.
4. **Given** một mục có nhãn, **When** xem lịch ở chế độ ngày, tuần hoặc tháng, **Then** mục hiển thị
   theo màu nhãn thay cho màu môn học hoặc danh sách.
5. **Given** lịch hoặc danh sách task, **When** người dùng chọn lọc theo một hoặc nhiều nhãn, **Then**
   chỉ hiện các mục có ít nhất một nhãn đã chọn; bỏ lọc thì hiện lại tất cả.
6. **Given** một nhãn đang được dùng, **When** người dùng xoá nhãn và xác nhận, **Then** nhãn bị gỡ
   khỏi mọi mục, các mục trở về màu môn học hoặc danh sách.

---

### User Story 10 - Tự tạo deadline cho môn đặc biệt (Priority: P3)

Với môn học có nhãn "E-Learning" hoặc buổi học bắt đầu từ 20:00 trở đi, mỗi buổi học tự sinh một
task deadline vào 08:00 sáng Chủ Nhật gần nhất sau buổi học đó, trừ các môn Giáo dục thể chất. Mốc
giờ 20:00, giờ deadline 08:00 và danh sách môn ngoại lệ chỉnh được trong cài đặt.

**Why this priority**: Tiết kiệm công tạo task lặp lại cho các môn học trực tuyến có bài nộp hằng
tuần, nhưng người dùng vẫn có thể tạo task bằng tay.

**Independent Test**: Thêm môn "Triết học" gắn nhãn E-Learning học Thứ Ba hằng tuần trong 4 tuần và
môn "Giáo dục thể chất 2" học Thứ Tư 20:30; kiểm tra có đúng 4 task deadline 08:00 các Chủ Nhật
tương ứng cho Triết học và không có task nào cho Giáo dục thể chất.

**Acceptance Scenarios**:

1. **Given** môn "Triết học" có nhãn E-Learning, học Thứ Ba 10/11/2026, **When** lưu môn học, **Then**
   ứng dụng tạo task "Bài tập Triết học – buổi 10/11" hạn 08:00 Chủ Nhật 15/11/2026 trong danh sách
   Học tập.
2. **Given** môn không có nhãn E-Learning nhưng buổi học bắt đầu lúc 20:30, **When** lưu, **Then** buổi
   đó cũng có task deadline tự tạo.
3. **Given** môn "Giáo dục thể chất 2" học lúc 20:30, **When** lưu, **Then** không có task tự tạo nào.
4. **Given** người dùng đổi mốc giờ thành 19:00 hoặc giờ deadline thành 22:00 Chủ Nhật trong cài
   đặt, **When** lưu cài đặt, **Then** task tự tạo của các buổi có deadline trong tương lai được tạo
   lại hoặc cập nhật theo quy tắc mới.
5. **Given** buổi học có task tự tạo, **When** người dùng huỷ buổi đó, **Then** task tự tạo bị xoá nếu
   chưa hoàn thành và chưa bị người dùng sửa; khôi phục buổi học thì task được tạo lại.
6. **Given** task tự tạo, **When** xem task, **Then** thấy rõ đây là task tự tạo và liên kết tới buổi
   học sinh ra nó.

---

### User Story 11 - Lịch thi (Priority: P2)

Người dùng quản lý lịch thi: mỗi buổi thi có mã học phần, tên học phần, lần thi, ngày thi, giờ bắt
đầu và kết thúc, hình thức thi (ví dụ "Trắc nghiệm trên máy 60p", "Bài tập lớn"), phòng thi (có thể
trống) và số báo danh. Buổi thi là sự kiện một lần, không lặp. Người dùng nhập tay hoặc đưa ảnh chụp
bảng "Lịch thi cá nhân" trên cổng sinh viên; hệ thống tự nhận biết ảnh là lịch học dạng tuần hay lịch
thi dạng bảng. Buổi thi hiện trên lịch và trang Hôm nay với nhãn "Thi" màu nổi bật, được cảnh báo khi
trùng giờ với buổi học, mặc định là mục Quan trọng nên được nhắc trước 7 ngày, 1 ngày, 3 giờ, 1 giờ
và 15 phút (FR-069), và đồng bộ sang Lịch/Lời nhắc của Apple như buổi học.

**Why this priority**: Lịch thi là mốc quan trọng nhất của học kỳ; quên giờ hoặc phòng thi gây hậu
quả lớn. Tính năng dựa trên phần nhập ảnh (US6) và lịch (US5) nên xếp cùng nhóm P2.

**Independent Test**: Thêm tay một buổi thi; nhập một ảnh bảng lịch thi có 6 môn (2 môn đã qua);
kiểm tra bảng xem trước đánh dấu 2 môn "Đã qua" và bỏ chọn, không có họ tên hay mã số sinh viên;
lưu, rồi xem buổi thi trên trang Hôm nay và lịch tuần với nhãn "Thi"; nhập lại cùng ảnh thì không
tạo trùng.

**Acceptance Scenarios**:

1. **Given** trang Lịch thi, **When** người dùng thêm buổi thi "Cơ sở dữ liệu", mã CSE2301, lần 1,
   ngày 05/01/2027, 07:30–08:30, "Trắc nghiệm trên máy 60p", phòng A5-310, SBD 125, **Then** buổi
   thi được lưu và hiện trên lịch ngày 05/01/2027 với nhãn "Thi".
2. **Given** buổi thi không có phòng, **When** lưu, **Then** được chấp nhận và hiển thị "Chưa có
   phòng".
3. **Given** buổi thi trùng giờ với một buổi học (chưa huỷ) hoặc một buổi thi khác, **When** lưu,
   **Then** vẫn lưu được nhưng hiện cảnh báo nêu rõ buổi bị trùng; trên lịch và trang Hôm nay buổi
   thi có dấu "Trùng giờ".
4. **Given** ảnh chụp bảng "Lịch thi cá nhân", **When** người dùng nhập ảnh, **Then** hệ thống nhận
   ra đây là lịch thi (không phải lịch học dạng tuần) và hiện bảng xem trước theo các cột của buổi
   thi; cột họ tên, mã số sinh viên bị bỏ qua và không xuất hiện ở bất kỳ đâu.
5. **Given** bảng lịch thi có môn đã thi xong, **When** hiện bảng xem trước, **Then** các dòng đó
   có nhãn "Đã qua" và mặc định không được chọn.
6. **Given** một buổi thi trong ảnh đã có trong ứng dụng (cùng mã học phần hoặc tên học phần, cùng
   ngày và giờ bắt đầu), **When** hiện bảng xem trước, **Then** dòng đó có nhãn "Đã có trong lịch",
   mặc định bỏ chọn và không bị tạo trùng khi lưu.
7. **Given** buổi thi sắp tới với nhắc mặc định, **When** tới từng mốc 7 ngày, 1 ngày, 3 giờ, 1 giờ
   và 15 phút trước giờ thi, **Then** có thông báo gồm tên học phần, giờ và phòng thi; khi đồng bộ
   đang bật, buổi thi có trong lịch "Lịch Học Cá Nhân" kèm đủ các lời báo trước đó.
8. **Given** trang Hôm nay vào ngày có thi, **When** mở trang, **Then** buổi thi hiện ở khối "Buổi
   thi" phía trên buổi học, gồm giờ, phòng, hình thức thi, số báo danh.

---

### Edge Cases

- Ngày bắt đầu học kỳ không rơi vào thứ của môn học: buổi đầu tiên là ngày đúng thứ đó gần nhất sau
  ngày bắt đầu.
- Khoảng ngày không chứa thứ nào đã chọn (ví dụ chỉ 3 ngày): ứng dụng cảnh báo rằng không có buổi
  học nào được tạo.
- Hai buổi học trùng giờ: ứng dụng vẫn cho lưu nhưng hiển thị cảnh báo trùng lịch.
- Task không có hạn chót: không xuất hiện trên lịch và trang Hôm nay, chỉ trong danh sách của nó.
- Task có hạn chót nhưng không có giờ: coi như hạn vào cuối ngày (23:59) khi xét quá hạn, nhưng lời
  nhắc hiện lúc 08:00 sáng ngày hạn chót (FR-022).
- Xoá một danh sách đang có task: ứng dụng hỏi chuyển task sang danh sách khác hoặc xoá luôn các
  task đó.
- Mac gập hoặc tắt vào thời điểm cần nhắc: iPhone vẫn nhắc nếu đã bật đồng bộ; Mac không hiện các
  nhắc đã lỡ dồn lại khi mở; task quá hạn vẫn hiện ở nhóm "Quá hạn".
- Chưa bật đồng bộ và tab ứng dụng đóng vào thời điểm cần nhắc: không có thông báo nào.
- Người dùng chặn quyền thông báo của trình duyệt (khi chưa bật đồng bộ): ứng dụng hiện một dòng
  cảnh báo trên trang Hôm nay kèm hướng dẫn bằng tiếng Việt; các chức năng khác vẫn hoạt động.
- Người dùng từ chối quyền truy cập Lịch/Lời nhắc khi bật đồng bộ: công tắc trở về tắt, ứng dụng
  giải thích bằng tiếng Việt cách cấp quyền; nhắc bằng trình duyệt vẫn hoạt động.
- Người dùng tự xoá hoặc sửa lịch "Lịch Học Cá Nhân" trong ứng dụng Lịch: ở lần cập nhật sau, ứng
  dụng tạo lại và ghi đè theo dữ liệu gốc.
- Số lượng lời nhắc lớn (cả học kỳ khoảng 6 môn × 15 tuần): toàn bộ buổi học còn lại của học kỳ
  được ghi sẵn, để iPhone vẫn nhắc đủ dù Mac gập hoặc tắt nhiều ngày.
- Sửa giờ một ca thành giờ kết thúc không sau giờ bắt đầu: ứng dụng từ chối lưu.
- Xoá một ca đang được môn học dùng: sau khi xác nhận, các môn đó giữ nguyên giờ hiện tại và chuyển
  thành "Giờ tuỳ chỉnh".
- Buổi học vào tối Chủ Nhật thuộc diện tự tạo deadline: deadline là 08:00 Chủ Nhật tuần sau.
- Người dùng tự xoá một task tự tạo: ứng dụng không tạo lại task đó cho buổi học ấy.
- Người dùng sửa một task tự tạo (tiêu đề, hạn chót...): task không còn bị cập nhật hay xoá tự động.
- Nhập môn học giữa học kỳ: chỉ tạo task tự động cho các buổi có deadline chưa qua.
- Tạo nhãn trùng tên với nhãn đã có (không phân biệt hoa thường): ứng dụng từ chối và báo lỗi.
- Mục có nhiều nhãn: trên lịch dùng màu của nhãn gắn đầu tiên, các nhãn còn lại hiện dưới dạng chấm
  màu hoặc tên nhãn.
- Ứng dụng bị tắt đột ngột giữa lúc lưu: dữ liệu trước đó vẫn còn nguyên, không bị hỏng.
- Ảnh có nhiều tuần hoặc cả lịch tháng: mỗi buổi học nhận diện được là một dòng trong bảng xem
  trước; các buổi cùng môn, cùng thứ, cùng giờ được gợi ý gộp thành một môn lặp hàng tuần.
- Các dấu hiệu tháng/năm trong ảnh mâu thuẫn nhau (ví dụ ngày giờ hệ thống khác tháng của lịch
  thu nhỏ): ưu tiên thông tin nằm trong chính thời khoá biểu, đánh dấu chưa chắc chắn và cho người
  dùng chọn.
- Ngày nhận diện được không khớp với thứ (ví dụ ghi "Thứ Hai" nhưng ngày đó là Thứ Ba): đánh dấu
  chưa chắc chắn, không tự sửa.
- Môn học trong ảnh trùng tên với môn đã có nhưng khác giờ hoặc khác phòng: không coi là trùng, tạo
  buổi học mới và hiển thị cảnh báo trùng giờ nếu có (FR-015).
- Người dùng đóng bảng xem trước mà không lưu: không có dữ liệu nào được tạo.
- Ảnh quá lớn hoặc không phải định dạng ảnh được hỗ trợ: báo lỗi trước khi nhận diện.
- Chưa có học kỳ nào khi thêm môn học: ứng dụng yêu cầu tạo học kỳ ngay trong màn hình thêm môn.
- Sửa ngày học kỳ làm một số môn nằm ngoài khoảng mới: ứng dụng cảnh báo, liệt kê các môn bị ảnh
  hưởng và cho chọn thu hẹp ngày của các môn đó theo học kỳ hoặc huỷ thao tác.
- Tạo học kỳ có ngày chồng lấn với học kỳ đã có: ứng dụng từ chối và chỉ rõ học kỳ bị chồng lấn.
- Tiêu đề, ghi chú, tên môn và phòng học có dấu tiếng Việt và ký tự đặc biệt được lưu và hiển thị
  đúng.
- Bảng lịch thi chỉ ghi giờ bắt đầu (không có giờ kết thúc): giờ kết thúc được tính từ thời lượng
  trong hình thức thi (ví dụ "60p", "90 phút"); không suy ra được thì ô giờ kết thúc bị đánh dấu chưa
  chắc chắn.
- Ảnh không xác định được là lịch học hay lịch thi: bảng xem trước hỏi người dùng chọn loại trước khi
  hiện kết quả.
- Buổi thi trùng giờ với buổi học đã huỷ: không cảnh báo.
- Sửa hoặc xoá buổi thi khi đồng bộ đang bật: bản trong Lịch được cập nhật hoặc xoá như buổi học.
- Lần thi lại (lần 2) của cùng học phần: là buổi thi riêng, không bị coi là trùng với lần 1.
- Giờ tổng hợp của hôm nay đã qua lúc bản tóm tắt được tạo hoặc sửa: không gửi bù cho hôm nay.
- Buổi học hoặc buổi thi bắt đầu trước giờ tổng hợp (ví dụ thi 05:00 mà tổng hợp lúc 05:00): vẫn có
  trong bản tóm tắt; nhắc riêng của mục đó vẫn hoạt động như thường.
- Mac gập lâu hơn số ngày được tạo sẵn (14 ngày): các ngày sau đó không có bản tóm tắt trên iPhone
  cho tới khi Mac mở lại; nhắc buổi học và task vẫn hoạt động vì đã được ghi sẵn.
- Số task quá hạn trong bản tóm tắt của ngày tương lai được tính theo dữ liệu hiện tại (task chưa
  xong có hạn trước ngày đó); hoàn thành task thì các bản tóm tắt được cập nhật.
- Mốc nhắc của mục quan trọng đã qua (ví dụ đánh dấu Quan trọng 2 giờ trước giờ học): chỉ còn các mốc
  chưa tới; không gửi bù mốc đã qua.
- Task chỉ có ngày hạn chót được đánh dấu Quan trọng: nhắc vào giờ nhắc task chỉ có ngày (mặc định
  08:00) của ngày hạn và của 1 ngày trước; các mốc dưới 1 ngày không áp dụng.
- Mục quan trọng đã tắt nhắc riêng ("Không nhắc"): vẫn hiển thị nổi bật nhưng không có nhắc nào.
- Mục quan trọng có mốc nhắc riêng (ví dụ 30 phút): được nhắc theo các mốc quan trọng cộng thêm mốc
  riêng đó; hai mốc trùng nhau chỉ nhắc một lần.

## Requirements *(mandatory)*

### Functional Requirements

**Công việc (task) và danh sách**

- **FR-001**: Người dùng PHẢI tạo được task với tiêu đề (bắt buộc), ghi chú (tuỳ chọn), hạn chót
  gồm ngày và giờ (tuỳ chọn), mức ưu tiên Cao / Trung bình / Thấp (mặc định Trung bình) và một danh
  sách (bắt buộc).
- **FR-002**: Người dùng PHẢI sửa được mọi thuộc tính của task và xoá task sau khi xác nhận.
- **FR-003**: Người dùng PHẢI đánh dấu được task là hoàn thành và bỏ đánh dấu.
- **FR-004**: Ứng dụng PHẢI có sẵn ba danh sách "Học tập", "Cá nhân", "Công việc"; người dùng PHẢI
  tạo, đổi tên, đổi màu và xoá được danh sách.
- **FR-005**: Người dùng PHẢI xem được task theo từng danh sách, sắp xếp theo hạn chót (task không
  có hạn chót ở cuối), rồi theo mức ưu tiên.
- **FR-006**: Task đã hoàn thành PHẢI được phân biệt rõ với task chưa hoàn thành (ví dụ gạch ngang,
  làm mờ) và người dùng PHẢI ẩn/hiện được task đã hoàn thành.

**Lịch học**

- **FR-036**: Người dùng PHẢI tạo, sửa và xoá được học kỳ với tên (ví dụ "HK1 2026–2027"), ngày bắt
  đầu và ngày kết thúc. Các học kỳ KHÔNG ĐƯỢC chồng lấn ngày nhau. Học kỳ hiện tại là học kỳ chứa
  ngày hôm nay; nếu không có thì là học kỳ sắp tới gần nhất.
- **FR-037**: Xoá học kỳ PHẢI xoá kèm mọi môn học và buổi học thuộc học kỳ đó, sau khi xác nhận và
  cho biết số môn học sẽ bị xoá.
- **FR-007**: Người dùng PHẢI thêm được môn học với tên môn (bắt buộc), học kỳ (bắt buộc, mặc định
  là học kỳ hiện tại), mã lớp (tuỳ chọn), giảng viên (tuỳ chọn), nhãn (tuỳ chọn), một hoặc nhiều
  thứ trong tuần, ca học hoặc giờ bắt đầu/kết thúc tuỳ chỉnh (FR-039), phòng học (tuỳ chọn), ngày
  bắt đầu và ngày kết thúc. Ngày bắt đầu/kết thúc
  mặc định bằng ngày của học kỳ, người dùng sửa được nhưng PHẢI nằm trong khoảng ngày của học kỳ.
  Môn học chỉ học một lần có ngày bắt đầu trùng ngày kết thúc.
- **FR-008**: Ứng dụng PHẢI tự sinh buổi học vào mỗi thứ đã chọn, lặp hàng tuần, trong khoảng ngày
  bắt đầu đến ngày kết thúc (tính cả hai đầu).
- **FR-009**: Người dùng PHẢI nhập được nhiều môn học trong một lần thao tác, thuộc cùng một học
  kỳ và dùng chung một khoảng ngày (mặc định cả học kỳ, có thể thu hẹp, ví dụ một tháng), với khả
  năng thêm/bớt dòng trước khi lưu.
- **FR-010**: Ứng dụng PHẢI từ chối lưu khi giờ kết thúc không sau giờ bắt đầu, ngày kết thúc trước
  ngày bắt đầu, hoặc thiếu trường bắt buộc, và chỉ rõ trường/dòng bị lỗi.
- **FR-011**: Người dùng PHẢI huỷ và khôi phục được một buổi học riêng lẻ mà không ảnh hưởng buổi
  khác.
- **FR-012**: Người dùng PHẢI sửa được giờ và phòng của một buổi học riêng lẻ mà không ảnh hưởng buổi
  khác.
- **FR-013**: Khi sửa thông tin chung của môn học, ứng dụng PHẢI giữ nguyên các buổi đã sửa riêng
  hoặc đã huỷ.
- **FR-014**: Người dùng PHẢI xoá được cả môn học (kèm mọi buổi học) sau khi xác nhận.
- **FR-015**: Ứng dụng PHẢI cảnh báo (không chặn) khi buổi học mới trùng giờ với buổi học đã có.

**Xem lịch và trang Hôm nay**

- **FR-016**: Ứng dụng PHẢI có chế độ xem ngày, tuần (Thứ Hai đến Chủ Nhật) và tháng, với nút chuyển
  trước/sau và về hôm nay.
- **FR-017**: Lịch PHẢI hiển thị buổi học theo khung giờ và task tại ngày hạn chót; buổi đã huỷ
  hiển thị khác biệt rõ ràng.
- **FR-018**: Mỗi môn học và mỗi danh sách PHẢI có màu riêng; màu được gán tự động khi tạo và người
  dùng đổi được. Mục có nhãn hiển thị theo màu nhãn (FR-044).
- **FR-019**: Ứng dụng PHẢI có trang "Hôm nay" hiển thị buổi học hôm nay theo thứ tự giờ, task có
  hạn chót hôm nay, và nhóm "Quá hạn" cho task chưa hoàn thành đã qua hạn.
- **FR-020**: Trang "Hôm nay" PHẢI là màn hình mặc định khi mở ứng dụng.

**Nhập lịch học từ ảnh**

- **FR-028**: Người dùng PHẢI nhập được ảnh thời khoá biểu bằng cách kéo thả vào ứng dụng hoặc chọn
  file ảnh (PNG, JPEG, HEIC; tối đa 20 MB).
- **FR-029**: Việc nhận diện ảnh PHẢI chạy hoàn toàn trên máy; ảnh KHÔNG ĐƯỢC rời khỏi máy
  (theo constitution, Nguyên tắc IV).
- **FR-030**: Ứng dụng PHẢI nhận diện từ ảnh các buổi học gồm: tên môn, mã lớp, ngày, thứ, giờ bắt
  đầu, giờ kết thúc, phòng và giảng viên; bỏ qua các phần không liên quan trong ảnh chụp toàn màn
  hình. Giờ nhận diện được đối chiếu với bảng ca học (FR-041).
- **FR-031**: Ứng dụng PHẢI xác định tháng/năm từ dấu hiệu trong ảnh (lịch tháng thu nhỏ, tiêu đề
  tuần, ngày giờ hệ thống) và cho người dùng biết dấu hiệu đã dùng.
- **FR-032**: Ô nào không đọc được hoặc không chắc chắn PHẢI được đánh dấu nổi bật kèm lý do; ứng
  dụng KHÔNG ĐƯỢC lưu dòng có ô bắt buộc (tên môn, ngày, giờ bắt đầu, giờ kết thúc) còn chưa chắc
  chắn cho tới khi người dùng xác nhận hoặc sửa.
- **FR-033**: Trước khi lưu, ứng dụng PHẢI luôn hiển thị bảng xem trước cho phép sửa mọi ô, chọn/bỏ
  chọn từng dòng, và chọn cho từng dòng "chỉ một lần" hoặc "lặp hàng tuần đến ngày ...". Các buổi
  học được gán vào học kỳ chứa ngày của buổi đó; mặc định là "lặp hàng tuần đến ngày kết thúc học
  kỳ đó". Nếu ngày của buổi học không thuộc học kỳ nào, bảng xem trước PHẢI đánh dấu dòng đó và cho
  người dùng chọn học kỳ có sẵn hoặc tạo học kỳ mới ngay tại đó trước khi lưu.
- **FR-034**: Ứng dụng KHÔNG ĐƯỢC tạo buổi học trùng: buổi học có cùng tên môn (hoặc cùng mã lớp),
  cùng ngày và cùng giờ bắt đầu với buổi đã có được đánh dấu "Đã có trong lịch", mặc định bỏ chọn
  và bị bỏ qua khi lưu. Quy tắc này cũng áp dụng giữa các dòng trong cùng một lần nhập.
- **FR-035**: Ảnh và kết quả nhận diện chưa lưu KHÔNG ĐƯỢC lưu lại sau khi người dùng đóng bảng xem
  trước; chỉ các buổi học người dùng đã xác nhận mới được lưu cục bộ.

**Thông báo nhắc**

- **FR-051**: Người dùng PHẢI bật/tắt được "Đồng bộ với Lịch và Lời nhắc" trong cài đặt; khi mở ứng
  dụng lần đầu, ứng dụng đề nghị bật. Khi bật, ứng dụng PHẢI xin quyền truy cập Lịch và Lời nhắc,
  rồi ghi mỗi buổi học (không bị huỷ) kèm giờ báo trước vào một lịch riêng tên "Lịch Học Cá Nhân",
  và mỗi task có hạn chót (kể cả task deadline tự tạo) kèm giờ báo trước vào một danh sách lời nhắc
  riêng cùng tên, để iCloud của người dùng đồng bộ sang iPhone.
- **FR-052**: Bản sao chỉ chứa tên môn hoặc tiêu đề task, thời gian, phòng học, giờ báo trước, mức
  "Quan trọng" và bản tóm tắt hằng ngày (FR-065, chỉ gồm ca, tên môn, tên học phần, giờ, phòng,
  tối đa 3 tiêu đề task và số việc còn lại); KHÔNG chứa ghi chú, ảnh hay dữ liệu khác. Ứng dụng KHÔNG ĐƯỢC đọc, sửa hay xoá mục nào ngoài lịch
  và danh sách lời nhắc do nó tạo.
- **FR-053**: Mọi thay đổi trong ứng dụng (thêm, sửa, huỷ, khôi phục, xoá buổi học hoặc môn học; thêm,
  sửa, hoàn thành, xoá task; đổi giờ nhắc; task tự tạo được sinh, cập nhật hoặc xoá) PHẢI được cập
  nhật vào bản sao ngay khi lưu. Dữ liệu trong ứng dụng là bản gốc: chỉnh sửa trực tiếp trong
  Lịch/Lời nhắc không được đọc ngược lại và bị ghi đè ở lần cập nhật sau.
- **FR-054**: Khi tắt đồng bộ, ứng dụng PHẢI xoá lịch và danh sách lời nhắc nó đã tạo.
- **FR-021**: Khi chưa bật đồng bộ, ứng dụng PHẢI hiển thị thông báo của trình duyệt trước giờ bắt
  đầu buổi học và trước hạn chót task theo thời gian nhắc đã đặt, trong lúc tab ứng dụng đang mở
  (kể cả ở nền hoặc cửa sổ thu nhỏ); ứng dụng xin quyền thông báo kèm giải thích. Khi đồng bộ đang
  bật, ứng dụng KHÔNG ĐƯỢC hiện thông báo trình duyệt cho cùng lời nhắc, để mỗi lời nhắc chỉ hiện
  một lần trên mỗi thiết bị. Mỗi lời nhắc chỉ hiện một lần dù mở nhiều tab; nhắc đã lỡ không hiện
  dồn khi mở lại.
- **FR-022**: Người dùng PHẢI chỉnh được thời gian nhắc mặc định (buổi học: mặc định 15 phút trước;
  task có giờ hạn chót: mặc định 1 giờ trước hạn chót; task chỉ có ngày hạn chót: mặc định nhắc lúc
  08:00 sáng ngày đó) và chỉnh riêng hoặc tắt nhắc cho từng môn học, từng task.
- **FR-023**: Ứng dụng KHÔNG ĐƯỢC gửi nhắc cho buổi đã huỷ, task đã hoàn thành hoặc đã xoá, và PHẢI
  cập nhật lịch nhắc ngay khi giờ/hạn chót thay đổi.
- **FR-065**: Ứng dụng PHẢI gửi **thông báo tổng hợp hằng ngày**, bật/tắt được (mặc định bật), giờ
  gửi chỉnh được (mặc định 05:00). Nội dung theo thứ tự: buổi thi trong ngày (giờ, tên học phần,
  phòng), các buổi học chưa huỷ theo giờ bắt đầu (ca hoặc giờ, tên môn, phòng), rồi tiêu đề của tối
  đa 3 task chưa hoàn thành (đến hạn hôm nay trước, rồi quá hạn), các task còn lại gộp thành "+N
  việc khác" (tiêu đề task vốn đã được đồng bộ sang Lời nhắc). KHÔNG có ghi chú, số báo danh hay
  hình thức thi. Ngày không có buổi thi, buổi học, task đến hạn và task quá hạn thì KHÔNG gửi. Ngày
  chỉ có task quá hạn thì gửi theo tuỳ chọn "Gửi tóm tắt khi chỉ có việc quá hạn" (mặc định bật).
- **FR-066**: Khi đồng bộ đang bật, bản tóm tắt của hôm nay và 13 ngày tiếp theo PHẢI được ghi sẵn
  vào lịch "Lịch Học Cá Nhân" kèm lời báo đúng giờ tổng hợp, và PHẢI được cập nhật hoặc xoá ngay khi
  dữ liệu hay cài đặt thay đổi (như FR-053), để iPhone nhận đúng giờ khi Mac gập. Khi chưa bật đồng
  bộ, bản tóm tắt hiện bằng thông báo trình duyệt như FR-021.
- **FR-067**: Task, buổi học và buổi thi PHẢI có công tắc **"Quan trọng"**. Môn học có công tắc áp
  dụng cho mọi buổi của môn; từng buổi học có thể đặt riêng (theo môn / quan trọng / không quan
  trọng). Task và môn mặc định không quan trọng; buổi thi mặc định quan trọng.
- **FR-068**: Mục quan trọng PHẢI được nhắc theo các mốc nhắc quan trọng (mặc định 1 ngày, 3 giờ,
  1 giờ và 15 phút trước), chỉnh được trong cài đặt (tối đa 6 mốc), cộng thêm mốc nhắc riêng của
  mục nếu có, mỗi thời điểm chỉ nhắc một lần. Mục thường nhắc 1 mốc như FR-022. "Không nhắc" (FR-022)
  luôn tắt mọi mốc. Task quan trọng chỉ có ngày hạn chót được nhắc vào giờ nhắc task chỉ có ngày của
  ngày hạn và của từng ngày tương ứng với các mốc ≥ 1 ngày.
- **FR-069**: Buổi thi quan trọng PHẢI được nhắc theo các mốc nhắc quan trọng cộng thêm các mốc riêng
  cho buổi thi (mặc định 7 ngày trước), chỉnh được trong cài đặt; buổi thi không quan trọng nhắc 1
  mốc (mặc định 1 giờ trước). Mốc nhắc riêng của từng buổi thi (FR-063) thay thế các mốc mặc định.
- **FR-070**: Mục quan trọng PHẢI hiển thị nổi bật (dấu ★ và viền đậm) trên lịch ngày, tuần, tháng và
  trang Hôm nay; khi đồng bộ, lời nhắc của task quan trọng có mức ưu tiên cao trong Lời nhắc.

**Ca học**

- **FR-038**: Ứng dụng PHẢI có bảng ca học, mặc định: Ca 1 06:45–09:25, Ca 2 09:35–12:10, Ca 3
  13:00–15:40, Ca 4 15:45–18:25. Người dùng PHẢI sửa được giờ, thêm và xoá ca; giờ kết thúc PHẢI sau
  giờ bắt đầu.
- **FR-039**: Khi thêm hoặc sửa môn học (kể cả nhập nhiều môn), người dùng PHẢI chọn được một ca,
  nhiều ca liền nhau (ví dụ "Ca 1–2": từ giờ bắt đầu ca đầu đến giờ kết thúc ca cuối) hoặc "Giờ tuỳ
  chỉnh" để nhập giờ bằng tay.
- **FR-040**: Môn học chọn ca PHẢI gắn với ca đó: khi người dùng đổi giờ ca và xác nhận (ứng dụng cho
  biết số môn bị ảnh hưởng), giờ các buổi học của những môn này cập nhật theo, trừ buổi đã sửa giờ
  riêng. Xoá ca đang được dùng thì các môn liên quan giữ giờ hiện tại và chuyển sang "Giờ tuỳ chỉnh".
- **FR-041**: Khi nhập từ ảnh, nếu giờ bắt đầu và kết thúc đọc được khớp với một ca hoặc một dãy ca
  liền nhau (lệch tối đa 5 phút), hoặc ảnh ghi tên ca, bảng xem trước PHẢI gán ca đó và dùng giờ theo
  bảng ca; nếu không khớp, dòng đó giữ giờ đọc được ở dạng "Giờ tuỳ chỉnh" kèm ghi chú "không khớp ca
  nào".

**Nhãn**

- **FR-042**: Người dùng PHẢI tạo, đổi tên, đổi màu và xoá được nhãn; tên nhãn bắt buộc và không trùng
  (không phân biệt hoa thường), màu chọn từ bảng màu của ứng dụng; nhiều nhãn được dùng chung một
  màu. Xoá nhãn PHẢI yêu cầu xác nhận và gỡ nhãn khỏi mọi mục.
- **FR-043**: Người dùng PHẢI gắn được nhiều nhãn cho một task, cho một môn học (áp dụng cho mọi buổi
  học của môn) và cho riêng một buổi học (cộng thêm vào nhãn của môn, không ảnh hưởng buổi khác).
- **FR-044**: Trên mọi chế độ xem lịch, mục có nhãn PHẢI hiển thị theo màu của nhãn gắn đầu tiên và
  cho thấy các nhãn còn lại; mục không có nhãn dùng màu môn học hoặc danh sách.
- **FR-045**: Người dùng PHẢI lọc được lịch (ngày, tuần, tháng) và danh sách task theo một hoặc nhiều
  nhãn; chỉ hiện mục có ít nhất một nhãn đã chọn. Bộ lọc giữ nguyên khi chuyển chế độ xem và bỏ
  được bằng một thao tác.

**Tự tạo deadline cho môn đặc biệt**

- **FR-046**: Ứng dụng PHẢI có sẵn nhãn hệ thống "E-Learning" (đổi được màu, không xoá hay đổi tên
  được). Khi nhập từ ảnh, môn học được ghi là E-Learning trong ảnh PHẢI được gợi ý gắn nhãn này.
- **FR-047**: Với mỗi buổi học (không bị huỷ) của môn có nhãn "E-Learning", hoặc bắt đầu từ mốc giờ
  (mặc định 20:00) trở đi, ứng dụng PHẢI tự tạo đúng một task: tiêu đề "Bài tập <tên môn> – buổi
  <dd/mm>", danh sách Học tập, ưu tiên Trung bình, hạn chót vào giờ deadline (mặc định 08:00) của
  Chủ Nhật đầu tiên sau khi buổi học kết thúc; chỉ tạo cho buổi có hạn chót chưa qua.
- **FR-048**: Môn học có tên chứa một mục trong danh sách ngoại lệ (mặc định "Giáo dục thể chất",
  không phân biệt hoa thường) KHÔNG ĐƯỢC tự tạo task. Mốc giờ, giờ deadline và danh sách ngoại lệ
  PHẢI chỉnh được trong cài đặt; thay đổi áp dụng cho các buổi có hạn chót chưa qua.
- **FR-049**: Khi buổi học bị huỷ, đổi giờ, bị xoá cùng môn học, hoặc môn không còn thoả quy tắc,
  task tự tạo tương ứng PHẢI được xoá hoặc cập nhật theo, nếu task đó chưa hoàn thành và chưa bị
  người dùng sửa. Task người dùng đã xoá KHÔNG ĐƯỢC tạo lại.
- **FR-050**: Task tự tạo PHẢI được đánh dấu rõ là "Tự tạo" và mở được buổi học sinh ra nó; ngoài ra
  nó là task bình thường (sửa, hoàn thành, xoá, nhắc như task khác).

**Lịch thi**

- **FR-055**: Người dùng PHẢI thêm, sửa, xoá được buổi thi với: tên học phần (bắt buộc), mã học phần,
  lần thi (số nguyên ≥ 1, mặc định 1), ngày thi (bắt buộc), giờ bắt đầu và giờ kết thúc (bắt buộc,
  kết thúc sau bắt đầu), hình thức thi, phòng thi (có thể trống), số báo danh. Buổi thi là sự kiện
  một lần, không lặp, không thuộc học kỳ hay môn học nào.
- **FR-056**: Ứng dụng PHẢI có sẵn nhãn hệ thống "Thi" (màu nổi bật mặc định, đổi được màu, không xoá
  hay đổi tên được), luôn gắn đầu tiên cho mọi buổi thi; người dùng gắn thêm được nhãn khác.
- **FR-057**: Lịch (ngày, tuần, tháng) và trang Hôm nay PHẢI hiển thị buổi thi theo màu nhãn "Thi";
  trang Hôm nay có khối "Buổi thi" riêng phía trên khối buổi học.
- **FR-058**: Khi buổi thi trùng giờ với buổi học chưa huỷ hoặc với buổi thi khác, ứng dụng PHẢI cảnh
  báo (không chặn) lúc lưu và hiển thị dấu "Trùng giờ" trên lịch và trang Hôm nay.
- **FR-059**: Khi nhập ảnh, ứng dụng PHẢI tự nhận biết ảnh là lịch học dạng tuần hay bảng lịch thi;
  không nhận biết được thì hỏi người dùng chọn loại.
- **FR-060**: Với bảng lịch thi, ứng dụng PHẢI nhận diện các cột: mã học phần, tên học phần, lần thi,
  ngày thi (ngày đầy đủ), giờ thi, hình thức thi, phòng thi, số báo danh; giờ kết thúc thiếu thì
  tính từ thời lượng trong hình thức thi (ví dụ "60p").
- **FR-061**: Cột thông tin sinh viên (họ tên, mã số sinh viên, ngày sinh, lớp) PHẢI bị bỏ qua: không
  có trong kết quả nhận diện, bảng xem trước hay database.
- **FR-062**: Bảng xem trước lịch thi PHẢI đánh dấu "Đã qua" và mặc định bỏ chọn các buổi thi đã kết
  thúc; đánh dấu "Đã có trong lịch" và bỏ qua khi lưu các buổi trùng (cùng mã học phần hoặc tên học
  phần, cùng ngày, cùng giờ bắt đầu, cùng lần thi); vẫn cho sửa mọi ô và đánh dấu ô chưa chắc chắn
  như FR-032, FR-033.
- **FR-063**: Ứng dụng PHẢI nhắc buổi thi theo các mốc mặc định của FR-069 (buổi thi mặc định quan
  trọng: 7 ngày, 1 ngày, 3 giờ, 1 giờ, 15 phút trước); người dùng chỉnh được các mốc mặc định trong
  cài đặt, chỉnh riêng hoặc tắt nhắc cho từng buổi thi.
- **FR-064**: Buổi thi PHẢI được đồng bộ sang Lịch của Apple như buổi học (FR-051 đến FR-054), với
  tiêu đề "Thi: <tên học phần>", phòng thi, thời gian và các lời báo trước; KHÔNG ghi số báo danh hay
  hình thức thi vào bản sao (FR-052). Khi chưa bật đồng bộ, nhắc qua trình duyệt như FR-021.

**Dữ liệu và ràng buộc chung**

- **FR-024**: Mọi dữ liệu PHẢI được lưu cục bộ trên máy ngay khi thay đổi và còn nguyên sau khi tắt
  ứng dụng hoặc khởi động lại máy.
- **FR-025**: Toàn bộ ứng dụng, kể cả nhập lịch học từ ảnh, PHẢI chạy hoàn toàn offline trên máy,
  không cần internet, không yêu cầu đăng nhập và không kết nối ra ngoài máy (kết nối nội bộ
  localhost được phép). Việc đồng bộ sang iPhone (FR-051) do Lịch/Lời nhắc và iCloud của Apple đảm
  nhiệm, không phải ứng dụng.
- **FR-026**: Mọi chữ hiển thị PHẢI là tiếng Việt; ngày giờ theo định dạng Việt Nam
  (ví dụ `Thứ Hai, 16/11/2026`, giờ 24h).
- **FR-027**: Mọi thao tác xoá (task, danh sách, môn học, học kỳ, ca học, nhãn, buổi thi) PHẢI yêu
  cầu xác nhận.

### Key Entities

- **Danh sách**: nhóm task; có tên và màu. Một danh sách chứa nhiều task.
- **Task**: việc cần làm; có tiêu đề, ghi chú, hạn chót (ngày, giờ tuỳ chọn), mức ưu tiên, trạng
  thái hoàn thành, thời gian nhắc, mức "Quan trọng", các nhãn; thuộc đúng một danh sách. Task tự tạo có thêm cờ "Tự
  tạo", liên kết tới buổi học sinh ra nó và trạng thái "đã bị người dùng sửa".
- **Học kỳ**: khoảng thời gian học; có tên, ngày bắt đầu, ngày kết thúc; không chồng lấn với học kỳ
  khác. Một học kỳ chứa nhiều môn học.
- **Môn học**: quy tắc lặp lịch học; thuộc đúng một học kỳ; có tên, mã lớp, giảng viên, màu, các thứ
  trong tuần, ca học (một ca hoặc dãy ca liền nhau) hoặc giờ bắt đầu/kết thúc tuỳ chỉnh, phòng học,
  ngày bắt đầu/kết thúc (nằm trong học kỳ; trùng nhau nếu chỉ học một lần), thời gian nhắc, mức
  "Quan trọng", các nhãn.
- **Ca học**: khung giờ cố định của trường; có tên (ví dụ "Ca 1"), giờ bắt đầu, giờ kết thúc, thứ tự.
- **Nhãn**: có tên (duy nhất) và màu; gắn được cho nhiều task, môn học và buổi học. Nhãn hệ thống
  "E-Learning" không xoá được.
- **Kết quả nhận diện ảnh** (tạm thời, không lưu): danh sách dòng buổi học nhận diện được, mỗi dòng
  có các trường như buổi học, mức độ chắc chắn và lý do cho từng trường, trạng thái "Đã có trong
  lịch", lựa chọn lặp ("chỉ một lần" hoặc "lặp hàng tuần đến ngày ...") và trạng thái được chọn.
- **Buổi học**: một lần học cụ thể của môn học vào một ngày; được suy ra từ môn học, có thể có ngoại
  lệ riêng (đã huỷ, giờ khác, phòng khác), nhãn riêng và mức "Quan trọng" riêng (mặc định theo
  môn); có tối đa một task tự tạo.
- **Cài đặt nhắc**: thời gian nhắc mặc định cho buổi học, cho task có giờ, giờ nhắc cho task chỉ có
  ngày (mặc định 08:00); các mốc nhắc cho mục quan trọng (mặc định 1 ngày, 3 giờ, 1 giờ, 15 phút);
  bật/tắt và giờ gửi thông báo tổng hợp (mặc định bật, 05:00); "Gửi tóm tắt khi chỉ có việc quá
  hạn" (mặc định bật); bật/tắt "Đồng bộ với Lịch và Lời nhắc".
- **Bản tóm tắt hằng ngày** (suy ra, không lưu): ngày, các dòng tóm tắt (buổi thi, buổi học, tối đa
  3 tiêu đề task và "+N việc khác"), thời điểm gửi; không tồn tại với ngày trống.
- **Buổi thi**: sự kiện một lần; có mã học phần, tên học phần, lần thi, ngày, giờ bắt đầu/kết thúc,
  hình thức thi, phòng thi, số báo danh, mức "Quan trọng" (mặc định bật), các mốc nhắc riêng (hoặc
  theo mặc định / tắt), nhãn (luôn có nhãn "Thi").
- **Cài đặt nhắc thi**: các mốc thêm cho buổi thi quan trọng (mặc định 7 ngày trước) và mốc nhắc của
  buổi thi không quan trọng (mặc định 1 giờ trước).
- **Cài đặt tự tạo deadline**: mốc giờ buổi tối (mặc định 20:00), giờ deadline Chủ Nhật (mặc định
  08:00), danh sách tên môn ngoại lệ (mặc định "Giáo dục thể chất").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng tạo được một task mới trong dưới 30 giây.
- **SC-002**: Người dùng nhập được lịch 6 môn học cho cả học kỳ trong dưới 5 phút, trong một lần
  thao tác.
- **SC-003**: 100% buổi học được sinh ra đúng thứ, đúng giờ trong khoảng ngày đã chọn (kiểm tra với
  học kỳ 15 tuần).
- **SC-004**: Huỷ hoặc sửa một buổi học riêng lẻ hoàn tất trong dưới 3 lần bấm/thao tác và không làm
  thay đổi bất kỳ buổi nào khác.
- **SC-005**: Trang "Hôm nay" hiện ra trong dưới 2 giây sau khi mở ứng dụng, với 1 học kỳ dữ liệu
  (khoảng 6 môn và 200 task).
- **SC-006**: Chuyển giữa các chế độ xem ngày/tuần/tháng và sang khoảng thời gian khác phản hồi gần
  như tức thì (dưới 1 giây).
- **SC-007**: Thông báo nhắc trên Mac hiện trong vòng 1 phút so với thời điểm đã đặt khi Mac đang
  mở (qua Lịch/Lời nhắc nếu đã bật đồng bộ, hoặc qua trình duyệt khi tab đang mở nếu chưa bật).
- **SC-017**: Khi đồng bộ đã bật và iCloud đã đồng bộ trước khi Mac gập hoặc tắt, 100% lời nhắc hiện
  trên iPhone trong vòng 1 phút so với thời điểm đã đặt.
- **SC-018**: Sau khi sửa, huỷ hoặc xoá buổi học hay task, 100% bản trong Lịch/Lời nhắc trên Mac khớp
  với dữ liệu trong ứng dụng ngay khi lưu.
- **SC-022**: Khi đồng bộ đã bật và Mac gập liên tục 3 ngày, iPhone nhận 100% bản tóm tắt của các
  ngày không trống, mỗi bản trong vòng 1 phút so với giờ tổng hợp và khớp dữ liệu tại lúc Mac gập;
  0 bản tóm tắt cho ngày trống.
- **SC-023**: 100% mục quan trọng có đúng số mốc nhắc theo cài đặt (trừ mốc đã qua) và hiện nổi bật
  trên lịch và trang Hôm nay; bật hoặc tắt "Quan trọng" mất không quá 2 lần bấm.
- **SC-008**: 0 trường hợp mất dữ liệu khi tắt ứng dụng, tắt đột ngột hoặc khởi động lại máy trong
  kiểm thử.
- **SC-009**: Người dùng tự hoàn thành các tác vụ chính (thêm task, thêm môn học, huỷ một buổi, xem
  lịch tuần) lần đầu mà không cần hướng dẫn.
- **SC-010**: Nhập một tuần thời khoá biểu (khoảng 10 buổi) từ ảnh chụp toàn màn hình, gồm kiểm
  tra và lưu, mất dưới 2 phút.
- **SC-011**: Với ảnh chụp màn hình rõ nét, ít nhất 80% buổi học được nhận diện đúng mọi trường mà
  người dùng không phải sửa; mọi trường sai còn lại đều được đánh dấu chưa chắc chắn hoặc dễ phát
  hiện trong bảng xem trước.
- **SC-012**: Nhập lại cùng một ảnh hai lần tạo ra 0 buổi học trùng.
- **SC-013**: Ứng dụng không gửi dữ liệu hay ảnh nào ra khỏi máy; thứ duy nhất rời máy là bản sao
  lời nhắc trong Lịch/Lời nhắc, do iCloud của người dùng đồng bộ khi đã bật đồng bộ.
- **SC-014**: Thêm một môn học bằng cách chọn ca nhanh hơn nhập giờ tay, hoàn tất trong dưới 20 giây;
  với ảnh có giờ đúng theo bảng ca, 100% dòng nhận diện đúng giờ được gán đúng ca.
- **SC-015**: Với một học kỳ mẫu, 100% buổi học thoả quy tắc có đúng một task tự tạo với hạn 08:00
  Chủ Nhật đúng tuần, và 0 task tự tạo cho môn ngoại lệ hoặc buổi đã huỷ.
- **SC-019**: Với ảnh bảng lịch thi rõ nét, ít nhất 80% buổi thi được nhận diện đúng mọi trường; 100%
  ảnh lịch thi được nhận đúng loại (không nhầm thành lịch học dạng tuần).
- **SC-020**: 0 giá trị họ tên hay mã số sinh viên xuất hiện trong kết quả nhận diện, bảng xem trước
  hay database sau khi nhập ảnh lịch thi.
- **SC-021**: 100% buổi thi đã qua trong ảnh được đánh dấu "Đã qua" và bỏ chọn; 100% buổi thi trùng
  giờ với buổi học chưa huỷ có cảnh báo.
- **SC-016**: Lọc theo nhãn cập nhật lịch và danh sách gần như tức thì (dưới 1 giây) và chỉ hiện đúng
  các mục có nhãn đã chọn.

## Assumptions

- Chỉ một người dùng, trên một máy Mac; không có đăng nhập hay chia sẻ, không đồng bộ dữ liệu giữa
  thiết bị ngoài bản sao lời nhắc qua Lịch/Lời nhắc và iCloud (theo constitution).
- "Nhập nhiều môn cùng lúc" nghĩa là một biểu mẫu nhiều dòng do người dùng điền tay, dùng chung một
  khoảng ngày; nhập từ file (Excel, CSV) hoặc kết nối trực tiếp với cổng thông tin trường nằm
  ngoài phạm vi (chỉ hỗ trợ nhập từ ảnh chụp màn hình).
- Ảnh thời khoá biểu thường là ảnh chụp toàn màn hình máy Mac, bằng tiếng Việt, có định dạng giống
  cổng thông tin sinh viên phổ biến (dạng lưới tuần hoặc dạng danh sách); mỗi lần nhập một ảnh.
- Hai buổi học được coi là trùng khi cùng tên môn (hoặc cùng mã lớp), cùng ngày và cùng giờ bắt
  đầu.
- Mỗi môn học dùng một khoảng ngày; môn học có lịch khác nhau giữa các thứ (ví dụ Thứ Hai phòng A,
  Thứ Năm phòng B) có thể nhập thành nhiều dòng.
- Task không lặp lại (không có task định kỳ) trong phiên bản này.
- Tuần bắt đầu từ Thứ Hai; múi giờ là múi giờ của máy (Việt Nam).
- Ứng dụng được dùng qua trình duyệt trên Mac. Thông báo của trình duyệt chỉ là phương án dự phòng
  khi chưa bật đồng bộ.
- Người dùng có iPhone đăng nhập cùng Apple ID với Mac và đã bật iCloud cho Lịch và Lời nhắc; thời
  gian đồng bộ do Apple quyết định (thường vài phút khi cả hai thiết bị có mạng).
- Khi Mac gập (ngủ) hoặc tắt, Mac không hiện thông báo; chỉ iPhone nhắc.
- Bản tóm tắt hằng ngày trên iPhone là một sự kiện cả ngày trong lịch "Lịch Học Cá Nhân" có lời báo
  đúng giờ tổng hợp; nội dung chính nằm ở tiêu đề để hiện trong thông báo.
- Đổi giờ ca áp dụng cho mọi buổi học của các môn dùng ca đó (kể cả buổi đã qua), trừ buổi đã sửa
  giờ riêng.
- "Buổi học bắt đầu sau 20:00" được hiểu là bắt đầu lúc 20:00 hoặc muộn hơn.
- Môn Giáo dục thể chất được nhận biết theo tên môn; người dùng tự thêm cách viết khác (ví dụ "GDTC")
  vào danh sách ngoại lệ nếu cần.
- Thời gian nhắc chọn từ các mốc sẵn (ví dụ 5, 10, 15, 30 phút, 1 giờ, 1 ngày) hoặc nhập số phút
  tuỳ ý.
- Màu sắc chọn từ một bảng màu cố định khoảng 10–12 màu dễ phân biệt.
- Bảng "Lịch thi cá nhân" trên cổng sinh viên có dạng bảng, mỗi dòng một buổi thi, với tiêu đề cột
  tiếng Việt (ví dụ "Mã học phần", "Tên học phần", "Lần thi", "Ngày thi", "Giờ thi", "Hình thức thi",
  "Phòng thi", "SBD") và ngày thi đầy đủ dạng dd/mm/yyyy. Mỗi lần nhập một ảnh, một loại lịch.
- Buổi thi không gắn với môn học hay học kỳ; không áp dụng quy tắc tự tạo deadline (US10) cho buổi
  thi.
- Không có tính năng tìm kiếm, thống kê, xuất/nhập dữ liệu trong phiên bản này; người dùng tự sao
  lưu bằng cách sao chép thư mục dữ liệu (vị trí ghi trong README).
