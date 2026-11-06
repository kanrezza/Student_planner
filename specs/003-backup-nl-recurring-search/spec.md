# Feature Specification: Sao lưu tự động, thêm nhanh bằng câu tiếng Việt, task lặp lại và tìm kiếm

**Feature Branch**: `003-backup-nl-recurring-search`

**Created**: 2026-11-05

**Status**: Done (các kịch bản cần thao tác tay trên máy còn lại ghi ở validation.md)

**Input**: User description: "Bổ sung 4 tính năng cho Lịch Học Cá Nhân (app macOS hiện có, feature 001
và 002 đã xong): (1) Sao lưu tự động (ưu tiên cao nhất): mỗi ngày tự sao lưu toàn bộ dữ liệu vào một
thư mục người dùng chọn (mặc định iCloud Drive/Lịch Học Cá Nhân/Sao lưu; có thể chọn ổ SSD rời). Giờ
sao lưu chỉnh được; nếu đến giờ mà Mac đang tắt hoặc ngủ thì sao lưu bù ở lần chạy kế tiếp. Giữ 14
bản gần nhất (chỉnh được), bản cũ hơn tự xoá. Trong Cài đặt có: trạng thái lần sao lưu gần nhất (thời
gian, dung lượng, lỗi nếu có), nút "Sao lưu ngay", danh sách bản sao lưu để "Khôi phục" (hỏi xác nhận,
tự sao lưu dữ liệu hiện tại trước khi khôi phục). Thư mục đích không có (ví dụ SSD đã tháo) thì bỏ
qua, cảnh báo nhẹ và thử lại lần sau, không làm hỏng app. Cập nhật constitution: cho phép sao lưu vào
iCloud Drive của chính người dùng. (2) Thêm nhanh bằng ngôn ngữ tự nhiên tiếng Việt: trong ô "Thêm
công việc", app tự hiểu ngày giờ, nhãn, danh sách và mức quan trọng từ câu gõ. Ví dụ "Nộp bài QTDA
thứ 6 9h #Gấp" tạo task "Nộp bài QTDA", hạn 09:00 Thứ Sáu gần nhất, nhãn Gấp. Hiểu được: hôm nay,
mai/ngày mai, mốt/ngày kia, thứ 2…thứ 7, chủ nhật/CN, "tuần sau", "thứ 6 tuần sau", ngày dạng 20/11
hoặc 20/11/2026; giờ dạng 9h, 9h30, 21:00, "9 giờ tối", sáng/chiều/tối; #nhãn, ~danh sách (gợi ý tự
hoàn thành), dấu * hoặc "quan trọng" để đánh dấu Quan trọng; cụm lặp lại như "hằng ngày", "mỗi
tuần", "thứ 2 hàng tuần". Phần được hiểu được tô sáng ngay khi gõ và hiện trước kết quả (hạn, nhãn,
danh sách) trước khi nhấn Enter; bấm vào phần tô sáng để huỷ hiểu, giữ nguyên làm chữ. Phần đã hiểu
được bỏ khỏi tiêu đề. Xử lý hoàn toàn trên máy, không dùng AI hay internet. (3) Task lặp lại: lặp hằng
ngày, mỗi N ngày, hằng tuần (chọn một hoặc nhiều thứ), hằng tháng (theo ngày trong tháng), kết thúc
vào một ngày hoặc sau N lần hoặc không kết thúc. Hoàn thành một lần thì lần kế tiếp xuất hiện. Sửa
hoặc xoá thì hỏi "chỉ lần này" hay "lần này và các lần sau". Task lặp hiện đúng trên danh sách thông
minh, lịch, bản tóm tắt hằng ngày, nhắc lịch và đồng bộ Lời nhắc/iPhone. (4) Tìm kiếm: nhấn ⌘F (hoặc
ô tìm kiếm ở cột danh sách) để tìm trong task (tiêu đề, ghi chú), môn học, buổi học và buổi thi.
Không phân biệt dấu và hoa thường ("nop bai" tìm được "Nộp bài"). Kết quả nhóm theo loại, tô sáng chữ
khớp, có tuỳ chọn gồm cả task đã hoàn thành; bấm vào kết quả để mở chi tiết. Kết quả hiện ngay khi
gõ. Mọi chức năng hiện có giữ nguyên. Giao diện tiếng Việt, theo phong cách của feature 002."

## Bối cảnh

Feature này bổ sung bốn tính năng vào app macOS "Lịch Học Cá Nhân" đã có (feature
`001-task-class-scheduler` và `002-redesign-macos-app`). Mọi dữ liệu, quy tắc nghiệp vụ, bố cục và
chức năng hiện có (task, danh sách, nhãn, ưu tiên, Quan trọng, khung giờ làm, Thùng rác, học kỳ, môn
học, buổi học, buổi thi, deadline tự tạo, nhắc lịch, đồng bộ Lịch và Lời nhắc, bản tóm tắt hằng ngày,
nhập ảnh, lịch tuần, kéo thả, phím tắt) được giữ nguyên. Giao diện mới theo đúng phong cách của feature
002 (bo góc mềm, nhiều khoảng trắng, sáng/tối theo macOS, chữ tiếng Việt).

Hiện tại việc sao lưu chỉ làm thủ công bằng script trong README; feature này biến sao lưu thành chức
năng tự động trong app. Constitution IV (Ngoại lệ iCloud) được mở rộng để cho phép ghi bản sao lưu vào
iCloud Drive của chính người dùng (xem FR-014).

Ví dụ trong spec lấy hôm nay là **Thứ Năm, 05/11/2026**.

## Clarifications

### Session 2026-11-05

- Q: Đang xem danh sách có ngày mặc định (ví dụ "Ngày mai") mà câu chỉ có giờ, không có ngày, thì hạn
  là gì? → A: Ghép giờ trong câu với ngày mặc định của danh sách đang xem (Ngày mai → ngày mai; Hôm nay /
  7 ngày tới → hôm nay, kể cả khi giờ đã qua); danh sách không có ngày mặc định thì theo FR-028 (hôm nay
  nếu giờ chưa qua, nếu không thì ngày mai).
- Q: Sửa "Lần này và các lần sau" mà đổi ngày hạn của task lặp thì quy tắc lặp có dời theo không? → A:
  Có — quy tắc dời theo ngày mới (hằng ngày / mỗi N ngày đếm lại từ ngày mới; hằng tuần thay thứ cũ
  bằng thứ mới; hằng tháng đổi ngày D thành ngày mới); đổi giờ thì mọi lần sau đổi giờ theo.
- Q: Ngoài cảnh báo nhẹ trong app, có gửi thông báo macOS khi sao lưu lỗi hoặc lâu không sao lưu
  không? → A: Gửi một thông báo macOS khi đã quá 3 ngày không có bản sao lưu thành công; không nhắc lại
  cho đến khi có bản thành công. Lỗi lẻ từng lần chỉ cảnh báo nhẹ trong app.
- Q: File sao lưu có cần mã hoá bằng mật khẩu không? → A: Không mã hoá; dựa vào bảo vệ của iCloud và ổ
  đĩa của chính người dùng, khôi phục không cần mật khẩu.
- Q: Tìm kiếm có tìm cả tên nhãn và tên danh sách không? → A: Có; bấm vào kết quả nhãn/danh sách thì mở
  danh sách task lọc theo nhãn/danh sách đó.
- Q: Log của sao lưu ghi ở đâu? → A: Ghi vào file log hiện có của trình đồng bộ chạy nền (agent), như
  các hoạt động nền khác.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sao lưu tự động hằng ngày (Priority: P1)

Người dùng không muốn mất dữ liệu học tập nếu ổ đĩa hỏng, lỡ xoá volume dữ liệu hay cài lại máy. Mỗi
ngày, vào giờ đã đặt (mặc định 21:00), app tự sao lưu toàn bộ dữ liệu vào thư mục người dùng chọn —
mặc định `iCloud Drive/Lịch Học Cá Nhân/Sao lưu`, hoặc một thư mục trên ổ SSD rời. Nếu đến giờ mà Mac
tắt hoặc đang ngủ, bản sao lưu được tạo bù ngay khi có thể. App giữ 14 bản gần nhất (chỉnh được), bản
cũ hơn tự xoá. Trong Cài đặt, người dùng thấy lần sao lưu gần nhất (lúc nào, dung lượng, lỗi nếu có)
và có nút "Sao lưu ngay".

**Why this priority**: Đây là yêu cầu ưu tiên cao nhất của người dùng; với ứng dụng cá nhân không có
server, mất dữ liệu cục bộ là mất vĩnh viễn (constitution V). Tự nó đã mang lại giá trị đầy đủ.

**Independent Test**: Đặt giờ sao lưu sau 2 phút, đợi đến giờ và kiểm tra trong thư mục đích có một
bản sao lưu mới, Cài đặt hiện đúng thời gian và dung lượng; tạo 16 bản với giới hạn 14 và kiểm tra chỉ
còn 14 bản mới nhất.

**Acceptance Scenarios**:

1. **Given** sao lưu tự động đang bật với giờ 21:00 và thư mục mặc định, **When** đồng hồ qua 21:00
   khi Mac đang thức, **Then** trong vòng 5 phút có một bản sao lưu mới trong
   `iCloud Drive/Lịch Học Cá Nhân/Sao lưu`, tên bản có ngày giờ dễ đọc, và Cài đặt hiện "Lần gần nhất:
   21:00 Thứ Năm, 05/11/2026 — 2,4 MB — Thành công".
2. **Given** Mac gập máy (ngủ) từ 18:00 đến 07:30 sáng hôm sau, **When** Mac thức dậy lúc 07:30,
   **Then** trong vòng 5 phút app tạo bản sao lưu bù cho lần 21:00 đã lỡ, chỉ một bản (không tạo nhiều bản
   cho nhiều ngày bị lỡ).
3. **Given** Mac tắt hẳn suốt 3 ngày, **When** người dùng bật Mac và phần lưu trữ dữ liệu chạy lại,
   **Then** app tạo đúng một bản sao lưu bù.
4. **Given** đang có 14 bản và giới hạn là 14, **When** một bản mới được tạo thành công, **Then** bản
   cũ nhất bị xoá, còn đúng 14 bản.
5. **Given** người dùng đổi giới hạn từ 14 xuống 7, **When** bản sao lưu kế tiếp tạo thành công,
   **Then** chỉ còn 7 bản mới nhất.
6. **Given** người dùng chọn thư mục trên ổ SSD rời rồi tháo ổ, **When** đến giờ sao lưu, **Then** app
   bỏ qua lần này, không treo, không hiện hộp thoại chặn; Cài đặt hiện cảnh báo nhẹ và biểu tượng Cài
   đặt ở thanh biểu tượng có chấm cảnh báo (không có thông báo macOS) "Không tìm thấy thư mục sao lưu (ổ đĩa có thể đã được tháo). Sẽ thử lại khi ổ được cắm lại.";
   khi ổ được cắm lại, app sao lưu bù trong vòng 5 phút.
7. **Given** người dùng bấm "Sao lưu ngay", **Then** app tạo một bản sao lưu ngay, nút hiện trạng thái
   đang chạy, xong thì trạng thái trong Cài đặt cập nhật; app vẫn dùng bình thường trong lúc sao lưu.
8. **Given** người dùng đổi giờ sao lưu thành 22:00, **Then** lần sao lưu tự động kế tiếp diễn ra lúc
   22:00.
9. **Given** sao lưu thất bại (ví dụ ổ đầy), **Then** Cài đặt hiện "Lần gần nhất thất bại" kèm lý do
   tiếng Việt và cách khắc phục, các bản sao lưu cũ không bị xoá, và lần sao lưu thành công gần nhất
   vẫn được hiện riêng.
10. **Given** đã quá 3 ngày không có bản sao lưu thành công (ví dụ SSD rời tháo suốt 4 ngày), **Then** app
    gửi đúng một thông báo macOS "Đã 3 ngày chưa sao lưu được dữ liệu…"; bấm vào thì mở Cài đặt → Sao
    lưu; không có thông báo thứ hai cho đến khi sao lưu lại thành công.

---

### User Story 2 - Khôi phục từ bản sao lưu (Priority: P1)

Khi dữ liệu bị mất hoặc sai, người dùng mở Cài đặt → Sao lưu, chọn một bản trong danh sách và bấm
"Khôi phục". App hỏi xác nhận, tự sao lưu dữ liệu hiện tại trước, rồi thay toàn bộ dữ liệu bằng bản
đã chọn.

**Why this priority**: Sao lưu mà không khôi phục được thì vô ích; đây là nửa còn lại của US1.

**Independent Test**: Tạo một task, sao lưu, xoá hẳn task, khôi phục bản vừa tạo và kiểm tra task trở
lại; kiểm tra có thêm bản "Trước khi khôi phục" chứa dữ liệu ngay trước lúc khôi phục.

**Acceptance Scenarios**:

1. **Given** danh sách bản sao lưu trong Cài đặt, **Then** mỗi bản hiện ngày giờ tạo, dung lượng và
   loại (Tự động / Thủ công / Trước khi khôi phục), mới nhất ở trên.
2. **Given** người dùng bấm "Khôi phục" ở bản 21:00 04/11/2026, **Then** app hỏi xác nhận: "Khôi phục
   dữ liệu về lúc 21:00 Thứ Tư, 04/11/2026? Dữ liệu hiện tại sẽ được sao lưu trước rồi bị thay thế." với
   nút "Khôi phục" và "Huỷ".
3. **Given** người dùng xác nhận, **Then** app tạo bản sao lưu "Trước khi khôi phục" của dữ liệu hiện
   tại, sau đó khôi phục; khi xong, mọi màn hình hiện dữ liệu của bản đã chọn và có thông báo "Đã khôi
   phục dữ liệu về 21:00 04/11/2026".
4. **Given** không tạo được bản "Trước khi khôi phục" (ví dụ thư mục đích không có), **Then** app không
   khôi phục và báo lỗi, dữ liệu hiện tại giữ nguyên.
5. **Given** bản sao lưu được chọn bị hỏng hoặc không đọc được, **Then** app báo "Bản sao lưu bị hỏng,
   không thể khôi phục", dữ liệu hiện tại giữ nguyên.
6. **Given** đồng bộ Lịch và Lời nhắc đang bật, **When** khôi phục xong, **Then** các mục trong Lịch và
   Lời nhắc được cập nhật theo dữ liệu đã khôi phục (mục không còn thì bị xoá, mục mới thì được thêm).

---

### User Story 3 - Task lặp lại (Priority: P2)

Người dùng có những việc lặp đi lặp lại: ôn từ vựng mỗi ngày, nộp báo cáo tuần thứ 2 và thứ 5, đóng
tiền nhà ngày 5 hằng tháng. Trong bảng chi tiết task, người dùng đặt "Lặp lại": hằng ngày, mỗi N ngày,
hằng tuần (một hoặc nhiều thứ), hằng tháng (theo ngày trong tháng), với kết thúc: không bao giờ, vào
một ngày, hoặc sau N lần. Hoàn thành lần hiện tại thì lần kế tiếp xuất hiện với hạn mới.

**Why this priority**: Giảm việc tạo lại task thủ công mỗi tuần; là nền cho cụm "hằng ngày" trong US4.

**Independent Test**: Tạo task "Ôn từ vựng" hạn 20:00 hôm nay lặp hằng ngày, đánh dấu hoàn thành và
kiểm tra task xuất hiện lại với hạn 20:00 ngày mai, lần đã xong nằm trong Đã hoàn thành.

**Acceptance Scenarios**:

1. **Given** task "Nộp báo cáo tuần" hạn 17:00 Thứ Năm 05/11 lặp hằng tuần vào Thứ Hai và Thứ Năm,
   **When** đánh dấu hoàn thành, **Then** lần đó vào Đã hoàn thành và lần kế tiếp xuất hiện với hạn
   17:00 Thứ Hai 09/11, giữ nguyên tiêu đề, ghi chú, danh sách, nhãn, ưu tiên, Quan trọng, nhắc và
   khung giờ làm (khung giờ dời theo ngày mới).
2. **Given** task lặp "mỗi 3 ngày" hạn 05/11, **When** hoàn thành, **Then** lần kế tiếp hạn 08/11.
3. **Given** task lặp hằng tháng vào ngày 31, **When** tháng kế tiếp không có ngày 31, **Then** lần đó
   rơi vào ngày cuối tháng (ví dụ 30/11), tháng sau nữa trở lại ngày 31.
4. **Given** task lặp "kết thúc sau 3 lần", **When** hoàn thành lần thứ 3, **Then** không có lần kế
   tiếp. **Given** task lặp "kết thúc vào 30/11/2026", **When** lần kế tiếp rơi sau 30/11, **Then**
   không tạo lần đó.
5. **Given** task lặp hằng ngày đã quá hạn 3 ngày (hạn 02/11), **When** hoàn thành hôm nay 05/11,
   **Then** lần kế tiếp có hạn là ngày lặp gần nhất từ hôm nay trở đi (05/11 nếu giờ hạn chưa qua, nếu
   không thì 06/11), không sinh ra các lần đã lỡ.
6. **Given** bỏ đánh dấu hoàn thành một lần vừa xong, **Then** lần kế tiếp vừa được tạo (nếu chưa bị
   sửa) bị gỡ và lần cũ trở lại như trước.
7. **Given** người dùng sửa tiêu đề của một task lặp, **Then** app hỏi "Chỉ lần này" hay "Lần này và các
   lần sau"; chọn "Chỉ lần này" thì chỉ lần hiện tại đổi, các lần sau giữ tiêu đề cũ; chọn "Lần này và
   các lần sau" thì lần hiện tại và mọi lần sau đều đổi.
8. **Given** người dùng xoá một task lặp, **Then** app hỏi "Chỉ lần này" hay "Lần này và các lần sau";
   "Chỉ lần này" chuyển lần hiện tại vào Thùng rác và lần kế tiếp xuất hiện; "Lần này và các lần sau"
   chuyển task vào Thùng rác và chuỗi lặp dừng. Cả hai có "Hoàn tác".
9. **Given** task lặp hằng ngày hạn 20:00 có nhắc trước 15 phút và đồng bộ Lời nhắc đang bật, **Then**
   iPhone nhận nhắc cho lần hiện tại; sau khi hoàn thành, Lời nhắc có lần kế tiếp với giờ mới trong vòng
   1 phút.
10. **Given** task lặp hằng ngày, **When** xem lịch tuần, **Then** lần hiện tại hiện như task thường, các
    lần sau trong tuần hiện dạng khối mờ có biểu tượng lặp ("dự kiến"); bấm vào khối dự kiến mở chi
    tiết chuỗi lặp.
11. **Given** task lặp hằng ngày hạn 20:00, **Then** bản tóm tắt hằng ngày của mỗi ngày tới (kể cả các
    ngày đã được tạo sẵn) có task này.
12. **Given** dòng task trong danh sách, **Then** task lặp có biểu tượng lặp nhỏ cạnh giờ hạn; rê chuột
    hiện mô tả "Lặp hằng tuần vào Thứ Hai, Thứ Năm".

---

### User Story 4 - Thêm nhanh bằng câu tiếng Việt (Priority: P2)

Người dùng gõ vào ô "Thêm công việc" một câu tự nhiên như "Nộp bài QTDA thứ 6 9h #Gấp". Ngay khi gõ,
"thứ 6", "9h" và "#Gấp" được tô sáng; phía dưới ô hiện trước kết quả: "Hạn: 09:00 Thứ Sáu, 06/11 · Nhãn:
Gấp". Nhấn Enter tạo task tiêu đề "Nộp bài QTDA" với đúng hạn và nhãn. Nếu app hiểu nhầm (ví dụ "mai"
trong "Gọi chị Mai"), người dùng bấm vào phần tô sáng để huỷ, phần đó giữ nguyên là chữ trong tiêu đề.

**Why this priority**: Tăng tốc rõ rệt thao tác thêm task hằng ngày, nhưng app vẫn dùng được đầy đủ
mà không có nó (đặt hạn trong bảng chi tiết như hiện nay).

**Independent Test**: Gõ từng câu trong bảng ví dụ ở FR-030, kiểm tra phần tô sáng, phần xem trước và
task tạo ra; bấm vào phần tô sáng để huỷ và kiểm tra tiêu đề giữ chữ đó.

**Acceptance Scenarios** (hôm nay Thứ Năm 05/11/2026, 10:00; trừ khi ghi khác, đang xem danh sách Tất cả):

1. **Given** gõ "Nộp bài QTDA thứ 6 9h #Gấp", **Then** tô sáng "thứ 6", "9h", "#Gấp"; xem trước "Hạn:
   09:00 Thứ Sáu, 06/11 · Nhãn: Gấp"; Enter tạo task "Nộp bài QTDA".
2. **Given** gõ "Họp nhóm mai 14h ~Cá nhân", **Then** hạn 14:00 Thứ Sáu 06/11, danh sách Cá nhân.
3. **Given** gõ "Đi khám mốt 9 giờ sáng", **Then** hạn 09:00 Thứ Bảy 07/11.
4. **Given** gõ "Thi thử thứ 6 tuần sau 21:00 quan trọng", **Then** hạn 21:00 Thứ Sáu 13/11, đánh dấu
   Quan trọng; tiêu đề "Thi thử".
5. **Given** gõ "Gọi điện về nhà 9 giờ tối", **Then** hạn 21:00 hôm nay. **Given** gõ "Mua sữa 8h", vì
   08:00 hôm nay đã qua **Then** hạn 08:00 ngày mai.
6. **Given** gõ "Nộp đồ án 20/11", **Then** hạn cả ngày Thứ Sáu 20/11/2026 (không giờ); gõ "Nộp đồ án
   20/11/2027" thì hạn 20/11/2027.
7. **Given** gõ "Ôn từ vựng hằng ngày 21h", **Then** xem trước có "Lặp: hằng ngày"; task tạo ra lặp hằng
   ngày, hạn 21:00 hôm nay.
8. **Given** gõ "Họp lớp thứ 2 hàng tuần 7h", **Then** task lặp hằng tuần vào Thứ Hai, hạn 07:00 Thứ
   Hai 09/11.
9. **Given** gõ "Gọi chị Mai", **Then** "Mai" được tô sáng là "ngày mai"; bấm vào phần tô sáng thì phần
   đó hết tô sáng, xem trước không còn hạn, và Enter tạo task "Gọi chị Mai" không hạn (hoặc hạn theo
   danh sách đang xem như FR-017 của feature 002).
10. **Given** gõ "~", **Then** hiện danh sách gợi ý các danh sách hiện có, lọc dần theo chữ gõ tiếp
    (không phân biệt dấu); chọn bằng ↑/↓ và Enter/Tab. Tương tự "#" gợi ý nhãn hiện có.
11. **Given** gõ "Đọc sách #ThóiQuenMới" với nhãn chưa có, **Then** xem trước hiện "Nhãn mới:
    ThóiQuenMới"; Enter tạo task và tạo nhãn đó.
12. **Given** gõ "Viết báo cáo *", **Then** dấu * được tô sáng, xem trước có "★ Quan trọng"; task tạo ra
    là Quan trọng với tiêu đề "Viết báo cáo".
13. **Given** đang xem danh sách Ngày mai và gõ "Nộp bài thứ 6", **Then** hạn trong câu (Thứ Sáu)
    được dùng thay cho mặc định của danh sách đang xem. Gõ "Họp nhóm 9h" (chỉ có giờ) thì hạn 09:00
    ngày mai (giờ ghép với ngày của danh sách đang xem).
14. **Given** gõ "Học nhóm 3h", **Then** hạn 15:00 hôm nay (giờ 1–5 không kèm buổi là buổi chiều); gõ
    "Chạy bộ 5h sáng" thì hạn 05:00 ngày mai (05:00 hôm nay đã qua).
15. **Given** gõ "Làm bài tập !cao", **Then** "!cao" được tô sáng, xem trước có "Ưu tiên: Cao"; task tạo
    ra có ưu tiên Cao, tiêu đề "Làm bài tập". "!tb" đặt Trung bình, "!thấp" hoặc "!thap" đặt Thấp.

---

### User Story 5 - Tìm kiếm (Priority: P3)

Người dùng nhấn ⌘F (hoặc bấm ô tìm kiếm ở đầu cột danh sách) và gõ "nop bai". Ngay khi gõ, kết quả
hiện nhóm theo loại: Công việc, Môn học, Buổi học, Buổi thi; chữ khớp được tô sáng ("**Nộp bài**
QTDA"). Kết quả gồm cả danh sách và nhãn có tên khớp. Bấm vào một kết quả để mở chi tiết của nó (với
danh sách và nhãn: mở danh sách task lọc theo danh sách / nhãn đó).

**Why this priority**: Hữu ích khi dữ liệu nhiều, nhưng duyệt danh sách và lịch hiện vẫn đủ dùng.

**Independent Test**: Tạo task "Nộp bài QTDA" có ghi chú "gửi qua email thầy", nhấn ⌘F, gõ "nop bai"
rồi "email thay", kiểm tra task xuất hiện với phần khớp được tô sáng; bấm vào kết quả và kiểm tra bảng
chi tiết task mở ra.

**Acceptance Scenarios**:

1. **Given** có task "Nộp bài QTDA", **When** gõ "nop bai", "NỘP BÀI" hoặc "Nop Bai", **Then** task
   xuất hiện trong nhóm Công việc với "Nộp bài" được tô sáng.
2. **Given** ghi chú task chứa "gửi qua email thầy", **When** gõ "email thay", **Then** task xuất hiện,
   dưới tiêu đề hiện đoạn ghi chú quanh chỗ khớp với chữ khớp được tô sáng.
3. **Given** môn "Quản trị dự án" (mã QTDA), **When** gõ "quan tri", **Then** nhóm Môn học có môn này;
   nhóm Buổi học có các buổi của môn, buổi sắp tới trước; nhóm Buổi thi có buổi thi của môn (nếu có).
4. **Given** task đã hoàn thành "Nộp bài tuần 1", **Then** mặc định không có trong kết quả; bật tuỳ chọn
   "Gồm cả đã hoàn thành" thì xuất hiện, hiện mờ có dấu đã xong.
5. **Given** bấm vào kết quả là task / môn học / buổi học / buổi thi, **Then** mở lần lượt bảng chi tiết
   task / trang môn học tại môn đó / chi tiết buổi học / chi tiết buổi thi.
6. **Given** không có kết quả, **Then** hiện "Không tìm thấy kết quả cho “…”".
7. **Given** đang tìm, **When** nhấn Esc, **Then** xoá ô tìm và trở lại màn hình trước đó.
8. **Given** task ở Thùng rác khớp từ khoá, **Then** không có trong kết quả.
9. **Given** có nhãn "Gấp" và danh sách "📚 Học tập", **When** gõ "gap" hoặc "hoc tap", **Then** nhóm Nhãn
   có "Gấp" / nhóm Danh sách có "Học tập" (kèm số task chưa xong); bấm vào thì mục Công việc mở nhãn /
   danh sách đó với task được lọc theo nhãn / danh sách.

---

### Edge Cases

**Sao lưu**

- iCloud Drive chưa bật hoặc chưa đăng nhập iCloud: thư mục mặc định không có → xử lý như thư mục đích
  không có (bỏ qua, cảnh báo nhẹ, thử lại), Cài đặt gợi ý bật iCloud Drive hoặc chọn thư mục khác.
- Phần lưu trữ dữ liệu không chạy đúng giờ sao lưu: bỏ qua, sao lưu bù khi phần lưu trữ
  chạy lại.
- App bị tắt đột ngột hoặc Mac mất điện giữa lúc sao lưu: bản dở dang không bao giờ xuất hiện trong
  danh sách hay bị tính là bản hợp lệ; lần sao lưu đó được coi là thất bại và được thử lại.
- Thư mục đích hết dung lượng hoặc không có quyền ghi: sao lưu thất bại có báo lỗi; không xoá bản cũ.
- Hai lần sao lưu chồng nhau (tự động trùng lúc bấm "Sao lưu ngay"): chỉ chạy một lần, lần còn lại chờ
  hoặc bỏ qua; không tạo bản hỏng.
- Người dùng tự bỏ file lạ vào thư mục đích: app không xoá file không phải do nó tạo.
- Đổi thư mục đích: các bản ở thư mục cũ không bị di chuyển hay xoá; danh sách Khôi phục chỉ hiện bản ở
  thư mục hiện tại; Cài đặt có nút "Chọn bản sao lưu khác…" để khôi phục từ file bất kỳ.
- iCloud chưa tải xong file sao lưu về máy (chỉ có bản trên mây): khi khôi phục, app chờ tải và báo
  "Đang tải bản sao lưu từ iCloud…"; tải thất bại thì báo lỗi, không khôi phục.
- Bản sao lưu từ phiên bản app cũ hơn: khôi phục được và dữ liệu được nâng cấp theo phiên bản hiện tại;
  nâng cấp lỗi thì app tự đưa dữ liệu về bản "Trước khi khôi phục" và báo "Không nâng cấp được dữ liệu
  của bản sao lưu cũ; dữ liệu đã được đưa về như trước khi khôi phục."
  Bản từ phiên bản mới hơn app đang chạy: từ chối với thông báo rõ ràng.
- Đồng hồ máy bị chỉnh lùi: không tạo bản trùng tên đè lên bản cũ.

**Thêm nhanh bằng câu**

- Câu chỉ có phần được hiểu (ví dụ "mai 9h"): tiêu đề trống → không tạo task, xem trước báo "Thiếu tên
  công việc".
- Nhiều cụm ngày trong câu ("mai … thứ 6"): chỉ cụm đầu tiên được hiểu; cụm sau giữ là chữ.
- Ngày không hợp lệ ("31/2", "32/11"): không được hiểu, giữ là chữ.
- Ngày dạng 20/11 không kèm năm đã qua trong năm nay (ví dụ "02/11"): hiểu là năm sau (02/11/2027).
- "thứ 5" khi hôm nay là Thứ Năm: là hôm nay nếu không có giờ hoặc giờ chưa qua; nếu giờ đã qua thì là
  Thứ Năm tuần sau.
- "9h" khi đang 10:00 và không có ngày: hiểu là ngày mai 09:00. "9h" kèm ngày đã có thì dùng ngày đó.
- Giờ không hợp lệ ("25h", "9h75"): không được hiểu.
- Chữ trong từ khác không bị hiểu nhầm: "maintain", "Tháng 9h" (không có khoảng cách hợp lệ), "Lab 3",
  "CN" chỉ được hiểu khi là một từ riêng đứng độc lập.
- "#" hoặc "~" đứng một mình hoặc "~Tên danh sách không có": không được hiểu, giữ là chữ (danh sách
  không tự tạo mới).
- Nhãn hoặc danh sách có dấu cách: chọn qua gợi ý tự hoàn thành thì được hiểu nguyên tên.
- Hạn hiểu được nằm trong quá khứ (ví dụ "hôm nay 7h" lúc 10:00): vẫn tạo với hạn đó; xem trước hiện
  hạn màu đỏ "đã qua".
- Dán (⌘V) một câu vào ô: được hiểu như khi gõ.
- Phần đã huỷ hiểu giữ trạng thái huỷ cho đến khi người dùng sửa chính phần chữ đó.

**Task lặp lại**

- Task lặp không có hạn: khi đặt lặp, hạn mặc định là hôm nay (theo quy tắc lặp, ngày khớp gần nhất
  từ hôm nay), không giờ.
- Task deadline tự tạo (từ buổi học) không được đặt lặp; tuỳ chọn "Lặp lại" bị ẩn.
- Kéo thả lần hiện tại trên lịch sang ngày khác: hỏi "Chỉ lần này" hay "Lần này và các lần sau". Khối
  dự kiến không kéo được.
- Khôi phục từ Thùng rác một lần đã xoá "Chỉ lần này": lần đó trở lại như task thường độc lập (không
  lặp), chuỗi lặp không bị ảnh hưởng.
- Khôi phục một chuỗi đã xoá "Lần này và các lần sau": chuỗi lặp tiếp tục từ lần đã xoá.
- Hoàn thành lần cuối của chuỗi (đã đến ngày kết thúc hoặc đủ N lần): chuỗi kết thúc, không có lần
  mới; bảng chi tiết của lần đó hiện "Đã kết thúc lặp".
- Đổi quy tắc lặp ("Lần này và các lần sau"): lần hiện tại giữ hạn đang có; các lần dự kiến tính lại
  theo quy tắc mới.
- Bỏ lặp: task trở thành task thường với hạn hiện tại.
- Lặp hằng tuần không chọn thứ nào: không cho lưu, báo lỗi dưới ô.
- Hoàn thành nhiều lần liên tiếp nhanh (bấm checkbox lần mới vừa hiện): mỗi lần hoàn thành tạo đúng
  một lần kế tiếp, không trùng lặp.

**Tìm kiếm**

- Từ khoá chỉ gồm khoảng trắng: không tìm, không hiện kết quả.
- Nhiều từ ("nop qtda"): kết quả phải chứa tất cả các từ (ở bất kỳ vị trí nào trong các trường được
  tìm của cùng một mục).
- Kết quả nhiều: mỗi nhóm hiện tối đa 20 mục kèm "Xem thêm (n)".
- Chữ "đ"/"Đ" khớp với "d"/"D" (gõ "do an" tìm được "Đồ án").
- Task lặp chỉ hiện lần hiện tại (không hiện các lần dự kiến).
- Dữ liệu thay đổi trong lúc đang hiện kết quả (ví dụ hoàn thành task từ chi tiết): kết quả cập nhật.

## Requirements *(mandatory)*

### Functional Requirements

**Sao lưu tự động (US1)**

- **FR-001**: App PHẢI tự sao lưu toàn bộ dữ liệu (mọi task kể cả Thùng rác và đã hoàn thành, danh
  sách, nhãn, học kỳ, ca học, môn học, buổi học và các ngoại lệ, buổi thi, cài đặt của app) mỗi ngày
  một lần vào giờ người dùng đặt (mặc định 21:00). Khôi phục một bản PHẢI đưa toàn bộ các dữ liệu này
  về đúng trạng thái lúc sao lưu.
- **FR-002**: Sao lưu tự động PHẢI chạy khi Mac đang thức và phần lưu trữ dữ liệu đang chạy, kể cả khi
  cửa sổ app đã đóng hoặc app đã thoát (giống trình đồng bộ Lịch/Lời nhắc).
- **FR-003**: Nếu đến giờ sao lưu mà không sao lưu được (Mac tắt, ngủ, phần lưu trữ chưa chạy, thư mục
  đích không có, lỗi), app PHẢI thử lại và tạo một bản sao lưu bù trong vòng 5 phút sau khi điều kiện
  cho phép trở lại; dù lỡ nhiều ngày cũng chỉ tạo một bản bù.
- **FR-004**: Thư mục đích mặc định là `iCloud Drive/Lịch Học Cá Nhân/Sao lưu` (app tự tạo thư mục nếu
  iCloud Drive có sẵn). Người dùng PHẢI chọn được thư mục khác bằng hộp chọn thư mục của macOS (ví dụ
  trên ổ SSD rời) và trở lại thư mục mặc định bằng nút "Dùng thư mục mặc định".
- **FR-005**: Mỗi bản sao lưu là một file riêng, tên chứa ngày giờ tạo (ví dụ
  `LichHoc-2026-11-05-2100.backup`) và loại bản; một bản chỉ được coi là hợp lệ khi đã ghi xong và
  kiểm tra đọc lại được — bản dở dang không bao giờ xuất hiện như bản hợp lệ. Bản sao lưu không mã hoá và
  khôi phục không cần mật khẩu.
- **FR-006**: App PHẢI giữ N bản gần nhất (mặc định 14, chỉnh được từ 1 đến 365) và tự xoá bản cũ hơn,
  chỉ sau khi bản mới đã tạo thành công; app chỉ được xoá file sao lưu do chính nó tạo trong thư mục
  đích hiện tại. Bản đang được chọn để khôi phục KHÔNG BAO GIỜ bị xoá trong lúc khôi phục (kể cả khi
  bản "Trước khi khôi phục" vừa tạo làm số bản vượt giới hạn); việc dọn bản thừa khi đó chờ đến sau khi
  khôi phục xong.
- **FR-007**: Khi thư mục đích không có hoặc không ghi được, app PHẢI bỏ qua lần sao lưu đó mà không
  treo, không hiện hộp thoại chặn và không ảnh hưởng chức năng khác; hiện cảnh báo nhẹ (không chặn)
  trong Cài đặt và một chấm cảnh báo trên biểu tượng Cài đặt ở thanh biểu tượng, rồi thử lại theo
  FR-003.
- **FR-008**: Khi sao lưu tự động đang bật mà đã quá 3 ngày không có bản sao lưu thành công, app PHẢI
  (a) cảnh báo nhẹ (chấm cảnh báo + dòng trong Cài đặt) và (b) gửi đúng một thông báo macOS bằng tiếng
  Việt, kể cả khi cửa sổ app đang đóng, ví dụ "Đã 3 ngày chưa sao lưu được dữ liệu. Mở Cài đặt → Sao
  lưu để kiểm tra."; bấm vào thông báo mở Cài đặt → Sao lưu. Không gửi lại cho đến khi có một bản sao
  lưu thành công (sau đó bộ đếm bắt đầu lại). Mỗi lần thất bại lẻ chỉ cảnh báo nhẹ trong app, không gửi
  thông báo macOS.
- **FR-009**: Cài đặt PHẢI có mục "Sao lưu" gồm: công tắc bật/tắt sao lưu tự động (mặc định bật), giờ
  sao lưu, thư mục đích (đường dẫn dễ đọc + nút "Chọn thư mục…" + "Mở trong Finder"), số bản giữ lại,
  trạng thái lần gần nhất (thời gian, dung lượng, Thành công/Thất bại kèm lý do tiếng Việt và cách
  khắc phục), lần thành công gần nhất (nếu lần gần nhất thất bại), nút "Sao lưu ngay", và danh sách
  bản sao lưu.
- **FR-010**: "Sao lưu ngay" PHẢI tạo một bản sao lưu loại "Thủ công" ngay lập tức, hiện tiến trình
  và kết quả; app vẫn dùng được trong lúc sao lưu. Không chạy hai lần sao lưu cùng lúc.

**Khôi phục (US2)**

- **FR-010a**: Mỗi lần sao lưu, khôi phục và xoá bản cũ (bắt đầu, kết thúc, kết quả, dung lượng, lý do
  lỗi, thư mục đích) PHẢI được ghi vào file log hiện có của trình đồng bộ chạy nền (cùng file với các
  hoạt động nền khác, vị trí đã ghi trong README); log không chứa nội dung dữ liệu của người dùng.
- **FR-011**: Danh sách bản sao lưu PHẢI hiện các bản hợp lệ trong thư mục đích hiện tại, mới nhất ở
  trên, mỗi bản có ngày giờ (định dạng Việt Nam), dung lượng, loại (Tự động / Thủ công / Trước khi
  khôi phục) và nút "Khôi phục". Có thêm "Chọn bản sao lưu khác…" để khôi phục từ một file bất kỳ.
- **FR-012**: Khôi phục PHẢI: (a) hỏi xác nhận nêu rõ thời điểm của bản và việc dữ liệu hiện tại sẽ bị
  thay; (b) tạo bản "Trước khi khôi phục" của dữ liệu hiện tại — nếu không tạo được thì dừng, không
  khôi phục; (c) kiểm tra bản được chọn đọc được và tương thích — nếu không thì dừng, báo lỗi; (d) thay
  toàn bộ dữ liệu một cách trọn vẹn (thành công hoàn toàn hoặc giữ nguyên dữ liệu cũ, không bao giờ
  nửa vời), kể cả bước nâng cấp dữ liệu của bản cũ: nâng cấp lỗi thì app tự đưa dữ liệu về bản "Trước
  khi khôi phục" và báo lỗi; (e) làm mới mọi màn hình và thông báo kết quả.
- **FR-013**: Sau khi khôi phục, nếu đồng bộ Lịch và Lời nhắc đang bật, các mục do app ghi trong Lịch
  và Lời nhắc PHẢI được cập nhật khớp với dữ liệu đã khôi phục trong vòng 1 phút; lịch nhắc trên máy
  cũng được tính lại.

**Constitution (US1)**

- **FR-014**: Constitution PHẢI được sửa đổi (bản MINOR) trước khi triển khai, thêm ngoại lệ thứ hai ở
  Nguyên tắc IV: app được phép ghi file sao lưu đầy đủ dữ liệu vào thư mục người dùng chọn, kể cả
  thư mục trong iCloud Drive của chính người dùng; việc đồng bộ lên iCloud do macOS đảm nhiệm, app
  không tự kết nối ra ngoài máy; sao lưu tắt được bất kỳ lúc nào; dữ liệu gốc vẫn lưu và xử lý trên
  máy. Ngoài thư mục sao lưu do app quản lý, app chỉ được ĐỌC một file sao lưu khi người dùng chủ động
  chọn file đó để khôi phục ("Chọn bản sao lưu khác…", ví dụ sau khi cài lại máy); app không tự đọc, sửa
  hay xoá file nào ngoài thư mục sao lưu của nó (constitution 2.3.1).

**Task lặp lại (US3)**

- **FR-015**: Bảng chi tiết task PHẢI có trường "Lặp lại" với các kiểu: Không lặp (mặc định), Hằng
  ngày, Mỗi N ngày (N từ 2 đến 365), Hằng tuần (chọn một hoặc nhiều thứ từ T2 đến CN, mặc định là thứ
  của hạn), Hằng tháng (vào ngày D trong tháng, mặc định là ngày của hạn); và kết thúc: Không kết thúc
  (mặc định), Vào ngày (chọn ngày), Sau N lần (N từ 1 đến 999, tính cả lần đầu).
- **FR-016**: Một chuỗi lặp tại mỗi thời điểm có đúng một **lần hiện tại** là task thật (có checkbox,
  sửa được, có nhắc); các lần sau là **lần dự kiến**, chỉ suy ra từ quy tắc để hiển thị.
- **FR-017**: Hoàn thành lần hiện tại PHẢI đưa lần đó vào Đã hoàn thành và tạo lần kế tiếp có hạn là
  ngày khớp quy tắc đầu tiên sau hạn của lần vừa xong và không sớm hơn hôm nay (không sinh các lần đã
  lỡ); giữ nguyên giờ hạn, mọi trường khác của task và khung giờ làm (dời theo ngày mới). Nếu chuỗi đã
  kết thúc (quá ngày kết thúc hoặc đủ N lần) thì không tạo lần mới.
- **FR-018**: Hằng tháng vào ngày D mà tháng không có ngày D thì rơi vào ngày cuối tháng đó.
- **FR-019**: Bỏ hoàn thành lần vừa xong PHẢI gỡ lần kế tiếp đã được tạo từ nó nếu lần kế tiếp chưa bị
  sửa; nếu đã bị sửa thì giữ cả hai.
- **FR-020**: Sửa bất kỳ trường nào của một task lặp (kể cả kéo thả trên lịch) hoặc xoá task lặp PHẢI
  hỏi "Chỉ lần này" hay "Lần này và các lần sau" (có nút Huỷ). "Chỉ lần này": thay đổi chỉ áp dụng cho
  lần hiện tại (xoá thì lần hiện tại vào Thùng rác, lần kế tiếp xuất hiện). "Lần này và các lần sau":
  thay đổi áp dụng cho lần hiện tại và mọi lần sau (xoá thì task vào Thùng rác và chuỗi dừng). Sửa
  riêng trường "Lặp lại" luôn áp dụng cho cả chuỗi và không hỏi.
- **FR-020a**: Đổi ngày hạn với "Lần này và các lần sau" (trong bảng chi tiết hoặc kéo thả) PHẢI dời
  quy tắc lặp theo ngày mới: hằng ngày / mỗi N ngày đếm lại từ ngày mới; hằng tuần thay thứ của lần
  hiện tại bằng thứ mới (T2+T5, dời lần Thứ Hai sang Thứ Ba → T3+T5; nếu thứ mới đã có trong quy tắc
  thì chỉ bỏ thứ cũ); hằng tháng đổi ngày D thành ngày của hạn mới. Đổi giờ hạn thì mọi lần sau dùng
  giờ mới. Kiểu kết thúc và số lần đã tạo giữ nguyên.
- **FR-021**: Danh sách thông minh, nhóm task, số đếm và tìm kiếm chỉ tính **lần hiện tại** của task
  lặp. Dòng task lặp có biểu tượng lặp; rê chuột hiện mô tả quy tắc bằng tiếng Việt (ví dụ "Lặp hằng
  tuần vào Thứ Hai, Thứ Năm · đến 30/11/2026").
- **FR-022**: Trang Lịch PHẢI hiện lần hiện tại như task thường và các lần dự kiến trong khoảng đang xem
  dưới dạng khối mờ có biểu tượng lặp; khối dự kiến không có checkbox, không kéo được, bấm vào thì mở
  chi tiết lần hiện tại của chuỗi.
- **FR-023**: Bản tóm tắt hằng ngày (kể cả các bản đã tạo sẵn cho nhiều ngày tới) PHẢI gồm lần hiện tại
  và lần dự kiến rơi vào ngày đó, và tự cập nhật khi chuỗi thay đổi.
- **FR-024**: Nhắc lịch trên máy và đồng bộ Lời nhắc/iPhone áp dụng cho lần hiện tại như một task
  thường (cùng các mốc nhắc, kể cả mốc của Quan trọng); khi lần kế tiếp xuất hiện, Lời nhắc PHẢI cập
  nhật trong vòng 1 phút. Chỉ ghi các thông tin tối thiểu như constitution IV quy định.
- **FR-025**: Task deadline tự tạo không được đặt lặp. Khôi phục từ Thùng rác: lần xoá "Chỉ lần này"
  trở lại thành task thường không lặp; task xoá "Lần này và các lần sau" trở lại cùng chuỗi lặp.

**Thêm nhanh bằng câu tiếng Việt (US4)**

- **FR-026**: Ô "Thêm công việc" (kể cả khi mở bằng ⌘N) PHẢI hiểu ngày giờ, nhãn, danh sách, Quan trọng,
  mức ưu tiên và lặp lại từ câu gõ; mọi xử lý chạy hoàn toàn trên máy, không dùng AI hay internet.
- **FR-027**: Các cụm được hiểu (không phân biệt hoa thường; chấp nhận cả khi gõ không dấu, ví dụ "thu
  6", "ngay mai", "hang tuan"):
  - Ngày: "hôm nay"/"hnay"; "mai"/"ngày mai"; "mốt"/"ngày mốt"/"ngày kia"; "thứ 2"…"thứ 7" (cả "thứ
    hai"…"thứ bảy", "T2"…"T7"); "chủ nhật"/"CN"; "tuần sau" (= Thứ Hai tuần sau); "thứ X tuần sau"/"CN
    tuần sau" (= thứ X của tuần lịch kế tiếp, tuần bắt đầu Thứ Hai; "tuần tới" cùng nghĩa "tuần sau");
    "DD/MM" và "DD/MM/YYYY" (cả D/M; chỉ dấu "/" — "3-4" trong "Lab 3-4" KHÔNG phải ngày).
  - Giờ: "9h", "9h30", "9g", "9g30", "9:30", "21:00", "9 giờ", "9 giờ 30", "9 giờ 30 phút", "9 rưỡi"/"9h
    rưỡi" (= 9:30); kèm buổi "sáng", "trưa", "chiều", "tối", "đêm" (ví dụ "9 giờ tối", "3h chiều", "tối
    nay"). Buổi đứng một mình là giờ mặc định: sáng 08:00, trưa 12:00, chiều 14:00, tối 20:00, đêm 22:00.
    "chiều"/"tối" cộng 12 giờ cho giờ 1–11; "trưa" cộng 12 cho giờ 1–2; "đêm" cộng 12 cho giờ 9–11,
    "12h đêm" là 00:00 hôm sau, "đêm" với giờ 1–5 giữ nguyên ("2h đêm" là 02:00); "12h sáng" không
    hợp lệ (giữ là chữ). Giờ không
    kèm buổi: giờ 1–5 (kể cả có phút, ví dụ "3h", "2h30", "5:15") hiểu là buổi chiều 13:00–17:59; giờ 0
    và từ 6 trở lên giữ nguyên theo 24 giờ ("8h" là 08:00, "21:00" là 21:00). Muốn giờ 1–5 buổi sáng
    thì gõ kèm "sáng" ("5h sáng" là 05:00).
  - Nhãn: "#tên" (tên viết liền, hoặc chọn từ gợi ý để có dấu cách); có thể nhiều nhãn.
  - Danh sách: "~tên" — chỉ được hiểu khi khớp một danh sách đã có (so khớp không phân biệt dấu, hoa
    thường); một danh sách.
  - Quan trọng: "*" đứng riêng hoặc từ "quan trọng".
  - Ưu tiên: "!cao" → Cao, "!tb" → Trung bình, "!thấp" (cả "!thap") → Thấp. "!" đứng một mình hoặc kèm
    chữ khác ("!gấp") không được hiểu, giữ là chữ.
  - Lặp: "hằng ngày"/"hàng ngày"/"mỗi ngày"; "mỗi N ngày"; "hằng tuần"/"hàng tuần"/"mỗi tuần" (theo thứ
    của hạn, hoặc của hôm nay nếu không có hạn); "thứ X hằng tuần"/"thứ X hàng tuần"/"mỗi thứ X" (cả
    nhiều thứ, ví dụ "thứ 2 và thứ 5 hàng tuần"); "hằng tháng"/"hàng tháng"/"mỗi tháng" (theo ngày của
    hạn); "ngày D hằng tháng".
- **FR-028**: Quy tắc suy ra hạn:
  - "thứ X" = ngày thứ X gần nhất từ hôm nay trở đi; nếu là hôm nay mà giờ đã qua thì là tuần sau.
  - Chỉ có ngày, không giờ → hạn cả ngày (không giờ). Chỉ có giờ, không ngày → nếu danh sách đang xem
    có ngày mặc định (feature 002 FR-017: Hôm nay, Ngày mai, 7 ngày tới) thì ghép giờ với ngày đó, kể cả
    khi giờ đã qua (ở Ngày mai: "Họp nhóm 9h" → 09:00 ngày mai; ở Hôm nay lúc 10:00: "Mua sữa 8h" →
    08:00 hôm nay, hiện "đã qua"); nếu không (Tất cả, danh sách của người dùng, nhãn) thì hôm nay nếu
    giờ chưa qua, nếu đã qua thì ngày mai.
  - "DD/MM" không năm → năm nay, hoặc năm sau nếu ngày đó đã qua.
  - Cụm lặp không có ngày → lần đầu là ngày khớp quy tắc gần nhất từ hôm nay (theo cùng quy tắc giờ).
  - Mỗi loại chỉ hiểu cụm đầu tiên (một ngày, một giờ, một danh sách, một mức ưu tiên, một quy tắc lặp); cụm cùng loại
    xuất hiện sau giữ nguyên là chữ.
- **FR-029**: Cụm chỉ được hiểu khi đứng thành từ riêng (ngăn cách bằng khoảng trắng, đầu/cuối câu
  hoặc dấu câu); không hiểu phần nằm bên trong một từ khác.
- **FR-030**: Ngay khi gõ (không quá 0,1 giây sau mỗi phím), các cụm được hiểu PHẢI được tô sáng trong ô
  và dưới ô hiện dòng xem trước gồm những gì sẽ được đặt: "Hạn: 09:00 Thứ Sáu, 06/11", "Lặp: hằng tuần
  vào Thứ Hai", "Danh sách: 📚 Học tập", "Nhãn: Gấp" (hoặc "Nhãn mới: …"), "★ Quan trọng", "Ưu tiên: Cao", và tiêu đề
  sẽ tạo. Bảng ví dụ bắt buộc phải đúng (hôm nay Thứ Năm 05/11/2026, 10:00, đang xem danh sách Tất cả):

  | Gõ | Tiêu đề | Kết quả |
  |----|---------|---------|
  | Nộp bài QTDA thứ 6 9h #Gấp | Nộp bài QTDA | hạn 09:00 06/11, nhãn Gấp |
  | Họp nhóm mai 14h ~Cá nhân | Họp nhóm | hạn 14:00 06/11, danh sách Cá nhân |
  | Đi khám mốt 9 giờ sáng | Đi khám | hạn 09:00 07/11 |
  | Thi thử thứ 6 tuần sau 21:00 quan trọng | Thi thử | hạn 21:00 13/11, Quan trọng |
  | Gọi điện về nhà 9 giờ tối | Gọi điện về nhà | hạn 21:00 05/11 |
  | Mua sữa 8h | Mua sữa | hạn 08:00 06/11 |
  | Nộp đồ án 20/11 | Nộp đồ án | hạn cả ngày 20/11/2026 |
  | Báo cáo tuần sau | Báo cáo | hạn cả ngày Thứ Hai 09/11 |
  | Ôn từ vựng hằng ngày 21h | Ôn từ vựng | lặp hằng ngày, hạn 21:00 05/11 |
  | Họp lớp thứ 2 hàng tuần 7h | Họp lớp | lặp hằng tuần T2, hạn 07:00 09/11 |
  | Viết báo cáo * | Viết báo cáo | Quan trọng |
  | Học nhóm CN chiều | Học nhóm | hạn 14:00 Chủ Nhật 08/11 |
  | Học nhóm 3h | Học nhóm | hạn 15:00 05/11 |
  | Gọi mẹ mai 2h30 | Gọi mẹ | hạn 14:30 06/11 |
  | Chạy bộ 5h sáng | Chạy bộ | hạn 05:00 06/11 |
  | Ôn thi thứ 7 12h | Ôn thi | hạn 12:00 07/11 |
  | Làm bài tập !cao | Làm bài tập | ưu tiên Cao |
  | Dọn phòng CN 9h !thấp | Dọn phòng | hạn 09:00 08/11, ưu tiên Thấp |

- **FR-031**: Bấm vào một cụm đang tô sáng PHẢI huỷ hiểu cụm đó: cụm hết tô sáng, giữ nguyên là chữ
  trong tiêu đề, xem trước cập nhật ngay. Trạng thái huỷ giữ cho đến khi người dùng sửa chính cụm đó.
- **FR-032**: Khi nhấn Enter, task được tạo với tiêu đề là câu đã bỏ các cụm được hiểu (gộp khoảng
  trắng thừa, bỏ dấu câu thừa ở đầu/cuối), cùng các giá trị đã hiểu; tiêu đề rỗng thì không tạo và xem
  trước báo "Thiếu tên công việc".
- **FR-033**: Giá trị hiểu được từ câu PHẢI được ưu tiên hơn giá trị mặc định theo danh sách đang xem
  (feature 002 FR-017); trường nào câu không nói thì dùng mặc định như cũ (câu chỉ có giờ thì giờ ghép
  với ngày mặc định của danh sách, xem FR-028). Nhãn hiểu được cộng thêm vào
  nhãn mặc định của danh sách nhãn đang xem.
- **FR-034**: Gõ "#" hoặc "~" PHẢI mở gợi ý tự hoàn thành (nhãn / danh sách hiện có, kèm màu hoặc
  emoji), lọc theo chữ gõ tiếp không phân biệt dấu và hoa thường; chọn bằng ↑/↓ + Enter/Tab hoặc bấm
  chuột; Esc đóng gợi ý mà không xoá chữ. Khi gợi ý đang mở, Enter chọn gợi ý chứ không tạo task.
- **FR-035**: "#tên" chưa có nhãn nào khớp PHẢI tạo nhãn mới (màu mặc định) khi tạo task; "~tên" không
  khớp danh sách nào thì không được hiểu (giữ là chữ).

**Tìm kiếm (US5)**

- **FR-036**: Đầu cột danh sách (mục Công việc) PHẢI có ô tìm kiếm; ⌘F ở mọi nơi trong app PHẢI chuyển
  đến mục Công việc và đặt con trỏ vào ô tìm. ⌘F được thêm vào bảng phím tắt (⌘/).
- **FR-037**: Tìm kiếm PHẢI tìm trong: task (tiêu đề, ghi chú), danh sách của người dùng (tên), nhãn
  (tên), môn học (tên, mã lớp học phần, giảng viên), buổi học (tên môn, mã lớp học phần của môn, phòng)
  và buổi thi (tên học phần, mã học phần, phòng). Không tìm trong task ở Thùng rác và không tìm trong
  lần dự kiến của task lặp. (Buổi học và buổi thi không có trường ghi chú.)
- **FR-038**: So khớp PHẢI không phân biệt hoa thường và dấu tiếng Việt (kể cả đ/d); nhiều từ thì mục
  phải chứa đủ mọi từ.
- **FR-039**: Kết quả PHẢI hiện ngay khi gõ (không cần Enter) trong khu vực chính, nhóm theo thứ tự:
  Công việc, Danh sách, Nhãn, Môn học, Buổi học, Buổi thi; mỗi nhóm có tên và số kết quả, nhóm trống không hiện, mỗi nhóm
  tối đa 20 mục kèm "Xem thêm (n)". Mỗi mục hiện thông tin nhận diện (task: tiêu đề, danh sách, hạn;
  danh sách: emoji, tên, số task chưa xong; nhãn: chấm màu, tên, số task chưa xong; buổi học/thi: môn,
  ngày giờ, phòng) và đoạn trích quanh chỗ khớp nếu khớp ở ghi chú; chữ khớp được tô
  sáng.
- **FR-040**: Thứ tự trong nhóm: Công việc theo hạn gần nhất (task không hạn ở cuối); Buổi học và Buổi
  thi sắp tới trước (gần nhất trước), rồi đến buổi đã qua (gần nhất trước); Danh sách, Nhãn và Môn học theo tên.
- **FR-041**: Có tuỳ chọn "Gồm cả đã hoàn thành" (mặc định tắt); khi bật, task đã hoàn thành xuất hiện
  với dạng mờ có dấu đã xong.
- **FR-042**: Bấm vào kết quả (hoặc chọn bằng ↑/↓ và Enter) PHẢI mở chi tiết: task → bảng chi tiết task;
  danh sách → mục Công việc mở danh sách đó (task lọc theo danh sách); nhãn → mục Công việc mở nhãn đó
  (task lọc theo nhãn); môn học → trang Môn học tại môn đó; buổi học → chi tiết buổi học; buổi thi → chi tiết buổi thi. Ô tìm
  giữ từ khoá để quay lại kết quả.
- **FR-043**: Esc trong ô tìm PHẢI xoá từ khoá và trở về màn hình trước khi tìm; không có kết quả thì
  hiện "Không tìm thấy kết quả cho “…”".

**Chung**

- **FR-044**: Mọi chức năng của feature 001 và 002 PHẢI giữ nguyên hành vi; các kịch bản kiểm chứng của
  hai feature vẫn pass.
- **FR-045**: Mọi chữ mới PHẢI bằng tiếng Việt, ngày giờ theo định dạng Việt Nam, giao diện theo phong
  cách feature 002 (cả chế độ sáng và tối).
- **FR-046**: Ngoài việc ghi file sao lưu vào thư mục người dùng chọn (FR-014), app KHÔNG tạo kết nối
  ra ngoài máy.

### Key Entities

- **Cài đặt sao lưu** (lưu trên máy): bật/tắt, giờ sao lưu, thư mục đích, số bản giữ lại; trạng thái
  lần gần nhất (thời điểm, kết quả, dung lượng, lý do lỗi) và lần thành công gần nhất.
- **Bản sao lưu** (file trong thư mục đích): thời điểm tạo, loại (Tự động / Thủ công / Trước khi khôi
  phục), dung lượng, phiên bản dữ liệu; chứa toàn bộ dữ liệu của app tại thời điểm đó.
- **Quy tắc lặp** (gắn với task): kiểu (hằng ngày / mỗi N ngày / hằng tuần với các thứ / hằng tháng vào
  ngày D), khoảng N, kiểu kết thúc (không / vào ngày / sau N lần), số lần đã tạo.
- **Task** (mở rộng): có thể có quy tắc lặp; thuộc một chuỗi lặp (các lần đã hoàn thành và lần hiện
  tại cùng chuỗi); có thể là lần đã tách khỏi chuỗi (sửa "Chỉ lần này").
- **Lần dự kiến** (suy ra, không lưu): ngày giờ các lần sau của chuỗi, dùng cho lịch và bản tóm tắt.
- **Kết quả hiểu câu** (tạm thời, không lưu): các cụm được hiểu kèm vị trí trong câu, giá trị (ngày
  giờ, nhãn, danh sách, Quan trọng, mức ưu tiên, quy tắc lặp), cụm đã bị huỷ hiểu, tiêu đề còn lại.
- **Kết quả tìm kiếm** (suy ra, không lưu): loại (task, danh sách, nhãn, môn học, buổi học, buổi thi), mục, trường khớp, vị trí khớp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mỗi bản bù được tạo trong vòng 5 phút sau khi Mac thức / phần lưu trữ chạy lại (kiểm bằng
  kịch bản gập máy); theo dõi tay trong 30 ngày dùng bình thường, 100% các ngày Mac được bật có một bản
  sao lưu thành công.
- **SC-002**: Khôi phục một bản sao lưu trả lại 100% dữ liệu (so sánh số lượng và nội dung task, danh
  sách, nhãn, môn học, buổi học, buổi thi, cài đặt) như lúc sao lưu; với dữ liệu một học kỳ đầy đủ,
  khôi phục xong trong dưới 1 phút.
- **SC-003**: Tháo ổ đích hoặc tắt iCloud Drive trong 7 ngày: 0 lần app treo, lỗi hay mất dữ liệu; cảnh
  báo hiện đúng; bản bù được tạo trong vòng 5 phút sau khi thư mục đích có lại.
- **SC-004**: 0 trường hợp bản sao lưu dở dang (do mất điện, tắt app giữa chừng) được hiện hoặc dùng như
  bản hợp lệ; số bản luôn không vượt quá giới hạn đã đặt (không tính file do người dùng tự đặt vào).
- **SC-005**: 100% câu trong bảng FR-030 và các kịch bản US4 cho đúng tiêu đề và giá trị; phần tô sáng
  và xem trước cập nhật trong dưới 0,1 giây sau mỗi phím.
- **SC-006**: Thêm task có hạn, nhãn và danh sách bằng một câu (ví dụ "Họp nhóm mai 14h ~Cá nhân #Gấp")
  mất dưới 10 giây, chỉ một lần nhấn Enter, không phải mở bảng chi tiết.
- **SC-007**: Với các kiểu lặp (hằng ngày, mỗi N ngày, hằng tuần nhiều thứ, hằng tháng kể cả ngày 31)
  và các kiểu kết thúc, 100% lần kế tiếp có đúng ngày giờ trong 12 tháng liên tiếp; lần kế tiếp có
  trong Lời nhắc trên iPhone trong vòng 1 phút sau khi hoàn thành (khi đồng bộ bật và có mạng).
- **SC-008**: Tìm kiếm trên dữ liệu 1.000 task và một học kỳ đầy đủ hiện kết quả trong dưới 0,3 giây
  sau mỗi phím; 100% mục có từ khoá (gõ có dấu hoặc không dấu, hoa hoặc thường) được tìm thấy.
- **SC-009**: 100% kịch bản kiểm chứng của feature 001 và 002 vẫn pass.
- **SC-010**: Khi tắt mạng, mọi chức năng của feature này vẫn hoạt động (sao lưu vào thư mục iCloud Drive
  vẫn ghi file trên máy; macOS tải lên khi có mạng); app không tạo kết nối ra ngoài máy.

## Assumptions

- Người dùng đã đăng nhập iCloud và bật iCloud Drive trên Mac; nếu không, người dùng chọn thư mục khác.
  Đồng bộ file sao lưu lên iCloud do macOS đảm nhiệm; app chỉ ghi file vào thư mục.
- File sao lưu không mã hoá (đã chốt ở Clarifications) vì nằm trong iCloud Drive hoặc ổ đĩa của chính
  người dùng; quên mật khẩu không thể làm mất bản sao lưu.
- Giờ sao lưu mặc định 21:00 (buổi tối, lúc Mac thường đang bật); nếu máy ngủ hoặc tắt thì cơ chế bù đảm bảo vẫn có bản
  sao lưu mỗi ngày dùng máy.
- Bản "Trước khi khôi phục" và bản "Thủ công" được tính vào số bản giữ lại như bản tự động (trừ ngoại lệ
  ở FR-006: bản đang khôi phục không bị dọn giữa chừng).
- Dữ liệu một học kỳ cỡ vài MB; 14 bản không chiếm đáng kể dung lượng iCloud.
- Ảnh nhập lịch không được lưu (feature 001 FR-035) nên không có trong bản sao lưu. Trạng thái cửa sổ
  (kích thước, vị trí, nhóm thu gọn) không cần sao lưu.
- Các script `backup.sh`/`restore.sh` hiện có vẫn giữ để dùng thủ công.
- Task lặp theo mô hình "một lần hiện tại": hoàn thành lần này mới có lần sau (như yêu cầu "hoàn thành
  một lần thì lần kế tiếp xuất hiện"); các lần sau chỉ hiện dạng dự kiến trên lịch và trong bản tóm
  tắt, không xuất hiện trong danh sách thông minh hay Lời nhắc trước khi đến lượt.
- Lặp hằng tháng chỉ theo ngày trong tháng (không có "Thứ Hai đầu tiên của tháng"); không có lặp hằng
  năm — nằm ngoài phạm vi.
- Mức ưu tiên chỉ đặt bằng "!cao", "!tb", "!thấp"; không hiểu các cách nói khác ("ưu tiên cao", "gấp").
  Khung giờ làm (bắt đầu–kết thúc) không được hiểu từ câu; giờ trong câu là giờ hạn.
- Hiểu câu chỉ áp dụng cho ô "Thêm công việc", không áp dụng khi sửa tiêu đề trong bảng chi tiết.
- Giờ 1–5 không kèm buổi hiểu là buổi chiều ("3h" là 15:00) vì sinh viên ít khi có việc lúc 1–5 giờ
  sáng; người dùng thấy ngay trong xem trước và thêm "sáng" nếu cần giờ sáng.
- Tìm kiếm không có toán tử nâng cao (dấu ngoặc kép, loại trừ từ, lọc theo trường) và không lưu lịch sử
  tìm kiếm.
- ⌘F hiện chưa dùng cho chức năng nào trong app nên không xung đột phím tắt.
