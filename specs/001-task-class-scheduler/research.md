# Research: Lịch Học Cá Nhân

**Feature**: `001-task-class-scheduler` | **Date**: 2026-11-04 | **Plan**: [plan.md](plan.md)

Mỗi mục ghi: **Quyết định**, **Lý do**, **Phương án đã cân nhắc**. Các mục đánh dấu **SPIKE** là
rủi ro kỹ thuật cần kiểm chứng bằng code thử ngay đầu giai đoạn triển khai, trước khi xây phần
phụ thuộc vào chúng.

---

## R1. Kiến trúc tổng thể và giới hạn localhost

**Quyết định**: Docker Compose chạy trên OrbStack với 3 service `db` (PostgreSQL), `backend`
(Flask + gunicorn), `web` (bản build React/Vite phục vụ bằng nginx, đồng thời reverse proxy `/api`
sang backend). Thêm một tiến trình `mac-agent` chạy trực tiếp trên macOS (ngoài Docker). Chỉ
service `web` mở cổng ra máy, và chỉ trên `127.0.0.1:8080`. `db` và `backend` chỉ nằm trong mạng
nội bộ của Compose; agent gọi backend qua `http://127.0.0.1:8080/api`.

**Lý do**:
- Đúng kiến trúc người dùng chọn; gom giao diện và API về cùng một origin nên không cần CORS.
- Gắn cổng vào `127.0.0.1` đảm bảo không máy nào khác trong mạng LAN truy cập được (Nguyên tắc IV:
  chỉ kết nối nội bộ localhost).
- `restart: unless-stopped` để các container tự chạy lại khi OrbStack khởi động cùng máy.

**Phương án đã cân nhắc**:
- Chạy Vite dev server làm service `web`: chậm khởi động, không hợp dùng hằng ngày. Giữ làm
  `docker-compose.dev.yml` tuỳ chọn cho lúc phát triển.
- App macOS gốc (SwiftUI + SQLite): khớp nền tảng nhất nhưng người dùng đã chọn kiến trúc Docker +
  web.

---

## R2. Nhận diện ảnh offline bằng EasyOCR — **SPIKE**

**Quyết định**:
- EasyOCR 1.7.x với `Reader(['vi', 'en'], gpu=False)`. Model detector (CRAFT) và recognizer (latin)
  được tải trong bước build Docker vào `/opt/easyocr-models`. Lúc chạy, dùng
  `download_enabled=False` và `model_storage_directory=/opt/easyocr-models`, nên không bao giờ gọi
  mạng.
- PyTorch bản CPU (cài từ index CPU của PyTorch, có wheel cho linux/arm64 trên Apple Silicon) để
  image nhỏ hơn.
- Reader được nạp một lần cho mỗi tiến trình (lazy singleton), có khoá để chỉ một yêu cầu OCR chạy
  cùng lúc. Gunicorn chạy 1 worker × 4 thread, timeout 120 giây cho endpoint nhận diện.
- Ảnh HEIC chuyển sang RGB bằng `pillow-heif`. Ảnh lớn hơn 2560px ở cạnh dài được thu nhỏ trước
  khi OCR, để tăng tốc mà vẫn đọc được chữ của ảnh chụp màn hình Retina.
- Ảnh chỉ xử lý trong bộ nhớ, không ghi xuống đĩa và không lưu vào database (FR-035).

**Lý do**: EasyOCR hỗ trợ tiếng Việt có dấu và chạy offline. Tải model lúc build giữ đúng FR-025
và FR-029: lúc chạy không cần internet.

**Rủi ro và cách giảm**:
- Độ chính xác dấu tiếng Việt của EasyOCR ở mức trung bình, nên mục tiêu 80% (SC-011) có rủi ro.
  Cách giảm:
  (a) Sửa tên môn bằng so khớp gần đúng (rapidfuzz) với tên môn đã có trong học kỳ.
  (b) Chuẩn hoá giờ theo bảng ca (FR-041).
  (c) Ô có độ tin cậy OCR < 0.6 bị đánh dấu "chưa chắc chắn".
  (d) Bảng xem trước là bước bắt buộc.
- Thời gian OCR một ảnh toàn màn hình trên CPU dự kiến 5–20 giây. Giao diện hiện trạng thái "Đang
  nhận diện..." và không chặn thao tác khác.
- Kích thước image backend lớn (~1.5–2 GB do PyTorch). Chấp nhận được với máy cá nhân.

**Spike cần làm**: chạy EasyOCR trên 3–5 ảnh chụp thật từ cổng thông tin của người dùng, đo độ
chính xác ký tự và thời gian. Nếu tên môn sai dấu quá nhiều, thử thêm tham số `decoder='beamsearch'`
và tiền xử lý (phóng to ×1.5, tăng tương phản) trước khi bàn đến phương án khác.

**Phương án đã cân nhắc**:
- Tesseract với gói `vie`: nhẹ hơn, nhưng thường kém hơn với chữ trên giao diện web và khó lấy bố
  cục ổn định.
- Apple Vision (VNRecognizeTextRequest) trong mac-agent: hỗ trợ tiếng Việt và chạy offline, nhưng
  không chạy được trong container. Giữ làm phương án dự phòng nếu spike EasyOCR thất bại (agent nhận
  ảnh qua localhost và trả về các khối chữ).
- Dịch vụ AI trực tuyến: bị constitution cấm.

---

## R3. Ghép khối chữ thành buổi học (phân tích bố cục)

**Quyết định**: Pipeline gồm các hàm thuần (pure function), mỗi bước kiểm thử riêng được:

1. **OCR → `TextBox`** (text, toạ độ khung, độ tin cậy).
2. **Lọc vùng thừa**: bỏ thanh menu macOS ở dải trên cùng (nhưng giữ lại để đọc ngày giờ hệ thống),
   thanh tab và thanh địa chỉ trình duyệt, Dock. Vùng thời khoá biểu được xác định bằng cụm tiêu đề
   cột "Thứ 2 … Chủ nhật/CN".
3. **Nhận dạng bố cục**:
   - *Lưới tuần*: có ≥ 5 tiêu đề thứ xếp ngang. Mỗi cột là một thứ; ngày dạng `dd/mm/yyyy` dưới
     tiêu đề (nếu có) gán ngày cho cột.
   - *Danh sách*: có tiêu đề cột kiểu "Môn học / Thứ / Tiết / Phòng". Mỗi hàng là một buổi.
4. **Gom khối thành ô buổi học**: trong mỗi cột, gom các khối chữ gần nhau theo chiều dọc
   (khoảng cách < 1.2 × chiều cao dòng) thành một ô.
5. **Trích trường bằng regex và từ khoá**:
   - Giờ: `\d{1,2}[:hg]\d{2}\s*[-–]\s*\d{1,2}[:hg]\d{2}`.
   - Ca: `Ca\s*\d`. Tiết: `Tiết\s*\d+\s*[-–]\s*\d+`.
   - Phòng: `Phòng|P\.` hoặc mẫu `[A-Z]\d{1,2}[.-]?\d{2,3}`.
   - Giảng viên: `GV|Giảng viên`. Mã lớp: chuỗi chữ-số dài, ví dụ `INT1234_01`.
   - E-Learning: chứa `E-Learning|Elearning|Online` (FR-046).
   - Tên môn: dòng còn lại dài nhất.
6. **Xác định tháng/năm** (FR-031), theo thứ tự ưu tiên:
   (1) ngày `dd/mm/yyyy` nằm trong lưới;
   (2) tiêu đề tuần/tháng, ví dụ "Tuần 10 (04/11/2026 - 10/11/2026)";
   (3) lịch tháng thu nhỏ, ví dụ "Tháng 11 2026";
   (4) ngày giờ trên thanh menu macOS, ví dụ "Th 4 4 thg 11 14:05".
   Ghi lại nguồn đã dùng. Nếu các nguồn mâu thuẫn, chọn nguồn ưu tiên cao hơn và đánh dấu chưa chắc
   chắn.
7. **Đối chiếu ca** (FR-041): lệch ≤ 5 phút so với ca hoặc dãy ca liền nhau thì gán ca.
8. **Kiểm tra chéo**: ngày không khớp thứ thì đánh dấu, không tự sửa.
9. **Phát hiện trùng** (FR-034) với database và giữa các dòng trong cùng ảnh.

**Lý do**: Tách thành các hàm nhỏ giúp code dễ đọc (Nguyên tắc I) và cho phép test từng bước bằng
dữ liệu `TextBox` dựng tay, không cần chạy OCR (test nhanh). Bộ test end-to-end với ảnh mẫu chạy OCR
thật được đánh dấu `@pytest.mark.ocr`.

**Phương án đã cân nhắc**: mô hình học sâu hiểu bố cục (LayoutLM, Donut): nặng, cần train và không
cần thiết với định dạng cổng thông tin khá cố định.

---

## R4. Tiến trình nhắc trên Mac: Python + PyObjC hay Swift — **SPIKE**

**Quyết định**: Dùng **Python 3.12 + PyObjC (`pyobjc-framework-EventKit`)**, đóng gói bằng
**py2app** thành `LichHocAgent.app` (app ẩn, `LSUIElement=true`, không có icon trên Dock). Chuyển
sang Swift nếu spike thất bại.

**Lý do khả thi**:
- PyObjC bọc đầy đủ EventKit (`EKEventStore`, `EKEvent`, `EKReminder`, `EKAlarm`, `EKCalendar`).
- Từ macOS 14, việc xin quyền dùng `requestFullAccessToEventsWithCompletion_` và
  `requestFullAccessToRemindersWithCompletion_`. Hệ thống quyền riêng tư (TCC) yêu cầu tiến trình có
  `Info.plist` khai báo `NSCalendarsFullAccessUsageDescription` và
  `NSRemindersFullAccessUsageDescription`.
- Một script Python chạy trần (`python agent.py`) không có Info.plist, nên trên macOS 14+ yêu cầu
  quyền có thể bị từ chối âm thầm. Vì vậy **bắt buộc đóng gói thành .app** bằng py2app với
  Info.plist tuỳ chỉnh và ký ad-hoc (`codesign -s -`).
- Dùng chung ngôn ngữ Python với backend, giữ dự án một ngôn ngữ phía máy chủ.

**Rủi ro**: Mỗi lần build lại, chữ ký ad-hoc đổi, nên macOS có thể hỏi lại quyền. Chấp nhận được
với app cá nhân; ghi chú trong README.

**Spike cần làm**: build .app tối thiểu, xin quyền, tạo một sự kiện có báo trước trong lịch iCloud,
kiểm tra sự kiện hiện trên iPhone. Nếu không đạt sau 1 ngày, chuyển sang Swift (Swift Package,
executable + Info.plist), giữ nguyên hợp đồng API ở [contracts/calendar-sync.md](contracts/calendar-sync.md).

**Phương án đã cân nhắc**:
- Swift: hợp nền tảng nhất nhưng thêm ngôn ngữ thứ hai. Là phương án dự phòng.
- AppleScript/JXA qua `osascript`: chậm, khó đặt báo trước cho Lời nhắc, khó kiểm thử.
- Xuất file `.ics` hoặc lịch đăng ký qua URL: iPhone không truy cập được localhost của Mac và không
  tự cập nhật.

---

## R5. Cơ chế đồng bộ backend → Lịch/Lời nhắc

**Quyết định**: Đồng bộ kiểu **trạng thái mong muốn + đối chiếu (reconcile)**, kích hoạt bằng
**long-poll**:

- Backend có một bộ đếm `sync_revision`, tăng trong cùng transaction với mọi thay đổi ảnh hưởng tới
  buổi học, task, nhắc hay cài đặt.
- Agent gọi `GET /api/sync/changes?after=<rev>&wait=25`. Backend trả ngay nếu đã có revision mới,
  nếu chưa thì chờ tối đa 25 giây. Gần như tức thì (SC-018) mà không cần đẩy từ backend.
- Khi có revision mới, agent gọi `GET /api/sync/feed`, nhận toàn bộ danh sách mục cần có: buổi học
  từ hôm nay đến hết học kỳ còn lại, và task chưa hoàn thành có hạn chót. Mỗi mục có `sync_key` ổn
  định (ví dụ `session:123`, `task:45`) và `fingerprint` (hash nội dung).
- Agent đối chiếu với các mục trong lịch "Lịch Học Cá Nhân" và danh sách lời nhắc "Lịch Học Cá
  Nhân". Khoá được lưu trong trường `URL` của mục (`lichhoc://session/123`), fingerprint lưu trong
  một file JSON cục bộ của agent. Cụ thể: thêm mục thiếu, sửa mục lệch fingerprint, xoá mục thừa.
- Ghi theo lô, `commit` một lần mỗi vòng. Agent báo trạng thái về `PUT /api/sync/agent-status`
  (quyền, lần đồng bộ cuối, lỗi) để giao diện hiển thị.

**Lý do**: Đối chiếu toàn phần là idempotent và tự sửa sai: nếu người dùng tự sửa hoặc xoá mục
trong Lịch thì lần sau sẽ được ghi đè hoặc tạo lại (edge case trong spec). Khối lượng nhỏ (~100 sự
kiện + ~50 lời nhắc), nên mỗi vòng chỉ tốn vài trăm mili giây.

**Chi tiết**:
- Buổi học → `EKEvent` với một `EKAlarm(relativeOffset = -phút×60)`.
- Task → `EKReminder` có `dueDateComponents` và `EKAlarm` theo thời điểm tuyệt đối.
- Lịch được tạo trong nguồn iCloud (`EKSourceTypeCalDAV` có tiêu đề "iCloud"). Nếu không có nguồn
  iCloud, tạo lịch cục bộ và báo trạng thái `no_icloud` để giao diện cảnh báo rằng iPhone sẽ không
  nhận được.
- Mỗi buổi học là một sự kiện riêng, không dùng quy tắc lặp của Lịch, để các ngoại lệ (huỷ, đổi
  giờ) đơn giản.
- Khi đồng bộ tắt: agent xoá lịch và danh sách lời nhắc nó đã tạo (FR-054), rồi chờ.
- Khi backend không chạy (OrbStack tắt): agent thử lại sau 30 giây → 5 phút. Các mục đã ghi vẫn
  còn, nên iPhone vẫn nhắc.

**Phương án đã cân nhắc**:
- Gửi từng thay đổi (event log): phức tạp hơn và dễ lệch khi mất sự kiện.
- Backend chủ động đẩy tới agent: agent phải mở cổng nghe, thêm bề mặt tấn công.
- Hỏi định kỳ (polling) mỗi 60 giây: không đạt "ngay khi lưu".

---

## R6. Tự chạy agent khi đăng nhập

**Quyết định**: Một LaunchAgent `~/Library/LaunchAgents/vn.lichhoc.agent.plist` với
`RunAtLoad=true`, `KeepAlive=true`, chạy file thực thi trong `LichHocAgent.app`. Script
`mac-agent/scripts/install.sh` cài và gỡ (`launchctl bootstrap/bootout gui/$UID`). Log ghi ra
`~/Library/Logs/LichHocAgent/agent.log`, xoay vòng 1 MB × 3 file.

**Lý do**: Là cơ chế chuẩn của macOS. `KeepAlive` tự khởi động lại agent nếu nó bị lỗi.

**Phương án đã cân nhắc**: `SMAppService` (login item hiện đại) cần app ký bằng Developer ID để ổn
định. Login Items thủ công thì phải thao tác tay.

---

## R7. Nhắc dự phòng bằng trình duyệt (khi chưa bật đồng bộ)

**Quyết định**: Frontend có module `reminders/` chỉ chạy khi `calendar_sync_enabled = false`:
- Mỗi 5 phút gọi `GET /api/reminders/upcoming?hours=24` và đặt hẹn giờ trong trang.
- Dùng Web Locks API (`navigator.locks.request('lichhoc-reminders')`) để chỉ một tab làm "tab
  chính" phát thông báo. Thêm `Notification.tag = sync_key` để hệ thống tự gộp thông báo trùng.
- Khi tab mở lại, bỏ qua các nhắc đã quá giờ hơn 1 phút: không hiện dồn (FR-021).
- Xin quyền bằng một nút có giải thích tiếng Việt, không tự bật hộp thoại xin quyền khi vừa tải
  trang.

**Lý do**: Notification API chỉ hoạt động khi trang đang mở, đúng phạm vi dự phòng. Web Locks có
sẵn trong Safari, Chrome và Firefox hiện tại.

**Phương án đã cân nhắc**: Service Worker + Push API: cần máy chủ push trên internet, bị
constitution cấm.

---

## R8. Mô hình buổi học: lưu sẵn từng buổi hay tính khi cần

**Quyết định**: **Lưu sẵn (materialize)** mỗi buổi học thành một dòng `class_sessions`. Khi môn
học thay đổi, hàm `regenerate_sessions(subject)` tính lại tập ngày mong muốn:
- Thêm buổi mới.
- Xoá buổi không còn trong khoảng, nếu chưa có ngoại lệ.
- Cập nhật giờ và phòng cho buổi chưa sửa riêng.
- Giữ nguyên buổi có ngoại lệ (đã huỷ, đã sửa giờ hoặc phòng). Nếu buổi đó rơi ra ngoài khoảng mới,
  báo cho người dùng trước khi xoá.

**Lý do**: Truy vấn lịch theo khoảng ngày, trang Hôm nay, phát hiện trùng, task tự tạo và đồng bộ
đều cần buổi học cụ thể có ID ổn định. Khối lượng nhỏ (~100 buổi mỗi học kỳ). Logic sinh buổi nằm
trong một hàm thuần, dễ test 100% (SC-003).

**Phương án đã cân nhắc**: lưu quy tắc lặp (RRULE) và bảng ngoại lệ, tính khi đọc: tiết kiệm dòng
nhưng mọi truy vấn phức tạp hơn, và ID buổi học không ổn định cho task tự tạo và sync_key.

---

## R9. Quy tắc tự tạo deadline

**Quyết định**: Service `auto_deadlines.reconcile(session_ids | subject_id | all_future)` là hàm
đối chiếu có tính quyết định (deterministic), gọi sau mọi thay đổi buổi học, môn học, nhãn hoặc cài
đặt, trong cùng transaction:

- `eligible(session)` khi thoả tất cả:
  - Buổi không bị huỷ.
  - Môn không chứa từ khoá ngoại lệ: so sánh không phân biệt hoa thường, sau chuẩn hoá Unicode NFC.
  - Môn hoặc buổi có nhãn hệ thống `E-Learning`, **hoặc** giờ bắt đầu ≥ mốc giờ.
- `due_at(session)` = thời điểm Chủ Nhật đầu tiên lúc `deadline_time` *sau* `session.end_at`,
  theo giờ Asia/Ho_Chi_Minh.
- Bảng trạng thái theo từng buổi học:

| Trạng thái hiện có | Thoả điều kiện, hạn chưa qua | Không thoả điều kiện |
|---|---|---|
| Chưa có task, `auto_task_suppressed = false` | Tạo task | — |
| Có task tự tạo, chưa sửa, chưa hoàn thành | Cập nhật tiêu đề/hạn nếu lệch | Xoá task |
| Task đã sửa hoặc đã hoàn thành | Không đụng | Không đụng |
| `auto_task_suppressed = true` (người dùng đã xoá) | Không tạo lại | — |

- Mọi thao tác sửa task tự tạo qua API (trừ chỉ đánh dấu hoàn thành) đặt `user_modified = true`.

**Lý do**: Một hàm đối chiếu duy nhất dễ test theo bảng trên (SC-015) và tránh lỗi khi nhiều đường
sửa dữ liệu khác nhau.

---

## R10. Thời gian, múi giờ, định dạng tiếng Việt

**Quyết định**:
- Database lưu `timestamptz`, ngày dạng `date`, giờ ca dạng `time`. Các container đặt
  `TZ=Asia/Ho_Chi_Minh`, backend dùng `zoneinfo`.
- API trả ISO 8601 có offset (`2026-11-16T07:30:00+07:00`).
- Frontend định dạng bằng `Intl.DateTimeFormat('vi-VN', …)` cộng một hàm `formatThu()` cho dạng
  "Thứ Hai, 16/11/2026". Lịch dùng locale `vi`, tuần bắt đầu Thứ Hai, giờ 24h.

**Lý do**: Một múi giờ cố định cho người dùng ở Việt Nam. ISO có offset tránh lệch giờ giữa
backend, trình duyệt và agent.

---

## R11. Thư viện frontend

**Quyết định**:
- React 18 + TypeScript + Vite.
- **FullCalendar 6** (gói `@fullcalendar/react`, `daygrid`, `timegrid`, `interaction`, giấy phép
  MIT, có locale `vi`) cho ba chế độ xem ngày/tuần/tháng.
- **TanStack Query** để tải dữ liệu và làm mới cache sau khi thay đổi.
- **React Router** để chuyển trang.
- CSS Modules với một bảng màu 12 màu cố định; không dùng UI kit lớn.
- Font hệ thống (`-apple-system`), không tải font từ CDN (Nguyên tắc IV).

**Lý do**: Tự viết lịch ngày/tuần/tháng có kéo thả, "+3" và chia khung giờ tốn nhiều công và dễ
lỗi. FullCalendar là lợi ích rõ ràng so với chi phí phụ thuộc (Ràng buộc bổ sung). TanStack Query
giảm code tự quản lý cache.

**Phương án đã cân nhắc**: `react-big-calendar` (phụ thuộc moment/date-fns localizer, bản địa hoá
kém hơn); tự viết (YAGNI ngược: quá nhiều công).

---

## R12. Lưu dữ liệu bền vững và sao lưu

**Quyết định**:
- PostgreSQL 16 với named volume `lichhoc_pgdata`. Mọi thao tác ghi đi qua transaction của
  SQLAlchemy; giữ mặc định `fsync=on` và `synchronous_commit=on` (Nguyên tắc V).
- Migration bằng Flask-Migrate (Alembic). Backend tự chạy `flask db upgrade` khi khởi động, sau khi
  database sẵn sàng (healthcheck `pg_isready`).
- Sao lưu: `scripts/backup.sh` chạy `docker compose exec -T db pg_dump -Fc` vào
  `./backups/lichhoc-YYYYmmdd-HHMM.dump`. Khôi phục: `scripts/restore.sh <file>` dùng `pg_restore
  --clean`.
- README ghi vị trí vật lý của volume trong OrbStack (`~/OrbStack/docker/volumes/lichhoc_pgdata`)
  và cảnh báo: `docker compose down -v` sẽ xoá dữ liệu.

**Lý do**: Đúng lựa chọn của người dùng. Named volume giữ dữ liệu qua `down`/`up` và khởi động lại
máy. `pg_dump` cho bản sao lưu nhất quán ngay cả khi app đang chạy.

**Phương án đã cân nhắc**: SQLite trong một bind mount: đơn giản hơn cho app một người dùng, nhưng
người dùng đã chọn PostgreSQL (xem Complexity Tracking trong plan).

---

## R13. Kiểm thử

**Quyết định**:
- **Backend (pytest)**:
  - `tests/unit`: hàm thuần (sinh buổi, ca, deadline, parser bố cục, phát hiện trùng, định dạng).
  - `tests/integration`: API với PostgreSQL thật, chạy bằng `docker compose run --rm backend
    pytest` trên database test riêng; mỗi test chạy trong transaction rồi rollback.
  - `tests/ocr`: ảnh mẫu trong `backend/tests/fixtures/timetables/*.png` kèm `*.expected.json`;
    chạy riêng bằng `pytest -m ocr`, vì chậm.
- **Agent (pytest)**: logic đối chiếu viết thuần trên dữ liệu giả lập; lớp EventKit được bọc sau
  interface `CalendarStore` để thay bằng bản giả trong bộ nhớ.
- **Frontend (Vitest + Testing Library)**: chỉ phần logic chính: lên lịch nhắc dự phòng, định dạng
  ngày tiếng Việt, bộ lọc nhãn.
- **Lint/format**: ruff (lint + format) cho Python; ESLint + Prettier cho TypeScript.

**Ảnh mẫu**: Cần 3–5 ảnh chụp màn hình thật từ cổng thông tin của người dùng. Che hoặc xoá thông tin
cá nhân (họ tên, mã sinh viên) trước khi commit. Bổ sung 2–3 ảnh tổng hợp do script Pillow vẽ (lưới
tuần chuẩn) để test ổn định.

---

## Tổng hợp: không còn mục NEEDS CLARIFICATION

Mọi mục trong Technical Context đã có quyết định. Còn hai SPIKE (R2: độ chính xác EasyOCR; R4:
quyền EventKit qua PyObjC). Mỗi spike có phương án dự phòng, và được đặt làm task đầu tiên khi
triển khai.
