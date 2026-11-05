# Lịch Học Cá Nhân Constitution

## Core Principles

### I. Code Dễ Đọc

- Tên biến, hàm, lớp và file PHẢI mô tả rõ mục đích; không dùng tên viết tắt khó hiểu
  (trừ các quy ước phổ biến như `i`, `id`, `url`).
- Mỗi hàm PHẢI làm một việc; hàm dài hơn ~40 dòng hoặc lồng quá 3 cấp PHẢI được tách nhỏ
  hoặc có lý do ghi rõ trong review.
- Code PHẢI theo một định dạng thống nhất, được áp dụng bằng công cụ format/lint tự động
  của ngôn ngữ đang dùng.
- Comment giải thích *tại sao*, không lặp lại *cái gì* code đã nói rõ.
- Ưu tiên cách viết đơn giản, tường minh hơn cách viết "thông minh" nhưng khó hiểu.

**Lý do**: Code được đọc nhiều hơn được viết; code dễ đọc giúp sửa lỗi nhanh, review dễ và
người mới tham gia hiểu được dự án.

### II. Kiểm Thử Chức Năng Chính

- Mỗi chức năng chính (luồng người dùng cốt lõi và logic nghiệp vụ quan trọng) PHẢI có
  test tự động trước khi được coi là hoàn thành.
- Test PHẢI bao phủ trường hợp thành công và ít nhất một trường hợp lỗi/biên quan trọng.
- Toàn bộ test PHẢI chạy được bằng một lệnh duy nhất và PHẢI pass trước khi merge/release.
- Khi sửa một lỗi trong chức năng chính, PHẢI thêm test tái hiện lỗi đó.
- Không bắt buộc test cho code phụ trợ đơn giản (getter/setter, cấu hình, giao diện thuần
  trình bày) trừ khi có logic đáng kể.

**Lý do**: Test cho phần quan trọng nhất mang lại độ tin cậy cao nhất với chi phí hợp lý,
giúp thay đổi code mà không sợ làm hỏng tính năng cốt lõi.

### III. Giao Diện Đơn Giản

- Mỗi màn hình PHẢI có một mục đích chính rõ ràng; hành động chính PHẢI dễ nhận thấy.
- Chỉ hiển thị thông tin và điều khiển cần thiết cho tác vụ hiện tại; tính năng nâng cao
  NÊN được ẩn hoặc đặt ở vị trí phụ.
- Màu sắc, font chữ, khoảng cách và thành phần giao diện PHẢI nhất quán trong toàn ứng dụng.
- Thông báo lỗi PHẢI dễ hiểu với người dùng và chỉ ra cách khắc phục.
- Không thêm hiệu ứng, trang trí hoặc thư viện UI nặng nếu không phục vụ trực tiếp
  trải nghiệm người dùng.

**Lý do**: Giao diện đơn giản giúp người dùng hoàn thành việc nhanh hơn, ít nhầm lẫn hơn,
và cũng dễ phát triển, bảo trì hơn.

### IV. Ứng Dụng Cá Nhân, Chạy Offline Trên Mac

- Ứng dụng phục vụ một người dùng duy nhất và PHẢI chạy trên macOS (máy Mac của chủ dự án).
- KHÔNG có đăng nhập, tài khoản, phân quyền hay quản lý nhiều người dùng.
- KHÔNG cần server từ xa hay dịch vụ cloud; mọi chức năng PHẢI hoạt động đầy đủ khi không có
  kết nối internet.
- KHÔNG kết nối ra ngoài máy. Kết nối nội bộ trong máy (localhost, ví dụ giữa giao diện,
  backend và cơ sở dữ liệu chạy trên cùng máy Mac) được phép. Chỉ có hai ngoại lệ, nêu dưới
  đây: đồng bộ lịch qua iCloud của chính người dùng, và sao lưu vào thư mục người dùng chọn
  (kể cả iCloud Drive của chính người dùng).
- Không gửi dữ liệu hay ảnh ra ngoài máy (không analytics, không telemetry, không gọi API
  hay dịch vụ AI từ xa). Mọi xử lý, kể cả nhận diện ảnh, PHẢI chạy hoàn toàn trên máy.
- Không cần hỗ trợ Windows, Linux, mobile hay trình duyệt khác ngoài phạm vi chạy trên Mac.

**Ngoại lệ 1 — đồng bộ lịch qua iCloud của chính người dùng**:

- Ứng dụng ĐƯỢC PHÉP ghi bản sao lời nhắc (buổi học, task) vào ứng dụng Lịch và Lời nhắc có sẵn
  trên Mac, để hệ thống của Apple tự đồng bộ qua iCloud của chính người dùng sang iPhone.
  Ứng dụng không tự kết nối tới iCloud; việc đồng bộ do Lịch/Lời nhắc của Apple đảm nhiệm.
- Chức năng này PHẢI do người dùng bật trong cài đặt, tắt được bất kỳ lúc nào, và khi tắt thì
  ứng dụng PHẢI xoá các mục nó đã ghi.
- Chỉ được ghi các thông tin tối thiểu cần cho lời nhắc: tên môn hoặc tiêu đề task, thời gian,
  phòng học và thời điểm nhắc. KHÔNG ghi ghi chú, ảnh hay dữ liệu nào khác.
- Ứng dụng chỉ được ghi vào lịch và danh sách lời nhắc riêng do nó tạo, không được đọc, sửa
  hay xoá mục nào khác của người dùng.
- Dữ liệu gốc vẫn PHẢI lưu và xử lý hoàn toàn trên máy; Lịch/Lời nhắc chỉ là bản sao để nhắc.
  Mọi ngoại lệ mới về gửi dữ liệu ra ngoài PHẢI được bổ sung vào constitution trước khi
  triển khai.

**Lý do**: Phạm vi một người, một máy, không mạng giúp loại bỏ toàn bộ độ phức tạp về
bảo mật, đồng bộ và hạ tầng, giữ ứng dụng nhỏ gọn, riêng tư và dễ bảo trì. Người dùng không
luôn mang theo Mac, nên lời nhắc trên iPhone là cần thiết; đi qua ứng dụng có sẵn của Apple
giữ cho ứng dụng không kết nối ra ngoài máy và không cần server riêng. Kết nối localhost
không làm dữ liệu rời khỏi máy nên được phép.

**Ngoại lệ 2 — sao lưu vào thư mục người dùng chọn, kể cả iCloud Drive của chính người dùng**:

- Ứng dụng ĐƯỢC PHÉP ghi file sao lưu chứa toàn bộ dữ liệu vào một thư mục do người dùng chọn
  (ví dụ trên ổ SSD rời), kể cả thư mục nằm trong iCloud Drive của chính người dùng. Việc đưa
  file lên iCloud do macOS đảm nhiệm; ứng dụng không tự kết nối tới iCloud hay dịch vụ nào khác.
- Sao lưu tự động PHẢI tắt được bất kỳ lúc nào trong cài đặt. Ứng dụng chỉ được tạo, đọc và xoá
  các file sao lưu do chính nó tạo; không được đọc, sửa hay xoá file khác của người dùng.
- Dữ liệu gốc vẫn PHẢI lưu và xử lý hoàn toàn trên máy; bản sao lưu chỉ dùng để khôi phục.
- Thư mục đích không có hoặc không ghi được KHÔNG ĐƯỢC làm hỏng hay chặn ứng dụng.

**Lý do (ngoại lệ 2)**: Mất dữ liệu cục bộ là mất vĩnh viễn (Nguyên tắc V). Bản sao lưu nằm
ngoài ổ trong của Mac — trên iCloud Drive hay ổ rời của chính người dùng — bảo vệ dữ liệu khi
máy hỏng mà vẫn không cần server riêng và ứng dụng vẫn không tự kết nối ra ngoài máy.

### V. Dữ Liệu Cục Bộ Bền Vững

- Toàn bộ dữ liệu PHẢI được lưu cục bộ trên máy Mac (file hoặc cơ sở dữ liệu nhúng
  như SQLite/JSON), không phụ thuộc vào dịch vụ bên ngoài.
- Dữ liệu PHẢI được ghi xuống đĩa ngay khi người dùng lưu/thay đổi, và PHẢI còn nguyên
  sau khi tắt app, khởi động lại app hoặc khởi động lại máy.
- Việc ghi dữ liệu PHẢI an toàn trước sự cố (ví dụ: ghi file tạm rồi đổi tên, hoặc dùng
  transaction) để không làm hỏng dữ liệu cũ khi app bị tắt đột ngột.
- Lưu trữ dữ liệu (lưu, đọc lại sau khởi động lại) là chức năng chính và PHẢI có test
  theo Nguyên tắc II.
- Vị trí lưu dữ liệu PHẢI cố định, được ghi trong README để người dùng có thể tự sao lưu.

**Lý do**: Với ứng dụng cá nhân không có server, mất dữ liệu cục bộ là mất vĩnh viễn;
độ bền dữ liệu là yêu cầu không thể thương lượng.

### VI. Giao Diện Tiếng Việt

- Toàn bộ chữ hiển thị cho người dùng (nhãn, nút, menu, thông báo, thông báo lỗi) PHẢI
  bằng tiếng Việt có dấu, rõ ràng và tự nhiên.
- Tiếng Việt có dấu PHẢI hiển thị, nhập liệu, lưu trữ và tìm kiếm đúng (dùng UTF-8).
- Ngày giờ PHẢI hiển thị theo định dạng Việt Nam (ví dụ: `Thứ Hai, 04/11/2026`, giờ 24h).
- Không bắt buộc hỗ trợ đa ngôn ngữ; code, tên biến và comment có thể dùng tiếng Anh.

**Lý do**: Người dùng duy nhất là người Việt; giao diện tiếng Việt giúp dùng hằng ngày
dễ dàng và không gây nhầm lẫn.

## Ràng Buộc Bổ Sung

- Ưu tiên giải pháp đơn giản nhất đáp ứng yêu cầu (YAGNI); không thêm tính năng hay lớp
  trừu tượng "để dành cho sau này".
- Chỉ thêm thư viện phụ thuộc khi lợi ích rõ ràng hơn chi phí bảo trì.
- Dự án PHẢI có README hướng dẫn cài đặt, chạy ứng dụng và chạy test.

## Quy Trình Phát Triển

- Mỗi thay đổi PHẢI được kiểm tra theo sáu nguyên tắc cốt lõi trước khi merge: code dễ đọc,
  test chức năng chính pass, giao diện đơn giản, chạy offline trên Mac, dữ liệu không mất,
  giao diện tiếng Việt.
- Lint/format và test PHẢI pass trước khi merge.
- Các vi phạm nguyên tắc (nếu bắt buộc) PHẢI được ghi rõ lý do trong plan hoặc review.

## Governance

- Constitution này có hiệu lực cao hơn mọi quy ước khác của dự án.
- Sửa đổi PHẢI được ghi lại trong file này, kèm cập nhật phiên bản và ngày sửa đổi.
- Phiên bản theo semantic versioning: MAJOR khi bỏ hoặc định nghĩa lại nguyên tắc;
  MINOR khi thêm nguyên tắc/mục hoặc mở rộng đáng kể; PATCH khi làm rõ câu chữ.
- Mọi spec, plan và review PHẢI kiểm tra tuân thủ constitution; độ phức tạp vượt mức
  PHẢI có lý do chính đáng.

**Version**: 2.3.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-05
