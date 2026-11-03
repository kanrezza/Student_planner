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

Ứng dụng gửi thông báo nhắc trên máy Mac trước khi buổi học bắt đầu và trước hạn chót của task.
Người dùng chỉnh được thời gian nhắc mặc định và chỉnh riêng cho từng môn học hoặc từng task, hoặc
tắt nhắc.

**Why this priority**: Hữu ích nhưng người dùng vẫn dùng được ứng dụng bằng cách tự xem trang Hôm
nay.

**Independent Test**: Đặt nhắc 5 phút trước một buổi học và 10 phút trước hạn chót một task trong
tương lai gần; kiểm tra thông báo hiện đúng thời điểm với nội dung tiếng Việt.

**Acceptance Scenarios**:

1. **Given** nhắc mặc định cho buổi học là 15 phút, **When** còn 15 phút tới giờ học, **Then** máy
   hiện thông báo gồm tên môn, giờ bắt đầu và phòng học.
2. **Given** task có hạn chót và thời gian nhắc, **When** tới thời điểm nhắc, **Then** máy hiện
   thông báo gồm tiêu đề task và hạn chót.
3. **Given** người dùng đổi thời gian nhắc của một task hoặc môn học, **Then** thông báo hiện theo
   thời gian mới thay vì mặc định.
4. **Given** buổi học đã bị huỷ hoặc task đã hoàn thành/đã xoá, **When** tới thời điểm nhắc, **Then**
   không có thông báo nào.
5. **Given** người dùng tắt nhắc cho một mục, **Then** mục đó không gửi thông báo.

---

### Edge Cases

- Ngày bắt đầu học kỳ không rơi vào thứ của môn học: buổi đầu tiên là ngày đúng thứ đó gần nhất sau
  ngày bắt đầu.
- Khoảng ngày không chứa thứ nào đã chọn (ví dụ chỉ 3 ngày): ứng dụng cảnh báo rằng không có buổi
  học nào được tạo.
- Hai buổi học trùng giờ: ứng dụng vẫn cho lưu nhưng hiển thị cảnh báo trùng lịch.
- Task không có hạn chót: không xuất hiện trên lịch và trang Hôm nay, chỉ trong danh sách của nó.
- Task có hạn chót nhưng không có giờ: coi như hạn vào cuối ngày (23:59).
- Xoá một danh sách đang có task: ứng dụng hỏi chuyển task sang danh sách khác hoặc xoá luôn các
  task đó.
- Ứng dụng không chạy vào thời điểm cần nhắc: các nhắc đã lỡ không bắn dồn khi mở lại, nhưng task
  quá hạn vẫn hiện ở nhóm "Quá hạn".
- Người dùng đã tắt quyền thông báo của ứng dụng trong cài đặt máy: ứng dụng hiển thị hướng dẫn bằng
  tiếng Việt để bật lại.
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
- Tiêu đề, ghi chú, tên môn và phòng học có dấu tiếng Việt và ký tự đặc biệt được lưu và hiển thị
  đúng.

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

- **FR-007**: Người dùng PHẢI thêm được môn học với tên môn (bắt buộc), mã lớp (tuỳ chọn), giảng
  viên (tuỳ chọn), một hoặc nhiều thứ trong tuần, giờ bắt đầu, giờ kết thúc, phòng học (tuỳ chọn),
  ngày bắt đầu và ngày kết thúc. Môn học chỉ học một lần có ngày bắt đầu trùng ngày kết thúc.
- **FR-008**: Ứng dụng PHẢI tự sinh buổi học vào mỗi thứ đã chọn, lặp hàng tuần, trong khoảng ngày
  bắt đầu đến ngày kết thúc (tính cả hai đầu).
- **FR-009**: Người dùng PHẢI nhập được nhiều môn học trong một lần thao tác, dùng chung một khoảng
  ngày (cả tháng hoặc cả học kỳ), với khả năng thêm/bớt dòng trước khi lưu.
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
  dùng đổi được.
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
  hình.
- **FR-031**: Ứng dụng PHẢI xác định tháng/năm từ dấu hiệu trong ảnh (lịch tháng thu nhỏ, tiêu đề
  tuần, ngày giờ hệ thống) và cho người dùng biết dấu hiệu đã dùng.
- **FR-032**: Ô nào không đọc được hoặc không chắc chắn PHẢI được đánh dấu nổi bật kèm lý do; ứng
  dụng KHÔNG ĐƯỢC lưu dòng có ô bắt buộc (tên môn, ngày, giờ bắt đầu, giờ kết thúc) còn chưa chắc
  chắn cho tới khi người dùng xác nhận hoặc sửa.
- **FR-033**: Trước khi lưu, ứng dụng PHẢI luôn hiển thị bảng xem trước cho phép sửa mọi ô, chọn/bỏ
  chọn từng dòng, và chọn cho từng dòng "chỉ một lần" hoặc "lặp hàng tuần đến ngày ..." (mặc định
  là lặp đến ngày kết thúc học kỳ nếu đã biết, nếu chưa thì "chỉ một lần").
- **FR-034**: Ứng dụng KHÔNG ĐƯỢC tạo buổi học trùng: buổi học có cùng tên môn (hoặc cùng mã lớp),
  cùng ngày và cùng giờ bắt đầu với buổi đã có được đánh dấu "Đã có trong lịch", mặc định bỏ chọn
  và bị bỏ qua khi lưu. Quy tắc này cũng áp dụng giữa các dòng trong cùng một lần nhập.
- **FR-035**: Ảnh và kết quả nhận diện chưa lưu KHÔNG ĐƯỢC lưu lại sau khi người dùng đóng bảng xem
  trước; chỉ các buổi học người dùng đã xác nhận mới được lưu cục bộ.

**Thông báo nhắc**

- **FR-021**: Ứng dụng PHẢI gửi thông báo hệ thống của máy Mac trước giờ bắt đầu buổi học và trước
  hạn chót task theo thời gian nhắc đã đặt.
- **FR-022**: Người dùng PHẢI chỉnh được thời gian nhắc mặc định (buổi học: mặc định 15 phút trước;
  task: mặc định 1 giờ trước hạn chót) và chỉnh riêng hoặc tắt nhắc cho từng môn học, từng task.
- **FR-023**: Ứng dụng KHÔNG ĐƯỢC gửi nhắc cho buổi đã huỷ, task đã hoàn thành hoặc đã xoá, và PHẢI
  cập nhật lịch nhắc ngay khi giờ/hạn chót thay đổi.

**Dữ liệu và ràng buộc chung**

- **FR-024**: Mọi dữ liệu PHẢI được lưu cục bộ trên máy ngay khi thay đổi và còn nguyên sau khi tắt
  ứng dụng hoặc khởi động lại máy.
- **FR-025**: Toàn bộ ứng dụng, kể cả nhập lịch học từ ảnh, PHẢI chạy hoàn toàn offline trên máy,
  không cần internet và không yêu cầu đăng nhập.
- **FR-026**: Mọi chữ hiển thị PHẢI là tiếng Việt; ngày giờ theo định dạng Việt Nam
  (ví dụ `Thứ Hai, 16/11/2026`, giờ 24h).
- **FR-027**: Mọi thao tác xoá (task, danh sách, môn học) PHẢI yêu cầu xác nhận.

### Key Entities

- **Danh sách**: nhóm task; có tên và màu. Một danh sách chứa nhiều task.
- **Task**: việc cần làm; có tiêu đề, ghi chú, hạn chót (ngày, giờ tuỳ chọn), mức ưu tiên, trạng
  thái hoàn thành, thời gian nhắc; thuộc đúng một danh sách.
- **Môn học**: quy tắc lặp lịch học; có tên, mã lớp, giảng viên, màu, các thứ trong tuần, giờ bắt
  đầu/kết thúc, phòng học, ngày bắt đầu/kết thúc (trùng nhau nếu chỉ học một lần), thời gian nhắc.
- **Kết quả nhận diện ảnh** (tạm thời, không lưu): danh sách dòng buổi học nhận diện được, mỗi dòng
  có các trường như buổi học, mức độ chắc chắn và lý do cho từng trường, trạng thái "Đã có trong
  lịch", lựa chọn lặp ("chỉ một lần" hoặc "lặp hàng tuần đến ngày ...") và trạng thái được chọn.
- **Buổi học**: một lần học cụ thể của môn học vào một ngày; được suy ra từ môn học, có thể có ngoại
  lệ riêng (đã huỷ, giờ khác, phòng khác).
- **Cài đặt nhắc**: thời gian nhắc mặc định cho buổi học và cho task.

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
- **SC-007**: Thông báo nhắc hiện trong vòng 1 phút so với thời điểm đã đặt khi ứng dụng đang chạy.
- **SC-008**: 0 trường hợp mất dữ liệu khi tắt ứng dụng, tắt đột ngột hoặc khởi động lại máy trong
  kiểm thử.
- **SC-009**: Người dùng tự hoàn thành các tác vụ chính (thêm task, thêm môn học, huỷ một buổi, xem
  lịch tuần) lần đầu mà không cần hướng dẫn.
- **SC-010**: Nhập một tuần thời khoá biểu (khoảng 10 buổi) từ ảnh chụp toàn màn hình, gồm kiểm
  tra và lưu, mất dưới 2 phút.
- **SC-011**: Với ảnh chụp màn hình rõ nét, ít nhất 90% buổi học được nhận diện đúng mọi trường mà
  người dùng không phải sửa; mọi trường sai còn lại đều được đánh dấu chưa chắc chắn hoặc dễ phát
  hiện trong bảng xem trước.
- **SC-012**: Nhập lại cùng một ảnh hai lần tạo ra 0 buổi học trùng.
- **SC-013**: Không có dữ liệu hay ảnh nào bị gửi ra khỏi máy.

## Assumptions

- Chỉ một người dùng, trên một máy Mac; không có đăng nhập, đồng bộ hay chia sẻ (theo constitution).
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
- Thông báo được gửi khi ứng dụng đang chạy (kể cả khi cửa sổ đã đóng nhưng ứng dụng chạy nền);
  khi ứng dụng hoàn toàn tắt thì không có nhắc.
- Thời gian nhắc chọn từ các mốc sẵn (ví dụ 5, 10, 15, 30 phút, 1 giờ, 1 ngày) hoặc nhập số phút
  tuỳ ý.
- Màu sắc chọn từ một bảng màu cố định khoảng 10–12 màu dễ phân biệt.
- Không có tính năng tìm kiếm, thống kê, xuất/nhập dữ liệu trong phiên bản này; người dùng tự sao
  lưu bằng cách sao chép thư mục dữ liệu (vị trí ghi trong README).
