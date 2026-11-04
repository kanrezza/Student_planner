# Feature Specification: Thiết kế lại giao diện và đóng gói thành app macOS

**Feature Branch**: `002-redesign-macos-app`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Thiết kế lại giao diện và đóng gói thành app macOS cho Lịch Học Cá Nhân.
Bố cục 3 cột lấy cảm hứng từ các app quản lý công việc phổ biến (tên, logo, màu sắc là của riêng
app): (1) thanh biểu tượng hẹp bên trái chuyển giữa Công việc, Lịch, Môn học, Lịch thi, Cài đặt; (2)
cột danh sách gồm các danh sách thông minh Hôm nay, Ngày mai, 7 ngày tới, Tất cả (có số đếm), các
danh sách của người dùng (có emoji), nhãn, Đã hoàn thành, Thùng rác; (3) khu vực chính hiển thị task
nhóm theo Hôm nay / Ngày mai / 7 ngày tới, mỗi dòng có checkbox, tiêu đề, giờ ở bên phải, màu nhãn và
dấu Quan trọng; bấm vào task mở bảng chi tiết bên phải để sửa. Ô "Thêm công việc" nhanh ở đầu danh
sách, nhấn Enter là tạo. Thùng rác: task bị xoá vào Thùng rác và khôi phục được trong 30 ngày. Giao
diện gọn, nhiều khoảng trắng, bo góc mềm, hỗ trợ chế độ sáng/tối theo macOS, phím tắt cơ bản. Toàn
bộ tiếng Việt. Đóng gói thành app macOS có icon riêng trên Dock và cửa sổ riêng, không cần mở trình
duyệt. Mọi chức năng hiện có giữ nguyên. Trang Lịch dạng tuần (lấy cảm hứng bố cục từ ảnh tham
khảo): đầu trang có tên tháng/năm, nút +, chọn chế độ Ngày/Tuần/Tháng, nút trước/sau và "Hôm nay".
Tuần bắt đầu Thứ Hai. Ngày hôm nay có số ngày tô tròn nổi bật, có đường kẻ đỏ báo giờ hiện tại. Hàng
"Cả ngày" ở trên cùng cho task chỉ có ngày. Task có thể có khung giờ làm (bắt đầu–kết thúc, không bắt
buộc) bên cạnh hạn chót; task chỉ có hạn thì hiện thành khối ngắn tại giờ hạn. Mỗi mục là một khối
màu nhạt (màu theo nhãn hoặc môn học) có checkbox, tiêu đề và khung giờ; buổi học hiện thêm phòng
học; buổi thi nổi bật hơn hẳn; mục đã hoàn thành hoặc buổi đã huỷ thì mờ đi. Các mục trùng giờ xếp
cạnh nhau, không đè lên nhau. Kéo thả để đổi giờ task, kéo mép dưới để đổi thời lượng; kéo vào ô
trống để tạo task mới ở giờ đó. Buổi học kéo thả chỉ đổi riêng buổi đó, có hỏi xác nhận."

## Bối cảnh

Feature này thay giao diện của feature `001-task-class-scheduler` (đang dùng qua trình duyệt) bằng
một app macOS riêng với bố cục mới. Mọi dữ liệu, quy tắc nghiệp vụ và chức năng của feature 001
(task, danh sách, học kỳ, môn học, buổi học, ca học, nhãn, deadline tự tạo, nhắc lịch, đồng bộ Lịch
và Lời nhắc, thông báo tổng hợp, chế độ Quan trọng, và khi hoàn thành: nhập ảnh, lịch thi) được giữ
nguyên; feature này chỉ thêm: khung giờ làm của task, emoji cho danh sách, Thùng rác, kéo thả trên
lịch.

## Ảnh tham khảo bố cục

Người dùng cung cấp hai ảnh tham khảo (chỉ lấy bố cục; KHÔNG sao chép logo, tên hay màu thương
hiệu):

- **Màn hình danh sách**: thanh biểu tượng hẹp sát mép trái; cột danh sách với các danh sách thông
  minh ở trên (biểu tượng, tên, số đếm canh phải màu xám), tiêu đề nhỏ "Danh sách" rồi các danh sách
  có emoji, dưới cùng tách riêng "Đã hoàn thành" và "Thùng rác"; khu vực chính có tiêu đề lớn, ô "+
  Thêm công việc" nền xám nhạt bo tròn, các nhóm có mũi tên thu gọn, tên nhóm đậm kèm số lượng, mỗi
  dòng có checkbox vuông bo góc, tiêu đề, và giờ canh phải bằng màu nhấn; dòng đang rê chuột có nền
  nhạt bo tròn.
- **Màn hình lịch tuần**: đầu trang có nút ẩn/hiện cột bên, tên tháng/năm cỡ lớn, rồi bên phải là nút
  "+", nút chọn chế độ dạng menu, cụm nút trước/"Hôm nay"/sau; dưới là hàng tên thứ và hàng số ngày
  (ngày hôm nay là số trắng trong vòng tròn màu nhấn); một dải "Cả ngày" ngay dưới số ngày; cột giờ
  bên trái; đường kẻ đỏ ngang qua tuần tại giờ hiện tại kèm nhãn giờ màu đỏ ở cột giờ và chấm đỏ ở
  ngày hôm nay; mỗi mục là khối nền màu nhạt bo góc có checkbox, tiêu đề đậm và khung giờ "08:00–10:00"
  ở dòng dưới; mục đã hoàn thành có checkbox đã đánh dấu, chữ và nền mờ.

## Clarifications

### Session 2026-11-04

- Q: Buổi học có được dời sang ngày khác (học bù) không, hay chỉ đổi giờ trong cùng ngày? → A: Cho
  dời sang ngày khác sau khi xác nhận; buổi đó được đánh dấu "Đã dời" kèm ngày gốc (FR-028).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mở ứng dụng như một app macOS riêng (Priority: P1)

Người dùng mở "Lịch Học Cá Nhân" từ Dock, Launchpad hoặc Spotlight như mọi app khác. App có icon
riêng, cửa sổ riêng (không có thanh địa chỉ hay tab của trình duyệt), nhớ kích thước và vị trí cửa
sổ. Nếu phần lưu trữ dữ liệu trên máy chưa chạy, app tự khởi động nó và hiện màn hình chờ, rồi vào
thẳng màn hình chính.

**Why this priority**: Là nền cho mọi phần giao diện mới; người dùng muốn dùng hằng ngày như một app
bình thường thay vì mở trình duyệt và gõ địa chỉ.

**Independent Test**: Cài app, mở từ Dock khi phần lưu trữ đang tắt; kiểm tra app tự khởi động, hiện
màn hình chính với dữ liệu cũ còn nguyên, không có trình duyệt nào được mở.

**Acceptance Scenarios**:

1. **Given** app đã cài, **When** người dùng bấm icon trên Dock, **Then** app mở trong cửa sổ riêng
   với icon riêng trên Dock, không mở trình duyệt.
2. **Given** phần lưu trữ dữ liệu chưa chạy, **When** mở app, **Then** app hiện "Đang khởi động…",
   tự khởi động phần lưu trữ và vào màn hình chính khi sẵn sàng.
3. **Given** không khởi động được phần lưu trữ (ví dụ chưa cài môi trường chạy), **When** mở app,
   **Then** app hiện thông báo tiếng Việt nêu nguyên nhân và cách khắc phục, có nút "Thử lại".
4. **Given** người dùng đã đổi kích thước và vị trí cửa sổ, **When** mở lại app, **Then** cửa sổ
   về đúng kích thước và vị trí đó.
5. **Given** người dùng đóng cửa sổ hoặc thoát app, **Then** dữ liệu còn nguyên và việc đồng bộ
   Lịch/Lời nhắc sang iPhone vẫn tiếp tục.

---

### User Story 2 - Bố cục 3 cột và danh sách thông minh (Priority: P1)

Màn hình Công việc gồm 3 cột: thanh biểu tượng hẹp bên trái (Công việc, Lịch, Môn học, Lịch thi, Cài
đặt), cột danh sách (Hôm nay, Ngày mai, 7 ngày tới, Tất cả kèm số đếm; các danh sách của người dùng
có emoji; các nhãn; Đã hoàn thành; Thùng rác), và khu vực chính hiển thị task theo nhóm. Mỗi dòng
task có checkbox, tiêu đề, giờ hạn ở bên phải, chấm màu nhãn và dấu ★ nếu Quan trọng. Bấm vào task
mở bảng chi tiết bên phải để sửa mọi thông tin của task.

**Why this priority**: Đây là màn hình dùng nhiều nhất; tổ chức lại theo danh sách thông minh giúp
thấy ngay việc cần làm.

**Independent Test**: Có task hạn hôm nay, ngày mai, 5 ngày nữa, quá hạn và không có hạn; kiểm tra
số đếm và nội dung từng danh sách thông minh; mở và sửa một task trong bảng chi tiết.

**Acceptance Scenarios**:

1. **Given** có 2 task hạn hôm nay, 1 task quá hạn, 3 task hạn ngày mai, **When** mở app, **Then**
   màn hình mặc định là Công việc → Hôm nay, hiện nhóm "Quá hạn" và nhóm "Hôm nay"; số đếm cạnh Hôm
   nay là 3, cạnh Ngày mai là 3.
2. **Given** danh sách Hôm nay, **When** ngày hôm nay có buổi học hoặc buổi thi, **Then** đầu khu
   vực chính có khối "Lịch hôm nay" liệt kê buổi thi trước rồi buổi học (giờ, tên, phòng), và các
   cảnh báo (đồng bộ, quyền thông báo) như trang Hôm nay hiện tại.
3. **Given** danh sách Tất cả hoặc một danh sách của người dùng, **Then** task chưa xong được nhóm
   theo Quá hạn, Hôm nay, Ngày mai, 7 ngày tới, Sau này, Không có hạn; nhóm trống không hiện.
4. **Given** một dòng task, **Then** dòng có checkbox, tiêu đề, giờ hạn (hoặc ngày nếu ngoài 7 ngày)
   canh phải, chấm màu các nhãn và ★ nếu Quan trọng; task quá hạn có giờ hạn màu đỏ.
5. **Given** bấm vào một task, **Then** bảng chi tiết mở bên phải với mọi trường của task (tiêu đề,
   ghi chú, hạn chót, khung giờ làm, ưu tiên, danh sách, nhãn, Quan trọng, nhắc, liên kết buổi học
   nếu là task tự tạo); sửa trường nào thì lưu ngay khi rời ô đó; Esc đóng bảng.
6. **Given** bấm checkbox, **Then** task được đánh dấu hoàn thành, mờ đi rồi chuyển sang "Đã hoàn
   thành"; số đếm cập nhật ngay.
7. **Given** chọn một nhãn trong cột danh sách, **Then** khu vực chính hiện mọi task chưa xong có
   nhãn đó, nhóm như mục 3.
8. **Given** danh sách Đã hoàn thành, **Then** task đã xong hiện theo ngày hoàn thành, mới nhất
   trước; bỏ chọn checkbox thì task quay lại danh sách cũ.
9. **Given** người dùng tạo hoặc sửa danh sách, **Then** chọn được emoji cho danh sách (không bắt
   buộc) và emoji hiện trước tên danh sách ở cột danh sách và trong bảng chi tiết.

---

### User Story 3 - Thêm công việc nhanh (Priority: P1)

Ở đầu khu vực chính có ô "Thêm công việc". Gõ tiêu đề rồi nhấn Enter là task được tạo ngay trong
danh sách đang xem, ô được xoá trống để gõ tiếp.

**Why this priority**: Ghi lại việc cần làm nhanh nhất có thể là giá trị cốt lõi của app công việc.

**Independent Test**: Ở từng danh sách (Hôm nay, Ngày mai, 7 ngày tới, Tất cả, một danh sách người
dùng, một nhãn), gõ tiêu đề và nhấn Enter; kiểm tra task mới có giá trị mặc định đúng.

**Acceptance Scenarios**:

1. **Given** đang xem Hôm nay, **When** gõ "Nộp bài Toán" rồi Enter, **Then** task được tạo trong
   danh sách mặc định với hạn là hôm nay (không có giờ), hiện ngay trong nhóm Hôm nay.
2. **Given** đang xem Ngày mai, **Then** task mới có hạn ngày mai; đang xem 7 ngày tới hoặc Tất cả
   thì task mới không có hạn (Tất cả) hoặc hạn hôm nay (7 ngày tới).
3. **Given** đang xem danh sách "Cá nhân", **Then** task mới thuộc danh sách "Cá nhân", không có
   hạn; đang xem một nhãn thì task mới có nhãn đó.
4. **Given** ô trống hoặc chỉ có khoảng trắng, **When** nhấn Enter, **Then** không tạo gì.
5. **Given** vừa tạo task, **Then** ô "Thêm công việc" vẫn được chọn để gõ task tiếp theo; nhấn Esc
   thì bỏ chọn ô.

---

### User Story 4 - Lịch tuần mới (Priority: P2)

Trang Lịch hiển thị tuần (Thứ Hai đến Chủ Nhật) với: tên tháng/năm, nút "+", chọn chế độ
Ngày/Tuần/Tháng, nút trước/sau và "Hôm nay" ở đầu trang. Ngày hôm nay có số ngày tô tròn nổi bật và
một đường kẻ đỏ báo giờ hiện tại. Hàng "Cả ngày" ở trên cùng chứa task chỉ có ngày. Mỗi mục là một
khối màu nhạt theo màu nhãn hoặc môn học, có tiêu đề và khung giờ; task có thêm checkbox; buổi học
hiện thêm phòng; buổi thi nổi bật hơn hẳn; mục đã hoàn thành hoặc buổi đã huỷ thì mờ đi; các mục
trùng giờ xếp cạnh nhau.

**Why this priority**: Nhìn cả tuần học và việc cần làm trên cùng một lưới giúp lên kế hoạch; lịch
hiện tại đã dùng được nên đây là cải tiến, không chặn việc dùng app.

**Independent Test**: Với một tuần có buổi học trùng giờ một task có khung giờ làm, một buổi thi, một
task chỉ có ngày, một task chỉ có giờ hạn, một buổi huỷ và một task đã xong; kiểm tra vị trí, kiểu
hiển thị và việc xếp cạnh nhau của từng mục.

**Acceptance Scenarios**:

1. **Given** tuần chứa hôm nay, **When** mở Lịch, **Then** chế độ Tuần hiện Thứ Hai đến Chủ Nhật,
   đầu trang ghi tên tháng/năm (ví dụ "Tháng 11, 2026"; tuần nằm giữa hai tháng thì ghi "Tháng 11 –
   Tháng 12, 2026"), số ngày hôm nay được tô tròn, có đường kẻ đỏ tại giờ hiện tại và lưới tự cuộn
   tới gần giờ hiện tại.
2. **Given** task chỉ có ngày hạn, **Then** task nằm ở hàng "Cả ngày" của ngày đó.
3. **Given** task có hạn kèm giờ nhưng không có khung giờ làm, **Then** task hiện thành khối ngắn
   (30 phút) bắt đầu tại giờ hạn, có biểu tượng hạn chót.
4. **Given** task có khung giờ làm 14:00–16:00 và hạn 23:59 Thứ Sáu, **Then** khối nằm 14:00–16:00
   ở ngày của khung giờ làm; hạn chót hiện trong bảng chi tiết, không tạo khối thứ hai.
5. **Given** buổi học, **Then** khối ghi tên môn, khung giờ và phòng; buổi đã huỷ mờ đi và có chữ
   "Đã huỷ"; buổi thi có nền màu đậm, viền rõ và nhãn "Thi", khác hẳn buổi học.
6. **Given** ba mục trùng giờ, **Then** ba khối xếp cạnh nhau, chia đều chiều ngang, không khối nào
   che khối nào.
7. **Given** bấm checkbox trên khối task, **Then** task hoàn thành và khối mờ đi ngay.
8. **Given** bấm vào một khối, **Then** mở chi tiết của mục đó (bảng chi tiết task, hoặc chi tiết
   buổi học, buổi thi).
9. **Given** bấm "+", **Then** mở bảng tạo task mới với ngày là ngày đang chọn.
10. **Given** chọn chế độ Ngày hoặc Tháng, bấm trước/sau hoặc "Hôm nay", **Then** lịch chuyển đúng
    khoảng thời gian; chế độ Tháng hiện tóm tắt mỗi ngày như lịch tháng hiện tại.

---

### User Story 5 - Kéo thả trên lịch (Priority: P2)

Trên lịch Tuần và Ngày, người dùng kéo khối task sang giờ hoặc ngày khác, kéo mép dưới để đổi thời
lượng, kéo trên vùng trống để tạo task mới ở khung giờ đó. Kéo buổi học chỉ đổi riêng buổi đó, và app
hỏi xác nhận trước khi lưu.

**Why this priority**: Sắp xếp lại kế hoạch bằng kéo thả nhanh hơn nhiều so với mở form, nhưng vẫn có
thể sửa bằng bảng chi tiết nên không chặn.

**Independent Test**: Kéo một task có khung giờ làm từ Thứ Hai 14:00 sang Thứ Ba 09:00; kéo mép dưới
từ 2 giờ thành 3 giờ; kéo vùng trống Thứ Tư 10:00–11:30 để tạo task; kéo một buổi học sang 13:00 và
xác nhận; kiểm tra dữ liệu, nhắc và bản trong Lịch Apple được cập nhật.

**Acceptance Scenarios**:

1. **Given** task có khung giờ làm 14:00–16:00 Thứ Hai, **When** kéo khối sang Thứ Ba 09:00,
   **Then** khung giờ làm thành 09:00–11:00 Thứ Ba; hạn chót không đổi.
2. **Given** task chỉ có giờ hạn (khối ngắn), **When** kéo sang 17:00 ngày khác, **Then** hạn chót
   đổi thành ngày và giờ đó; các lời nhắc dời theo.
3. **Given** khối task có khung giờ làm, **When** kéo mép dưới, **Then** giờ kết thúc khung giờ làm
   đổi theo, làm tròn 15 phút, tối thiểu 15 phút; khối chỉ có giờ hạn không kéo dãn được.
4. **Given** task chỉ có ngày ở hàng "Cả ngày", **When** kéo sang một giờ trong lưới, **Then** task
   có khung giờ làm 1 giờ tại đó (hạn chót giữ nguyên); kéo sang ô "Cả ngày" của ngày khác thì đổi
   ngày hạn.
5. **Given** kéo trên vùng trống từ 10:00 đến 11:30 Thứ Tư, **Then** bảng chi tiết task mới mở với
   khung giờ làm 10:00–11:30 Thứ Tư, hạn chót là ngày Thứ Tư (không có giờ), con trỏ ở ô tiêu đề;
   bấm Esc khi tiêu đề trống thì không tạo task.
6. **Given** kéo một buổi học sang giờ khác, **When** thả, **Then** app hỏi "Chỉ đổi giờ buổi học
   ngày … sang …? Các buổi khác của môn không đổi."; đồng ý thì chỉ buổi đó đổi (như sửa riêng một
   buổi); huỷ thì khối về chỗ cũ.
7. **Given** kéo buổi học Thứ Hai 16/11 sang Thứ Bảy 21/11 lúc 08:00, **When** thả, **Then** app hỏi
   "Dời buổi học ngày 16/11 sang Thứ Bảy 21/11, 08:00? Các buổi khác của môn không đổi."; đồng ý thì
   chỉ buổi đó được dời, có dấu "Đã dời" (kèm ngày gốc) ở lịch và chi tiết buổi; deadline tự tạo,
   nhắc, bản tóm tắt và bản trong Lịch Apple tính theo ngày mới.
8. **Given** buổi thi, buổi đã huỷ, task đã hoàn thành, **Then** không kéo thả được (con trỏ không
   đổi thành biểu tượng kéo).
9. **Given** vừa kéo thả task, **Then** có thông báo nhỏ kèm nút "Hoàn tác" trong 5 giây; bấm Hoàn tác
   thì task về giờ cũ.

---

### User Story 6 - Khung giờ làm của task (Priority: P2)

Ngoài hạn chót, task có thể có khung giờ làm (giờ bắt đầu và kết thúc trong một ngày, không bắt
buộc), để lên kế hoạch "làm việc này lúc nào" trên lịch. Khung giờ làm chỉnh được trong bảng chi tiết
và bằng kéo thả.

**Why this priority**: Cần cho lịch tuần và kéo thả có ý nghĩa; task không có khung giờ làm vẫn dùng
như cũ.

**Independent Test**: Thêm khung giờ làm 19:00–21:00 Thứ Năm cho task hạn Chủ Nhật; kiểm tra lịch,
danh sách và nhắc.

**Acceptance Scenarios**:

1. **Given** bảng chi tiết task, **When** bật "Khung giờ làm" và chọn Thứ Năm 19:00–21:00, **Then**
   lưu được; lịch hiện khối 19:00–21:00 Thứ Năm.
2. **Given** giờ kết thúc không sau giờ bắt đầu, **Then** app từ chối và báo lỗi tiếng Việt ngay dưới
   ô giờ.
3. **Given** task có khung giờ làm, **Then** dòng task trong danh sách hiện khung giờ làm (ví dụ
   "T5 19:00–21:00") bên cạnh hạn chót; danh sách thông minh Hôm nay cũng gồm task có khung giờ làm
   hôm nay dù hạn chót ở ngày khác.
4. **Given** task có khung giờ làm, **Then** các lời nhắc vẫn tính theo hạn chót như hiện tại;
   khung giờ làm không tạo thêm lời nhắc và không được ghi sang Lịch/Lời nhắc của Apple.
5. **Given** xoá khung giờ làm, **Then** task trở về hiển thị theo hạn chót.

---

### User Story 7 - Thùng rác (Priority: P2)

Xoá task thì task vào Thùng rác thay vì mất ngay. Trong 30 ngày người dùng khôi phục được task với
đầy đủ thông tin; sau 30 ngày task bị xoá hẳn.

**Why this priority**: Tránh mất dữ liệu do bấm nhầm; giá trị cao nhưng không chặn các luồng chính.

**Independent Test**: Xoá một task có nhãn, nhắc và khung giờ làm; kiểm tra nó biến mất khỏi mọi
danh sách, lịch và Lời nhắc của Apple; khôi phục và kiểm tra mọi thông tin quay lại.

**Acceptance Scenarios**:

1. **Given** một task, **When** bấm Xoá (hoặc ⌘⌫), **Then** task chuyển vào Thùng rác ngay, không hỏi
   xác nhận, kèm thông báo "Đã chuyển vào Thùng rác" có nút "Hoàn tác".
2. **Given** task trong Thùng rác, **Then** nó không xuất hiện ở danh sách, lịch, trang Hôm nay, số
   đếm, thông báo tổng hợp, không có nhắc, và bị gỡ khỏi Lời nhắc của Apple.
3. **Given** Thùng rác, **Then** mỗi task hiện ngày xoá và "Còn N ngày"; bấm "Khôi phục" thì task về
   danh sách cũ với đầy đủ tiêu đề, ghi chú, hạn, khung giờ làm, ưu tiên, nhãn, Quan trọng, nhắc.
4. **Given** danh sách cũ của task đã bị xoá, **When** khôi phục, **Then** task về danh sách "Học
   tập" và app báo rõ điều đó.
5. **Given** task đã ở Thùng rác hơn 30 ngày, **Then** task bị xoá hẳn và không khôi phục được.
6. **Given** bấm "Xoá vĩnh viễn" một task hoặc "Dọn sạch Thùng rác", **Then** app hỏi xác nhận rồi xoá
   hẳn.
7. **Given** task tự tạo bị chuyển vào Thùng rác, **Then** quy tắc tự tạo không tạo lại task cho buổi
   đó; khôi phục thì task quay lại và vẫn liên kết với buổi học.
8. **Given** xoá một danh sách và chọn "xoá luôn các task", **Then** các task đó vào Thùng rác.

---

### User Story 8 - Giao diện gọn, sáng/tối và phím tắt (Priority: P3)

Toàn app dùng một phong cách nhất quán: nhiều khoảng trắng, bo góc mềm, màu riêng của app, tự theo
chế độ sáng/tối của macOS. Các thao tác thường dùng có phím tắt. Trang Môn học, Lịch thi và Cài đặt
chuyển sang bố cục mới mà vẫn giữ mọi chức năng hiện có.

**Why this priority**: Làm app dễ chịu khi dùng lâu và nhanh hơn với người quen bàn phím; app vẫn
dùng được đầy đủ nếu thiếu phần này.

**Independent Test**: Đổi macOS giữa Sáng và Tối khi app đang mở; dùng từng phím tắt trong bảng phím
tắt; đi qua mọi chức năng của feature 001 trong bố cục mới.

**Acceptance Scenarios**:

1. **Given** macOS chuyển sang chế độ Tối, **Then** app đổi sang giao diện tối ngay, không cần mở
   lại; chữ và màu nhãn vẫn đủ tương phản.
2. **Given** bảng phím tắt (FR-031), **When** nhấn từng phím, **Then** thao tác tương ứng xảy ra;
   menu "Trợ giúp → Phím tắt" (hoặc ⌘/) liệt kê đủ các phím bằng tiếng Việt.
3. **Given** thanh biểu tượng, **When** chọn Môn học, **Then** thấy học kỳ, danh sách môn, thêm môn
   một lần hoặc nhiều môn, nhập từ ảnh (khi feature 001 hoàn thành phần này).
4. **Given** chọn Cài đặt, **Then** thấy đủ các mục hiện có: Nhắc lịch và đồng bộ, Thông báo tổng
   hợp, Mốc nhắc quan trọng, Học kỳ, Ca học, Nhãn, Danh sách, Tự tạo deadline.
5. **Given** chọn Lịch thi, **Then** thấy danh sách buổi thi và các thao tác của feature 001 US11; khi
   phần đó chưa có, trang hiện "Sắp có" thay vì lỗi.

---

### Edge Cases

- Cửa sổ hẹp (dưới khoảng 900 điểm ảnh): bảng chi tiết che lên khu vực chính thay vì đẩy sang; dưới
  khoảng 700 điểm ảnh, cột danh sách thu gọn và mở lại bằng nút.
- Số đếm danh sách thông minh chỉ tính task chưa hoàn thành và không ở Thùng rác; Hôm nay gồm cả task
  quá hạn.
- Sang ngày mới khi app đang mở: các nhóm Hôm nay/Ngày mai/7 ngày tới, số đếm và đường kẻ giờ hiện
  tại tự cập nhật, không cần mở lại app.
- Task có khung giờ làm ở ngày sau hạn chót: vẫn lưu được nhưng bảng chi tiết hiện cảnh báo "Khung
  giờ làm sau hạn chót".
- Khung giờ làm vắt qua nửa đêm: không cho phép; khung giờ làm nằm trong một ngày.
- Kéo task ra ngoài vùng lịch hoặc nhấn Esc khi đang kéo: huỷ, khối về chỗ cũ.
- Kéo thả trong lúc mất kết nối tới phần lưu trữ trên máy: khối về chỗ cũ và báo lỗi tiếng Việt;
  không mất dữ liệu.
- Kéo buổi học trùng giờ buổi khác: vẫn cho phép sau xác nhận, kèm cảnh báo trùng giờ như hiện tại.
- Dời buổi học sang ngày đã có buổi khác của cùng môn cùng giờ bắt đầu: app từ chối và báo lỗi
  tiếng Việt (hai buổi không được trùng hoàn toàn).
- Dời buổi học ra ngoài khoảng ngày của học kỳ: vẫn cho phép sau xác nhận, kèm cảnh báo "ngoài học
  kỳ".
- Đổi lịch chung của môn (thứ, ngày bắt đầu/kết thúc) khi có buổi đã dời: buổi đã dời được giữ nguyên;
  ngày gốc của nó không sinh lại buổi mới.
- Kéo buổi học có task tự tạo: task tự tạo cập nhật theo quy tắc deadline tự tạo như khi sửa giờ
  buổi.
- Thùng rác rỗng: hiện "Thùng rác trống".
- Task trong Thùng rác vẫn được giữ khi tắt app hoặc khởi động lại máy; việc xoá hẳn sau 30 ngày diễn
  ra ở lần mở app hoặc lần kiểm tra định kỳ kế tiếp.
- Emoji không hợp lệ (nhiều hơn một emoji, hoặc là chữ thường): app từ chối; danh sách không có emoji
  hiện biểu tượng mặc định.
- Mở app lần thứ hai khi đã mở: đưa cửa sổ đang có lên trước, không mở cửa sổ mới.
- Thoát app trong lúc đang lưu: dữ liệu đã lưu trước đó còn nguyên (như constitution V).
- Mở app khi chưa cài trình đồng bộ Lịch: app vẫn hoạt động; cảnh báo như hiện tại trong Cài đặt.

## Requirements *(mandatory)*

### Functional Requirements

**Đóng gói app macOS**

- **FR-001**: Ứng dụng PHẢI được cài và mở như một app macOS riêng tên "Lịch Học Cá Nhân", có icon
  riêng (không dùng tên, logo hay màu của app khác), có cửa sổ riêng, mở được từ Dock, Launchpad và
  Spotlight, không cần mở trình duyệt.
- **FR-002**: Khi mở, app PHẢI tự khởi động phần lưu trữ và xử lý dữ liệu trên máy nếu chưa chạy,
  hiện màn hình "Đang khởi động…" và vào màn hình chính khi sẵn sàng; nếu thất bại thì hiện thông báo
  tiếng Việt kèm cách khắc phục và nút "Thử lại".
- **FR-003**: App PHẢI nhớ kích thước và vị trí cửa sổ; chỉ có một cửa sổ chính, mở lần hai thì đưa
  cửa sổ đang có lên trước.
- **FR-004**: Đóng cửa sổ hoặc thoát app KHÔNG ĐƯỢC dừng việc đồng bộ Lịch/Lời nhắc và KHÔNG ĐƯỢC làm
  mất dữ liệu.
- **FR-005**: App PHẢI tiếp tục tuân thủ constitution IV: chỉ kết nối trong máy, chạy đầy đủ khi
  không có internet.
- **FR-006**: App PHẢI có menu macOS tiếng Việt tối thiểu: Giới thiệu, Cài đặt (⌘,), Ẩn, Thoát (⌘Q),
  các lệnh Sửa (Hoàn tác, Cắt, Chép, Dán, Chọn tất cả), Cửa sổ, Trợ giúp → Phím tắt.

**Bố cục và điều hướng**

- **FR-007**: Màn hình PHẢI có thanh biểu tượng hẹp bên trái với 5 mục: Công việc, Lịch, Môn học,
  Lịch thi, Cài đặt; mục đang chọn được tô nổi bật; mỗi biểu tượng có chú thích tiếng Việt khi rê
  chuột.
- **FR-008**: Mục Công việc PHẢI có cột danh sách gồm theo thứ tự: Hôm nay, Ngày mai, 7 ngày tới, Tất
  cả (mỗi mục có số đếm task chưa xong); các danh sách của người dùng (emoji, tên, số đếm); các nhãn
  (chấm màu, tên); Đã hoàn thành; Thùng rác.
- **FR-009**: Định nghĩa danh sách thông minh (chỉ task chưa xong, không ở Thùng rác): Hôm nay = hạn
  hôm nay, quá hạn, hoặc có khung giờ làm hôm nay; Ngày mai = hạn hoặc khung giờ làm ngày mai; 7 ngày
  tới = hạn hoặc khung giờ làm từ hôm nay đến hết 6 ngày sau, cộng task quá hạn; Tất cả = mọi task chưa
  xong.
- **FR-010**: Khu vực chính PHẢI nhóm task theo: Quá hạn, Hôm nay, Ngày mai, 7 ngày tới (từng ngày có
  tên thứ), Sau này, Không có hạn; nhóm trống không hiện; mỗi nhóm có tên kèm số lượng và thu gọn/mở
  được bằng mũi tên (trạng thái thu gọn được nhớ); trong nhóm sắp theo giờ rồi theo ưu tiên (như
  feature 001 FR-005).
- **FR-011**: Mỗi dòng task PHẢI có: checkbox hoàn thành, ★ nếu Quan trọng, tiêu đề, chấm màu nhãn,
  biểu tượng "Tự tạo" nếu là task tự tạo, và canh phải là giờ hạn (hôm nay/ngày mai) hoặc ngày hạn
  (xa hơn), màu đỏ nếu quá hạn; nếu có khung giờ làm thì hiện thêm khung giờ làm.
- **FR-012**: Danh sách Hôm nay PHẢI có khối "Lịch hôm nay" ở đầu, gồm buổi thi rồi buổi học của hôm
  nay (giờ, tên, phòng, trạng thái huỷ) và các cảnh báo hiện có của trang Hôm nay; Hôm nay là màn hình
  mặc định khi mở app.
- **FR-013**: Bấm vào task PHẢI mở bảng chi tiết bên phải để xem và sửa mọi trường của task; thay đổi
  được lưu khi rời ô hoặc nhấn Enter ở ô một dòng; lỗi nhập hiện ngay dưới ô bằng tiếng Việt; Esc
  hoặc nút đóng thì đóng bảng.
- **FR-014**: Danh sách Đã hoàn thành PHẢI hiện task đã xong nhóm theo ngày hoàn thành (mới nhất
  trước); bỏ đánh dấu hoàn thành thì task quay lại danh sách của nó.
- **FR-015**: Danh sách của người dùng PHẢI có thể có một emoji (không bắt buộc, đúng một emoji),
  chọn từ bảng chọn emoji của macOS hoặc gõ trực tiếp; danh sách không có emoji dùng biểu tượng mặc
  định.

**Thêm nhanh**

- **FR-016**: Đầu khu vực chính PHẢI có ô "Thêm công việc"; nhấn Enter với tiêu đề không trống thì tạo
  task ngay, xoá trống ô và giữ con trỏ trong ô.
- **FR-017**: Giá trị mặc định của task thêm nhanh theo danh sách đang xem: Hôm nay → hạn hôm nay;
  Ngày mai → hạn ngày mai; 7 ngày tới → hạn hôm nay; Tất cả, Đã hoàn thành, Thùng rác → không hạn;
  danh sách người dùng → thuộc danh sách đó; nhãn → gắn nhãn đó. Danh sách của task mặc định là "Học
  tập" khi không xem một danh sách cụ thể. Ưu tiên Trung bình, không Quan trọng, nhắc theo mặc định.

**Khung giờ làm**

- **FR-018**: Task PHẢI có thể có khung giờ làm (ngày, giờ bắt đầu, giờ kết thúc; kết thúc sau bắt
  đầu; trong một ngày), độc lập với hạn chót; không bắt buộc.
- **FR-019**: Khung giờ làm chỉ dùng để hiển thị và lên kế hoạch: KHÔNG tạo thêm lời nhắc, KHÔNG ghi
  sang Lịch/Lời nhắc của Apple, KHÔNG ảnh hưởng việc xét quá hạn hay deadline tự tạo.

**Lịch**

- **FR-020**: Trang Lịch PHẢI có đầu trang gồm tên tháng/năm của khoảng đang xem, nút "+", chọn chế độ
  Ngày/Tuần/Tháng, nút trước/sau và "Hôm nay"; tuần bắt đầu Thứ Hai; mặc định chế độ Tuần.
- **FR-021**: Ở chế độ Ngày và Tuần: hàng tên thứ (T2 … CN) phía trên hàng số ngày; số ngày hôm nay
  được tô tròn bằng màu nhấn; có đường kẻ đỏ tại giờ hiện tại kèm nhãn giờ màu đỏ ở cột giờ, tự di
  chuyển theo thời gian; có hàng "Cả ngày" ngay dưới hàng số ngày cho task chỉ có ngày hạn; có nút ẩn/
  hiện cột bên để lịch rộng hơn.
- **FR-022**: Vị trí của task trên lưới: có khung giờ làm → khối theo khung giờ làm; không có khung
  giờ làm nhưng có giờ hạn → khối ngắn 30 phút bắt đầu tại giờ hạn kèm biểu tượng hạn chót; chỉ có
  ngày hạn → hàng "Cả ngày".
- **FR-023**: Mỗi mục là một khối màu nhạt theo màu hiển thị hiện có (nhãn đầu tiên, hoặc môn/danh
  sách), có tiêu đề và khung giờ; task có checkbox; buổi học có thêm phòng; mục Quan trọng có ★; buổi
  thi PHẢI nổi bật hơn hẳn (nền đậm, viền rõ, nhãn "Thi"); task đã xong và buổi đã huỷ mờ đi.
- **FR-024**: Các mục trùng giờ trong cùng ngày PHẢI xếp cạnh nhau theo cột, không khối nào che khối
  nào; khối quá hẹp vẫn hiện tiêu đề rút gọn và đầy đủ khi rê chuột.
- **FR-025**: Bấm vào khối PHẢI mở chi tiết của mục (bảng chi tiết task, chi tiết buổi học, chi tiết
  buổi thi); bấm checkbox của task đánh dấu hoàn thành ngay.
- **FR-026**: Ở chế độ Ngày và Tuần, người dùng PHẢI kéo được khối task để đổi ngày/giờ (task có khung
  giờ làm → dời khung giờ làm, giữ thời lượng; task chỉ có giờ hạn → đổi hạn chót; task chỉ có ngày
  kéo vào lưới → có khung giờ làm 1 giờ; kéo vào hàng "Cả ngày" → đổi ngày hạn), và kéo mép dưới khối
  có khung giờ làm để đổi thời lượng; mọi thay đổi làm tròn 15 phút.
- **FR-027**: Kéo trên vùng trống của lưới PHẢI mở bảng tạo task mới với khung giờ làm bằng vùng đã
  kéo và hạn chót là ngày đó (không giờ); task chỉ được tạo khi có tiêu đề.
- **FR-028**: Kéo buổi học PHẢI hỏi xác nhận trước khi lưu và chỉ đổi riêng buổi đó (như sửa riêng
  một buổi của feature 001); huỷ thì khối về chỗ cũ. Buổi học PHẢI dời được sang ngày khác (ví dụ
  học bù): buổi được đánh dấu "Đã dời" kèm ngày gốc, được giữ nguyên khi môn học thay đổi như mọi buổi
  có ngoại lệ, và mọi thứ phụ thuộc (deadline tự tạo, nhắc, bản tóm tắt, bản sao trong Lịch Apple)
  tính theo ngày mới. Dời buổi cũng làm được trong chi tiết buổi học (ô ngày), không chỉ bằng kéo
  thả. Buổi thi, buổi đã huỷ và task đã hoàn thành
  không kéo được.
- **FR-029**: Sau mỗi lần kéo thả task, app PHẢI hiện thông báo kèm "Hoàn tác" trong 5 giây; mọi thay
  đổi do kéo thả cập nhật nhắc và bản trong Lịch/Lời nhắc như khi sửa bằng form.

**Thùng rác**

- **FR-030**: Xoá task PHẢI chuyển task vào Thùng rác (không hỏi xác nhận, có "Hoàn tác"); task trong
  Thùng rác bị loại khỏi mọi danh sách, số đếm, lịch, trang Hôm nay, bản tóm tắt, nhắc và bản sao trong
  Lời nhắc của Apple; khôi phục được với đầy đủ thông tin trong 30 ngày kể từ lúc xoá; quá 30 ngày thì
  bị xoá hẳn tự động. "Xoá vĩnh viễn" và "Dọn sạch Thùng rác" PHẢI hỏi xác nhận. Quy tắc này thay cho
  yêu cầu xác nhận khi xoá task của feature 001 (FR-027); các loại xoá khác vẫn hỏi xác nhận như cũ.
- **FR-031**: Task tự tạo trong Thùng rác vẫn ngăn việc tạo lại cho buổi đó; khôi phục thì giữ liên
  kết với buổi học. Khôi phục task có danh sách đã bị xoá thì đưa về "Học tập" và báo cho người dùng.

**Phong cách và phím tắt**

- **FR-032**: Giao diện PHẢI tự theo chế độ Sáng/Tối của macOS ngay khi hệ thống đổi; cả hai chế độ
  PHẢI đạt độ tương phản chữ tối thiểu 4.5:1 với nền.
- **FR-033**: Giao diện PHẢI nhất quán: một bộ màu riêng của app, bo góc mềm, khoảng trắng rộng, cùng
  một kiểu chữ; không dùng tên, logo hay bộ màu nhận diện của app khác.
- **FR-034**: App PHẢI hỗ trợ tối thiểu các phím tắt: ⌘N thêm công việc (đưa con trỏ vào ô Thêm công
  việc); ⌘1…⌘5 chuyển Công việc/Lịch/Môn học/Lịch thi/Cài đặt; ⌘, mở Cài đặt; Esc đóng bảng chi tiết
  hoặc hộp thoại; ⌘⌫ chuyển task đang chọn vào Thùng rác; ⌘↩ đánh dấu hoàn thành task đang chọn; ↑/↓
  chọn task trước/sau trong danh sách; ở Lịch: ←/→ khoảng trước/sau, T về Hôm nay, D/W/M chọn chế độ
  Ngày/Tuần/Tháng; ⌘/ mở bảng phím tắt.
- **FR-035**: Mọi chữ hiển thị PHẢI bằng tiếng Việt (constitution VI), kể cả menu, chú thích biểu
  tượng, thông báo và bảng phím tắt.

**Giữ nguyên chức năng hiện có**

- **FR-036**: Mọi chức năng của feature 001 PHẢI dùng được trong bố cục mới, gồm ít nhất: quản lý
  danh sách; học kỳ, môn học, thêm nhiều môn, ca học; huỷ, khôi phục, sửa riêng buổi học; nhãn và lọc
  theo nhãn; deadline tự tạo; nhắc lịch, đồng bộ Lịch/Lời nhắc, thông báo tổng hợp, chế độ Quan trọng;
  và khi feature 001 hoàn thành: nhập lịch từ ảnh (ở mục Môn học) và lịch thi (ở mục Lịch thi).
- **FR-037**: Lọc theo nhãn trên lịch (feature 001 FR-045) PHẢI có trong trang Lịch mới.

### Key Entities

- **Task** (mở rộng): thêm khung giờ làm (ngày, giờ bắt đầu, giờ kết thúc; không bắt buộc) và thời
  điểm chuyển vào Thùng rác (trống nếu không ở Thùng rác).
- **Buổi học** (mở rộng): có thể được dời sang ngày khác; lưu ngày gốc và trạng thái "Đã dời" như một
  loại ngoại lệ của buổi (cùng với huỷ, đổi giờ, đổi phòng).
- **Danh sách** (mở rộng): thêm emoji (không bắt buộc, đúng một emoji).
- **Danh sách thông minh** (suy ra, không lưu): Hôm nay, Ngày mai, 7 ngày tới, Tất cả, Đã hoàn thành,
  Thùng rác; nội dung và số đếm tính từ task theo FR-009.
- **Trạng thái cửa sổ** (lưu trên máy): kích thước, vị trí, mục và danh sách đang chọn gần nhất.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Từ lúc bấm icon trên Dock đến lúc dùng được màn hình Hôm nay: dưới 3 giây khi phần lưu
  trữ đang chạy, dưới 60 giây khi phải khởi động nó.
- **SC-002**: Thêm một task bằng ô "Thêm công việc" mất dưới 5 giây (gõ tiêu đề ngắn và Enter), và
  task xuất hiện trong danh sách ngay khi nhấn Enter.
- **SC-003**: 100% kịch bản kiểm chứng của feature 001 (quickstart V1–V21, trừ phần chưa làm) vẫn pass
  khi thực hiện trong app mới.
- **SC-004**: Trên lịch tuần có đến 5 mục trùng giờ cùng lúc, 0 khối bị che lấp; mọi tiêu đề đọc được
  đầy đủ khi rê chuột.
- **SC-005**: Đổi giờ một task bằng kéo thả hoàn tất trong 1 thao tác kéo và dưới 3 giây; giờ mới
  hiện trong Lời nhắc của Apple trên Mac trong vòng 1 phút.
- **SC-006**: Khôi phục task từ Thùng rác trả lại 100% thông tin (tiêu đề, ghi chú, hạn, khung giờ
  làm, ưu tiên, danh sách, nhãn, Quan trọng, nhắc); 100% task quá 30 ngày bị xoá hẳn trong vòng một
  ngày sau mốc 30 ngày.
- **SC-007**: Giao diện đổi theo chế độ Sáng/Tối của macOS trong vòng 1 giây; 100% chữ đạt tương phản
  4.5:1 ở cả hai chế độ.
- **SC-008**: 100% phím tắt trong FR-034 hoạt động và được liệt kê trong bảng phím tắt.
- **SC-009**: Người dùng tìm được mỗi chức năng chính (thêm task, xem lịch tuần, thêm môn, huỷ một
  buổi, bật đồng bộ, khôi phục task) trong không quá 3 lần bấm từ màn hình mặc định.
- **SC-010**: 0 kết nối ra ngoài máy được tạo bởi app (constitution IV), kiểm tra khi tắt mạng.

## Assumptions

- Feature này dựa trên dữ liệu và chức năng của feature `001-task-class-scheduler`; các phần còn dở ở
  feature 001 (nhập ảnh, lịch thi) xuất hiện trong bố cục mới khi được làm xong.
- Phần lưu trữ và xử lý dữ liệu tiếp tục chạy trên máy như hiện tại; app mới là cửa sổ riêng thay cho
  trình duyệt, không đổi nơi lưu dữ liệu. App vẫn cần môi trường chạy đã cài sẵn trên máy như hiện
  tại.
- Đóng cửa sổ không thoát app (theo thói quen macOS); thoát app (⌘Q) không dừng phần lưu trữ và trình
  đồng bộ Lịch, để nhắc trên iPhone vẫn được cập nhật.
- Bố cục theo hai ảnh tham khảo người dùng gửi (mục "Ảnh tham khảo bố cục"); phần nào ảnh không thể
  hiện thì theo mô tả bằng chữ trong yêu cầu.
- "Lấy cảm hứng" nghĩa là bố cục quen thuộc (thanh biểu tượng, cột danh sách, khu vực chính, bảng chi
  tiết); tên, icon, bộ màu và chi tiết hình ảnh là của riêng app.
- Buổi học và buổi thi không có checkbox hoàn thành; chỉ task có.
- Lưới lịch hiện đủ 24 giờ, khi mở tự cuộn tới khoảng giờ hiện tại (hoặc 06:00 nếu xem tuần khác).
- Kéo thả chỉ có trên chế độ Ngày và Tuần; chế độ Tháng chỉ xem và bấm.
- Danh sách mặc định cho task thêm nhanh ngoài một danh sách cụ thể là "Học tập" (danh sách chứa task
  tự tạo), vì người dùng chính là sinh viên.
- Không có tìm kiếm trong phiên bản này (giữ như feature 001).
- Thùng rác chỉ áp dụng cho task; xoá môn học, học kỳ, ca học, nhãn, danh sách vẫn hỏi xác nhận và
  xoá hẳn như feature 001.
- Khối task chỉ có giờ hạn dài 30 phút để đủ chỗ đọc tiêu đề; đây chỉ là cách hiển thị, không phải
  thời lượng thật.
