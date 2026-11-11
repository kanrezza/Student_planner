# Research: Bảng Kanban cho công việc và đính kèm file

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-11

Giữ kiến trúc hiện tại: Flask + PostgreSQL trong Docker, React, app Tauri, agent macOS. Yêu cầu của người dùng cho
lần lập kế hoạch này:
- lưu file đính kèm trong một Docker named volume riêng, không bind mount vào thư mục dự án;
- đặt tên file theo hash nội dung;
- sao lưu tự động gộp cả database lẫn thư mục file;
- Kanban dùng một thư viện kéo thả nhẹ cho React, có hỗ trợ bàn phím.

## R1. Thư viện kéo thả cho bảng Kanban

- **Decision**: `@dnd-kit/core` 6.3 + `@dnd-kit/sortable` 10 + `@dnd-kit/utilities` 3 (MIT), ghim phiên bản chính xác
  như các gói khác trong `package.json`.
- **Rationale**:
  - Nhẹ, khoảng 15 KB gzip cho cả ba gói, và không có phụ thuộc ngoài React.
  - Có sẵn `KeyboardSensor` với `sortableKeyboardCoordinates`, nên dùng được bằng bàn phím (FR-013).
  - Có `announcements` và `screenReaderInstructions`, nên viết được thông báo tiếng Việt cho trình đọc màn hình
    (US3 kịch bản 5).
  - Hỗ trợ nhiều vùng sắp xếp (3 cột) trong một `DndContext`, kéo giữa các cột được.
  - Chạy tốt trong WKWebView vì dùng Pointer Events.
- **Alternatives considered**:
  - `@hello-pangea/dnd` (bản kế thừa của react-beautiful-dnd): có bàn phím tốt nhưng nặng hơn khoảng 3 lần và áp đặt
    cấu trúc DOM.
  - `react-beautiful-dnd`: đã ngừng phát triển.
  - Kéo thả HTML5 thuần (app đang dùng cho lịch): không có bàn phím và không có bóng thẻ khi kéo trong WKWebView. Loại.
- **Phím tắt bổ sung**: ngoài cách "Space nhấc thẻ, mũi tên di chuyển, Space thả" của dnd-kit, bảng có phím tắt riêng
  cho thẻ đang chọn: ⌘←/⌘→ đổi cột, ⌘↑/⌘↓ đổi thứ tự, Enter mở chi tiết, phím `X` để Xong/bỏ Xong (FR-013). Lý do không
  dùng Space: Space đã được dnd-kit dùng để nhấc thẻ. Ở bước triển khai sẽ kiểm tra trùng với `useHotkeys` hiện có.

## R2. Trạng thái "Đang làm" và thứ tự trên bảng

- **Decision**:
  - Giữ `tasks.completed_at` là nguồn duy nhất của trạng thái "Xong" để không đụng mọi luồng hiện có: nhắc, đồng bộ,
    lặp, deadline tự tạo, Hôm nay.
  - Thêm `tasks.in_progress` (boolean, mặc định false).
  - Trạng thái suy ra như sau: `completed_at IS NOT NULL` là `done`; ngược lại `in_progress` thì `doing`, còn lại là
    `todo`.
  - Khi hoàn thành, `in_progress` được đặt về false. Vì vậy bỏ Xong thì task về Chưa làm, đúng mục Edge Cases của spec.
  - Thứ tự trên bảng: thêm `tasks.board_rank` (double precision). Thẻ được thả giữa hai thẻ nhận giá trị trung bình;
    thả lên đầu cột nhận `min − 1`; xuống cuối nhận `max + 1`.
  - Khi khoảng cách giữa hai thẻ kề nhau nhỏ hơn `1e-6`, sắp lại cả cột thành 1, 2, 3… trong cùng transaction.
  - Task mới có `board_rank = min(cột Chưa làm) − 1` để nằm đầu cột (FR-006).
  - Cột Xong chưa sắp tay thì xếp theo `completed_at` giảm dần. Ngay khi người dùng kéo trong cột Xong, `board_rank`
    được dùng.
- **Rationale**: Mỗi lần kéo chỉ ghi một dòng (trừ khi phải sắp lại cột). Không cần bảng thứ tự riêng. Dữ liệu cũ
  nâng cấp được bằng cách đặt `board_rank` theo `sort_key` hiện có.
- **Alternatives considered**:
  - Cột `status` dạng enum thay `completed_at`: phải sửa mọi truy vấn hiện có. Loại.
  - Chuỗi LexoRank: mạnh hơn cần thiết cho một người dùng với vài trăm task.
  - Danh sách id theo cột lưu trong settings: dễ lệch với dữ liệu task.

## R3. "Môn học" của task để lọc bảng

- **Decision**:
  - Thêm `tasks.subject_id` (nullable, FK `subjects.id` ON DELETE SET NULL); chọn được trong bảng chi tiết task.
  - Môn hiệu lực của task = `tasks.subject_id`, nếu rỗng thì lấy môn của buổi học nguồn (`source_session_id`, áp dụng
    cho deadline tự tạo).
  - Bộ lọc bảng theo môn dùng môn hiệu lực này.
- **Rationale**: Đúng mục Assumptions của spec. Deadline tự tạo được lọc theo môn mà không cần ghi thêm dữ liệu.

## R4. Nơi lưu và cách ghi file đính kèm

- **Decision**:
  - Dùng Docker named volume `lichhoc_attachments`, gắn vào backend ở `/var/lib/lichhoc/attachments`. Volume nằm trên
    ổ trong của Mac (trong máy ảo OrbStack/Docker) giống `lichhoc_pgdata`, nên tháo ổ SSD chứa mã nguồn không ảnh
    hưởng (SC-010).
  - Tên file = SHA-256 của nội dung, chia thư mục theo 2 ký tự đầu: `ab/ab12…ef` (tránh một thư mục chứa quá nhiều
    file).
  - Ghi an toàn theo các bước:
    1. Ghi luồng upload vào `.incoming/<uuid>` trong cùng volume, vừa ghi vừa tính SHA-256 và đếm byte (dừng ngay khi
       vượt giới hạn).
    2. `fsync` file.
    3. Nếu blob cùng hash đã có thì xoá file tạm (lưu một bản, FR-020). Nếu chưa có thì `os.replace` sang tên cuối rồi
       `fsync` thư mục.
    4. Ghi dòng CSDL (blob + mục đính kèm) trong một transaction.
  - Hệ quả: lỗi giữa chừng chỉ để lại file trong `.incoming/`, được dọn khi backend khởi động và sau mỗi lần upload
    lỗi.
- **Rationale**: Đúng yêu cầu người dùng (named volume riêng, tên theo hash) và constitution V (ghi file tạm rồi đổi
  tên). Nội dung trùng tự gộp vì cùng tên.
- **Alternatives considered**:
  - Lưu vào PostgreSQL (`bytea`/large object): làm dump và sao lưu phình to, chậm, không dùng `sendfile` được.
  - Thư mục trên Mac qua bind mount `~/Library/Application Support`: phụ thuộc đường dẫn người dùng và quyền của Docker
    Desktop/OrbStack; người dùng đã chọn named volume.

## R5. Upload lớn qua nginx và Flask

- **Decision**:
  - Thêm `location /api/attachments` trong `frontend/nginx.conf` với `client_max_body_size 510m` (trần 500 MB của cài
    đặt + phần đầu multipart), `proxy_request_buffering off`, `proxy_read_timeout 300s`.
  - Route upload đặt `request.max_content_length` theo cài đặt hiện tại (Flask 3.1 hỗ trợ, đã dùng cho khôi phục ở
    feature 003).
  - Đọc từng file của multipart bằng `stream.read(1 MiB)`, không `save()` vào `/tmp`.
  - Frontend upload bằng `XMLHttpRequest` để có `upload.onprogress` cho thanh tiến trình (US4 kịch bản 8). `fetch` không
    có tiến trình upload.
- **Giới hạn**:
  - Kiểm tra ở trình duyệt trước khi gửi, theo `attachment_max_mb` lấy từ `/settings`.
  - Kiểm tra lại ở server theo số byte thực đếm được: vượt thì trả 413 `file_too_large`.

## R6. Đếm tham chiếu và dọn file không dùng

- **Decision**:
  - Bảng `attachment_blobs (sha256 PK, size, mime_type, created_at)`.
  - Bảng `attachments` (mục đính kèm), mỗi dòng trỏ tới một blob và đúng một nơi gắn: `task_id` / `subject_id` /
    `session_id` / `exam_id`, CHECK đúng một cột khác NULL, FK ON DELETE CASCADE.
  - Task vào Thùng rác: mục đính kèm giữ nguyên, chỉ bị ẩn vì truy vấn lọc task đã xoá. Khôi phục task thì file trở lại
    tự nhiên (FR-023).
  - Xoá hẳn task, môn, buổi thi: mục đính kèm bị CASCADE xoá. Sau commit, service gọi `collect_garbage(candidates)` để
    xoá blob không còn dòng `attachments` nào trỏ tới (cả dòng CSDL lẫn file).
  - Khi backend khởi động (và mỗi ngày một lần qua cơ chế "throttled" như dọn Thùng rác) chạy quét đầy đủ:
    - xoá file trong volume không có dòng `attachment_blobs`;
    - xoá dòng `attachment_blobs` không có `attachments`;
    - đánh dấu dòng blob mất file. Trường hợp này không nên xảy ra; nếu có thì ghi log và hiện "File bị thiếu" ở giao
      diện.
- **Rationale**: Xoá file sau commit nên lỗi giữa chừng chỉ để lại rác (được quét sau), không bao giờ mất file đang
  dùng. Đạt SC-008 nhờ lượt quét.

## R7. Sao lưu gộp database và file

- **Decision**: Định dạng `.lhbackup` lên **format 2**: vẫn là ZIP không nén, gồm:
  - `manifest.json`
  - `data.dump`
  - `attachments/<sha256>`: mỗi blob đang được dùng có đúng một mục.

  Manifest thêm `attachments: {count, bytes}`. Kiểm tra toàn vẹn bằng chính tên file (SHA-256), không cần liệt kê từng
  hash trong manifest.
- **Tạo bản sao lưu**:
  - Ghi ZIP từng blob bằng `zf.write` từ volume, không đọc cả file vào bộ nhớ.
  - Agent đã tải bản sao lưu theo luồng (`stream=True`), nên file lớn vẫn được.
- **Khôi phục**:
  - Nhận cả format 1 (không có file) và format 2.
  - Giải nén blob vào `.restore/<id>/` trong volume (kiểm tra SHA-256 từng file khi giải nén) trước khi đụng vào CSDL.
  - Sau khi nạp dump và nâng cấp schema thành công: chuyển các blob còn thiếu vào chỗ chính bằng `os.replace`, rồi chạy
    quét dọn (R6).
  - Lỗi ở bất kỳ bước nào: xoá thư mục `.restore`; blob cũ không bị đụng tới nên dữ liệu hiện tại còn nguyên.
- **Cảnh báo dung lượng (FR-026)**:
  - `settings.backup_attachments_warn_mb` mặc định 1024.
  - `GET /backup/status` trả thêm `attachments_bytes` và `attachments_warning`.
  - Agent gửi thông báo macOS nhẹ sau lần sao lưu tự động khi vượt ngưỡng, tối đa 1 lần mỗi ngày.
  - Cài đặt → Sao lưu hiện dòng cảnh báo kèm dung lượng ước tính của mỗi bản.
- **Alternatives considered**:
  - Sao lưu file riêng và tăng dần theo hash: tiết kiệm chỗ nhưng thêm định dạng và đổi agent (chép thư mục), khó
    khôi phục một bản duy nhất. Để dành cho sau nếu dung lượng thành vấn đề.
  - Nén ZIP: tài liệu PDF/ảnh/Office vốn đã nén. Loại.

## R8. Xem trước ảnh và PDF trong app

- **Decision**:
  - `GET /attachments/{id}/content` trả nội dung với `Content-Disposition: inline` **chỉ** cho danh sách MIME an toàn:
    `image/png`, `image/jpeg`, `image/gif`, `image/webp`, `image/heic`, `image/heif`, `application/pdf`.
  - Mọi loại khác (kể cả SVG, HTML, XML) luôn trả `attachment` để tránh chạy script trong trang app.
  - Kèm `X-Content-Type-Options: nosniff` và `Content-Security-Policy: sandbox; default-src 'none'; img-src 'self';
    object-src 'self'`.
  - MIME xác định từ phần mở rộng **và** chữ ký đầu file (magic bytes). Không khớp thì coi là loại khác.
  - Ảnh xem bằng `<img>` trong khung xem trước có phóng to/thu nhỏ. WKWebView hiển thị được HEIC; trình duyệt không hỗ
    trợ HEIC thì hiện "Không xem trước được" kèm nút Tải về.
  - PDF xem bằng `<iframe>` dùng trình xem PDF có sẵn của WKWebView/Chrome. PDF hỏng hoặc có mật khẩu thì trình xem tự
    báo; app vẫn có nút Mở/Tải về (Edge Cases).
- **Alternatives considered**: `pdf.js`: thêm khoảng 1 MB vào bundle, không cần khi WKWebView đã xem được PDF. Loại.
- **Kiểm tra trong spike**: PDF trong `<iframe>` ở WKWebView của Tauri 2. Nếu không hiện thì mở PDF trong một cửa sổ
  Tauri phụ trỏ thẳng tới URL nội dung.

## R9. Mở bằng ứng dụng mặc định của macOS, tải về

- **Decision**: thêm hai lệnh Tauri trong `desktop/src-tauri`, cho phép qua capability mới `attachments`, chỉ dành cho
  trang `http://127.0.0.1:8080/*`.
  - `open_attachment(id)`:
    1. Hỏi backend metadata (`GET /api/attachments/{id}`).
    2. Từ chối nếu `is_executable`.
    3. Tải nội dung (`/download`) về `~/Library/Caches/<bundle-id>/attachments/<sha256>/<tên hiển thị>`; đã có thì
       dùng lại.
    4. Gọi `/usr/bin/open <đường dẫn>`.
  - `save_attachment(id)`: tải về `~/Downloads/<tên>`; trùng tên thì thêm " (2)", " (3)"…; trả đường dẫn để hiện
    thông báo "Đã lưu vào Tải về" kèm nút "Hiện trong Finder" (dùng lại lệnh `reveal_in_finder` sẵn có).
  - HTTP tới backend dùng `std::net::TcpStream` hoặc `curl` có sẵn của macOS để không thêm crate. Chọn `curl`
    (`/usr/bin/curl --fail -o …`): đơn giản, xử lý được file lớn.
- **Trên trình duyệt**: "Mở" của loại không xem trước được và "Tải về" đều dùng `<a href=/api/attachments/{id}/download
  download>`.
- **File thực thi** (FR-022): backend gắn cờ `is_executable` theo phần mở rộng (`.app .command .sh .tool .exe .msi .pkg
  .dmg .scpt .jar .bat .ps1 .js .vbs .workflow`) và chữ ký Mach-O/ELF/PE. Giao diện ẩn nút Mở và hiện cảnh báo; lệnh Tauri
  cũng tự từ chối.

## R10. Dán file (⌘V)

- **Decision**:
  - Ảnh trong clipboard (chụp màn hình): `clipboardData.files`/`items`, giống luồng dán ảnh hiện có (`usePasteFile`).
  - File chép từ Finder: WKWebView thường chỉ đưa vào `clipboardData` một ảnh biểu tượng hoặc tên file, không có nội
    dung file.
  - Trong app Tauri thêm lệnh `clipboard_file_paths()`. Lệnh đọc `NSPasteboard` qua `osascript -e 'the clipboard as
    «class furl»'` (nhiều file thì dùng JXA `$.NSPasteboard.generalPasteboard`) và trả danh sách đường dẫn.
  - Sau đó lệnh `upload_paths(owner_type, owner_id, paths)` upload từng file lên backend bằng `curl -F`. Lệnh trả lỗi
    theo từng file (vượt giới hạn, là thư mục, không đọc được).
  - Giao diện ưu tiên lệnh Tauri khi có. Trên trình duyệt chỉ dán được ảnh, còn file thì kéo thả hoặc chọn.
- **Spike khi triển khai**: kiểm tra WKWebView của Tauri 2 trên macOS 14/15 có đưa `File` thật khi dán file từ Finder
  hay không. Có thì bỏ nhánh `osascript`.

## R11. Tìm tên file bằng ⌘F

- **Decision**:
  - Thêm nhóm `files` vào `services/search.py`, so khớp `attachments.display_name` bằng cách gập dấu/hoa thường như các
    nhóm hiện có (`fold_key`).
  - Bỏ mục đính kèm của task đang trong Thùng rác.
  - Kết quả gồm `{attachment_id, name, owner_type, owner_id, owner_title}`. Chọn kết quả thì điều hướng tới nơi gắn kèm
    `?attachment=<id>` để tô sáng.
  - Đánh chỉ mục: index biểu thức trên tên đã gập, dùng hàm `vn_fold` đã có trong CSDL từ feature 003, để đạt SC-009
    (1.000 file < 1 giây).

## R12. Buổi học bị xoá do sửa lịch môn, môn/buổi thi bị xoá

- **Decision**:
  - Trong `regenerate_sessions` (feature 004), trước khi xoá các buổi theo `plan.to_delete`: đổi `session_id` của mục
    đính kèm thuộc các buổi đó sang `subject_id` của môn, rồi thêm cảnh báo `attachments_moved` với số file vào
    `warnings` (FR-024).
  - Xoá môn hoặc buổi thi: API `DELETE` trả 409 `confirm_required` kèm `attachment_count` khi có file và chưa có
    `?confirm=true`. Giao diện hiện hộp xác nhận nêu số file.
  - Nhập lại lịch thi từ ảnh: buổi thi trùng bị bỏ qua (hành vi sẵn có), nên file giữ nguyên.

## R13. Hoàn tác "Xong" trên bảng

- **Decision**:
  - `PATCH /tasks/{id}/board` khi chuyển sang `done` trả kèm `undo`: `{status, board_rank}` trước khi chuyển và
    `next_task_id` nếu task lặp sinh lần kế tiếp.
  - Nút "Hoàn tác" gọi lại `PATCH /tasks/{id}/board` với trạng thái và vị trí cũ. Bỏ Xong dùng `uncomplete_task` sẵn
    có, hàm này đã gỡ lần kế tiếp chưa bị sửa (FR-019 của 003).
- **Rationale**: Dùng lại đúng luồng hoàn thành/bỏ hoàn thành, nên SC-004 đúng theo cách xây dựng.

## R14. Giao diện và phong cách

- Nút chuyển dạng xem "Danh sách / Bảng" là nút phân đoạn trong thanh đầu trang Công việc, nhớ bằng `localStorage`
  (khoá `lichhoc.tasks.view`); bộ lọc bảng lưu ở khoá `lichhoc.board.filters`.
- Thẻ bảng dùng lại thành phần hiển thị của `TaskRow`: chấm màu nhãn, `formatDue`, dấu Quan trọng. Thêm biểu tượng kẹp
  giấy và số file.
- Mục "File đính kèm" là một thành phần dùng chung `AttachmentsSection(ownerType, ownerId)` đặt trong `TaskDetailPanel`,
  form/chi tiết môn học, `SessionDetail`, chi tiết buổi thi. Mục có vùng thả, nút "Thêm file", danh sách (biểu tượng
  theo loại, tên, dung lượng "2,4 MB", ngày thêm) và menu ⋯ gồm Mở/Xem, Tải về, Đổi tên, Xoá.
- Cài đặt có mục mới "File đính kèm" (slug `file-dinh-kem`).

## R15. Thứ tự làm

1. Trạng thái + thứ tự task, API bảng (backend).
2. Giao diện bảng + bàn phím.
3. Lọc + thông tin thẻ.
4. Lưu file (volume, blob, upload, tải về, xem trước).
5. Gắn vào task/môn/buổi/buổi thi.
6. Thùng rác, dọn, xoá.
7. Sao lưu format 2.
8. Tìm kiếm.
9. Cài đặt.
10. Lệnh Tauri (mở, tải về, dán).

Kanban và đính kèm độc lập nhau (chỉ có số file trên thẻ là chung), nên sau bước 1–3 có thể làm song song.
