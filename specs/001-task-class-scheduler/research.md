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

**Kết quả spike trên ảnh THẬT (2026-11-05)** — `backend/spikes/real_spike.py`, 2 ảnh thật (bảng "Lịch
thi cá nhân" 2344×816 và lưới tuần 2672×1336), 8 ô nhìn thấy đủ, so từng từ trong vùng của ô:

| Cỡ ảnh đưa vào OCR | Đúng nguyên văn | Đúng gần đúng (≥ 80%/từ) | Thời gian |
|--------------------|-----------------|--------------------------|-----------|
| ×1.0 (nguyên cỡ)   | 5/8 = 62,5%     | 6/8 = 75%                | 19–39 giây |
| ×1.5               | 8/8 = 100%      | 8/8 = 100%               | 28–57 giây |
| ×2.0               | 7/8 = 87,5%     | 5/8 = 62,5%              | 31–42 giây |

Kết luận: vượt ngưỡng 80%. **Phóng ảnh lên cạnh dài ~3600 px (tối đa ×1.5)**, KHÔNG thu nhỏ ảnh về
2560 px như dự kiến ban đầu (ảnh 2672 px thu về 2560 px chỉ đạt 62,5%) — xem `ocr/preprocess.py`.
Lỗi thường gặp trên ảnh thật: chữ trắng trên nền màu (tiêu đề ô) đọc kém, "Tiết" thành "Tlết", ":"
thành "."/"-", "60p" thành "6Op", O↔0 trong mã lớp, mất dấu ("báo" thay "bảo"); đã có xử lý trong
`ocr/fields.py` (ưu tiên tên môn ở thân ô, chuẩn hoá giờ, sửa O↔0) và bảng xem trước để người dùng sửa.

**Spike cần làm (đã làm ở trên)**: chạy EasyOCR trên 3–5 ảnh chụp thật từ cổng thông tin của người dùng, đo độ
chính xác ký tự và thời gian. Nếu tên môn sai dấu quá nhiều, thử thêm tham số `decoder='beamsearch'`
và tiền xử lý (phóng to ×1.5, tăng tương phản) trước khi bàn đến phương án khác.

**Kết quả spike S1 (T010, 2026-11-04)**

> ⚠️ **Đo trên 3 ảnh GIẢ LẬP** (`samples/synthetic/`, xem README trong đó), vì chưa có ảnh chụp thật.
> Kết luận dưới đây là tạm thời và **phải kiểm chứng lại bằng ảnh thật trước khi làm US6**.

- **Cách đo**: script `backend/spikes/ocr_spike.py` chạy trong image backend với `--network none`.
  Model nạp trong 2 giây với `download_enabled=False`, chứng tỏ chạy offline được.
  - Lần 1: tìm chuỗi đúng y nguyên trong kết quả OCR.
  - Lần 2 (`--parsed`): gom khối theo ô (cột lấy từ tiêu đề "Thứ 2…CN"), rồi chuẩn hoá các lỗi có quy
    luật: `:` đọc thành `.`, mất dấu `-` giữa hai giờ, `N01` đọc thành `NO1`, đối chiếu giờ với ca và
    tiết. Tên môn **không** được sửa dấu.

| Ảnh | OCR (giây) | Buổi đúng mọi trường | Giờ | Mã lớp | Phòng | GV | Tên môn |
|-----|-----------:|---------------------:|----:|-------:|------:|---:|--------:|
| sample-01 (2880×1800 PNG) | 38–54 | **7/9 (77.8%)** | 100% | 100% | 100% | 100% | 77.8% |
| sample-03 (2880×1800 JPEG q70) | 40–64 | **5/6 (83.3%)** | 100% | 100% | 100% | 100% | 83.3% |
| sample-02 (1440×900, phóng to ×2) | 54 | **0/7 (0%)** | 100% | 42.9% | 57.1% | 14.3% | 42.9% |

- **Ảnh Retina**: tổng 12/15 = **80%** buổi đúng hoàn toàn, vừa chạm mục tiêu SC-011. Mọi lỗi còn
  lại nằm ở **tên môn**: sai dấu ("thống" → "thông") hoặc mất dấu gạch ("Mác - Lênin" → "Mác Lênin").
  Độ tin cậy OCR của các chữ sai dấu vẫn cao (> 0.8), nên **ngưỡng tin cậy 0.6 không bắt được loại
  lỗi này**.
- **Ảnh màn hình thường 1440×900**: không đạt.
  - Không phóng to thì tiêu đề "Thứ 2/3/4" bị đọc thành "Thứ", nên không xác định được cột.
  - Phóng to ×2 thì xác định được cột và giờ đúng 100% (nhờ đối chiếu tiết/ca), nhưng dấu tiếng Việt
    sai nhiều: "Kiến" → "Kiên", "Kỹ năng mềm" → "Kỹ năng mêm", "ThS." → "TnS_".
- **Tháng/năm**: tiêu đề lịch thu nhỏ ("Tháng 11/2026") đọc đúng ở mọi lần chạy. Ngày giờ trên thanh
  menu đọc được nhưng dấu `:` thành `.` (ví dụ "Th 2 9 thg 11 08.30"), nên cần regex chấp nhận cả hai.
- **Cấu hình**: `decoder='beamsearch'` không cải thiện mà chậm hơn. Phóng to ×1.5 + tăng tương phản
  không giúp với ảnh Retina; chỉ cần cho ảnh < 2000 px.
- **Thời gian**: 38–64 giây mỗi ảnh (CPU, OrbStack, Apple Silicon). Giới hạn 60 giây trong plan **có
  lúc bị vượt** (sample-03 lần đầu: 63.5 giây).
- **Image backend**: 2.46 GB. Model CRAFT 83 MB + latin_g2 15 MB nằm sẵn trong image.

**Quyết định tạm thời**: **giữ EasyOCR** cho US6, kèm các điều kiện sau. Chưa chuyển sang Apple
Vision; sẽ xem lại sau khi có ảnh thật.
1. Đưa các quy tắc chuẩn hoá đã chứng minh hiệu quả vào `ocr/fields.py` và `ocr/layout.py` (T096,
   T097):
   - Giờ chấp nhận `[:.*,]` làm dấu phân cách; bỏ qua dấu `-` bị mất.
   - Nếu giờ đọc lệch ca nhưng tiết đọc được thì tin tiết, và đánh dấu chưa chắc chắn.
   - Sửa `N[O0]\d` thành `N0\d` và `[A-Z]{3}[I1l]\d{3}` thành `[A-Z]{3}1\d{3}` trong mã lớp.
   - Tiêu đề cột chấp nhận cả dạng mất dấu hoặc dính chữ ("Thu2", "Thứ2").
2. Ảnh rộng < 2000 px: phóng to ×2 trước khi OCR, và hiện cảnh báo "Ảnh độ phân giải thấp, hãy kiểm
   tra kỹ tên môn và giảng viên".
3. Lỗi dấu ở tên môn không bị ngưỡng tin cậy bắt được. Để vẫn "dễ phát hiện" theo SC-011, bảng xem
   trước (T099 `preview.py`, T103 giao diện) cần:
   - So khớp gần đúng với tên môn đã có (đã có trong kế hoạch).
   - Đánh dấu chưa chắc chắn khi cùng một môn (cùng mã lớp) xuất hiện nhiều lần nhưng tên đọc ra khác
     nhau.
4. Tăng tốc để giữ dưới 60 giây: chỉ OCR vùng lưới tuần, lịch thu nhỏ và thanh menu, sau khi tìm tiêu
   đề cột ở lượt nhận diện nhanh đầu tiên.
5. **Bắt buộc**: chạy lại `ocr_spike.py --parsed` trên 3–5 ảnh thật trước khi bắt đầu US6. Nếu ảnh
   thật cho < 80%, thử Apple Vision qua mac-agent (phương án dự phòng bên dưới) và so sánh trên cùng bộ
   ảnh.

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

**Quyết định**: Dùng **Python 3.11 (Homebrew, dạng framework) + PyObjC
(`pyobjc-framework-EventKit`)**, đóng gói bằng
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

**Kết quả spike S2 (T011, 2026-11-04)**: `mac-agent/spikes/eventkit_spike.py`, đóng gói thành
`LichHocSpike.app` (py2app, ký ad-hoc), chạy bằng `open` trên macOS 26.7.1 (Apple Silicon).

- ✅ **Phía Mac đạt**:
  - Xin quyền đầy đủ cho Lịch và Lời nhắc thành công. Hộp thoại hiện câu giải thích tiếng Việt lấy từ
    Info.plist.
  - Tạo được lịch và danh sách lời nhắc "Lịch Học Cá Nhân (spike)" trong nguồn **iCloud**.
  - Lưu được `EKEvent` có `EKAlarm` báo trước tương đối và `EKReminder` có `dueDateComponents` + alarm
    tuyệt đối; `commit_()` thành công.
  - Đọc lại được sự kiện theo `URL = lichhoc://spike/session/1`, tức cách đối chiếu bằng `sync_key`
    qua trường URL là khả thi.
  - **Kết luận: giữ Python + PyObjC, không cần chuyển sang Swift.**
- ✅ **iPhone đạt** (người dùng kiểm tra trên máy thật, 2026-11-04):
  - Lần 1: sự kiện báo trước 5 phút, tạo lúc 04:02 cho 04:12. Sự kiện đồng bộ sang iPhone kèm cảnh
    báo "Trước 5 phút", nhưng **không có thông báo**, nhiều khả năng vì đồng bộ đến sau giờ báo
    (04:07).
  - Lần 2: tạo lúc 04:11 một sự kiện 04:27 và một lời nhắc hạn 04:27, cả hai báo lúc 04:22. Cả hai
    **hiện trên iPhone lúc 04:12** (iCloud đồng bộ khoảng 1 phút), và **có thông báo lúc 04:22**.
  - Kết luận: chuỗi ứng dụng → EventKit → iCloud → iPhone hoạt động, thông báo đúng giờ (SC-017).
    Một lời nhắc chỉ đến được iPhone nếu đồng bộ xong **trước** giờ báo. Feed của agent đã ghi trước
    mọi buổi còn lại của học kỳ, nên trường hợp thông thường không bị ảnh hưởng. Riêng buổi học hoặc
    task tạo sát giờ (trong khoảng 1–2 phút trước giờ báo) có thể không kịp nhắc trên iPhone. Đây là
    giới hạn của iCloud, cần ghi vào README.
- **Phát hiện cần đưa vào T136 (`calendar_store.py`) và T138 (`install.sh`)**:
  1. **Nguồn Lời nhắc khác nguồn Lịch.** Tạo danh sách lời nhắc trong cùng nguồn CalDAV với Lịch bị lỗi
     `EKErrorDomain Code=24 "That account does not support reminders"`. Phải lấy nguồn từ
     `defaultCalendarForNewReminders().source()`.
  2. **py2app không chạy với Python do uv cài** (bản standalone: `zlib` không có `__file__`). Cần Python
     dạng framework (Homebrew hoặc python.org). **Quyết định (người dùng chọn): mac-agent dùng Homebrew
     `python@3.11`** (`/opt/homebrew/opt/python@3.11/bin/python3.11`; đã kiểm chứng với PyObjC 13 và
     py2app 0.28.10). `requires-python = ">=3.11,<3.12"`. Backend vẫn dùng Python 3.12 trong Docker.
  3. **py2app báo `install_requires is no longer supported`** khi thư mục chạy build có
     `pyproject.toml` khai báo `[project].dependencies`. `install.sh` phải build từ một thư mục tạm
     không có pyproject (spike build trong `mac-agent/spikes/`).
  4. **Build lại chưa chắc làm macOS hỏi lại quyền.** Lần chạy thứ ba (build và ký ad-hoc lại) xong
     trong 11 giây mà không hỏi lại quyền. 108 giây của lần thứ hai nhiều khả năng là thời gian người
     dùng bấm hộp thoại. Rủi ro này chưa được xác nhận, nhưng README vẫn nên dặn: nếu bị hỏi lại quyền
     sau khi cập nhật agent thì bấm "Cho phép".
- **Dọn dữ liệu spike**: `open -a mac-agent/spikes/dist/LichHocSpike.app --args --cleanup` xoá lịch và
  danh sách "(spike)". Đã chạy lúc 04:22; xoá thành công cả hai.

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

## R14. Lịch thi: nhận biết loại ảnh và phân tích bảng lịch thi

**Quyết định**:
- **Nhận biết loại ảnh** (FR-059) trong `ocr/layout.py`, chấm điểm theo từ khoá tiêu đề:
  - Lưới tuần: ≥ 5 tiêu đề "Thứ 2…CN" xếp ngang.
  - Bảng lịch thi: ≥ 3 trong các tiêu đề "Mã học phần", "Tên học phần", "Lần thi", "Ngày thi", "Giờ
    thi", "Ca thi", "Hình thức thi", "Phòng thi", "SBD/Số báo danh" trên cùng một hàng; và cột ngày có
    giá trị `dd/mm/yyyy` đầy đủ.
  - Không đạt cả hai, hoặc đạt cả hai → `kind = "unknown"`, giao diện hỏi người dùng chọn loại.
- **Phân tích bảng** (`ocr/exam_table.py`):
  - Hàng tiêu đề xác định khoảng x của từng cột. Các khối chữ bên dưới gán vào cột theo tâm x và gom
    thành hàng theo y; ô nhiều dòng (tên học phần dài, xuống dòng) được ghép.
  - Ánh xạ tiêu đề → trường theo từ điển đồng nghĩa (ví dụ "Giờ thi"/"Thời gian"/"Ca thi" →
    `start_time`, `end_time`), so khớp mờ (rapidfuzz ≥ 85) để chịu lỗi OCR mất dấu.
  - Giờ: `HH:MM - HH:MM`, hoặc một giờ bắt đầu cộng thời lượng lấy từ "Hình thức thi" (`(\d+)\s*(p|phút)`).
    Không suy ra được giờ kết thúc → `certain=false`.
- **Bảo vệ thông tin sinh viên** (FR-061): cột có tiêu đề khớp "Họ tên", "Họ và tên", "Mã SV", "Mã sinh
  viên", "Ngày sinh", "Lớp" bị **loại bỏ ngay sau khi phân tích bố cục**, trước khi tạo bất kỳ trường
  nào. Khối chữ trong các cột đó không được ghi log và không có trong phản hồi API. Test kiểm tra
  phản hồi không chứa các giá trị này.
- **Đã qua** (FR-062): `end_at < now()` → `is_past = true`, `selected = false`.

**Lý do**: Bảng lịch thi có cấu trúc đơn giản hơn lưới tuần (ngày đầy đủ, mỗi dòng một buổi), nên
dùng chung OCR và pipeline nhưng tách bộ phân tích riêng để dễ đọc và dễ test. Loại bỏ cột cá nhân
ngay ở bước bố cục là cách chắc chắn nhất để dữ liệu đó không lọt ra ngoài.

**Kiểm chứng**: thêm 1–2 ảnh bảng lịch thi **giả lập** vào `samples/synthetic/` (có cột họ tên, mã SV
bịa, có môn đã qua, có môn thiếu phòng, có "Trắc nghiệm trên máy 60p" không ghi giờ kết thúc) và chạy
lại `ocr_spike.py --parsed` cho loại ảnh này. Kết quả **phải kiểm chứng lại bằng ảnh thật**, như R2.

**Phương án đã cân nhắc**: dùng chung bộ phân tích dạng danh sách của lịch học: bố cục cột khác
nhiều, gộp sẽ làm code khó đọc và khó bảo đảm loại bỏ cột cá nhân.

---

## Tổng hợp: không còn mục NEEDS CLARIFICATION

Mọi mục trong Technical Context đã có quyết định. Còn hai SPIKE (R2: độ chính xác EasyOCR; R4:
quyền EventKit qua PyObjC). Mỗi spike có phương án dự phòng, và được đặt làm task đầu tiên khi
triển khai.

---

## R15. Thông báo tổng hợp hằng ngày trên iPhone khi Mac gập

**Quyết định**: Mỗi bản tóm tắt là một **sự kiện cả ngày** trong lịch "Lịch Học Cá Nhân"
(`sync_key = digest:YYYY-MM-DD`, `URL = lichhoc://digest/YYYY-MM-DD`) với một `EKAlarm` thời điểm
tuyệt đối lúc `daily_digest_time`. Nội dung tóm tắt nằm ở `title` (một dòng, hiện trong thông báo),
chi tiết nằm ở `notes`. Backend sinh bản tóm tắt cho hôm nay và 13 ngày tới trong feed; ngày trống
không có mục. Agent đối chiếu như các mục khác (fingerprint), nên huỷ buổi, hoàn thành task hay đổi
giờ tổng hợp đều cập nhật ngay. Agent tự đồng bộ toàn phần khi sang ngày mới để cửa sổ 14 ngày trượt
và bản của ngày đã qua bị xoá.

**Lý do**:
- Mac có thể gập lúc 05:00, nên không thể để agent hay trình duyệt tự phát thông báo đúng lúc; chỉ
  mục đã ghi sẵn trong Lịch/iCloud mới chắc chắn báo trên iPhone (cùng lý do với R5).
- Sự kiện cả ngày nằm ở dải "cả ngày", không chiếm chỗ trong lưới giờ, và tự trôi vào quá khứ, không
  cần người dùng đánh dấu xong như lời nhắc.
- 14 ngày đủ cho kỳ nghỉ ngắn khi Mac gập; nhiều hơn làm feed lớn và số task quá hạn ở ngày xa kém
  chính xác.

**Phương án đã cân nhắc**:
- Lời nhắc (`EKReminder`) mỗi ngày: phải tick hoàn thành, làm đầy danh sách lời nhắc.
- Sự kiện có giờ 05:00–05:05: chen vào lưới giờ mỗi ngày.
- Thông báo cục bộ từ agent (`UNUserNotificationCenter`): không chạy khi Mac ngủ, không tới iPhone.

**Cần kiểm chứng khi làm (T159)**: thông báo của sự kiện cả ngày trên iPhone hiện đủ tiêu đề dài
(khoảng 100–150 ký tự); nếu bị cắt, rút gọn tiêu đề (bỏ phòng, chỉ giữ ca + tên môn).

---

## R16. Mức "Quan trọng" và nhiều mốc nhắc

**Quyết định**:
- Cột `is_important` cho `tasks`, `subjects` (áp dụng cho mọi buổi), `exams` (mặc định `true`), và
  `class_sessions.important_override` (nullable) để đặt riêng một buổi, giống cách giữ ngoại lệ giờ
  và phòng.
- Mốc nhắc là danh sách phút, tính bằng một hàm thuần duy nhất (data-model "Quy tắc mốc nhắc"), dùng
  chung cho feed và nhắc trình duyệt. Feed đã gửi `alarms_minutes_before` dạng danh sách cho sự kiện;
  lời nhắc đổi `alarm_at` thành `alarms_at` (danh sách), nên agent và backend phải nâng cấp cùng lúc.
- Task quan trọng chỉ có ngày: nhắc lúc `date_only_task_reminder_time` của ngày hạn và của các ngày
  ứng với mốc ≥ 1 ngày, vì "3 giờ trước 23:59" không có nghĩa với task không có giờ.
- Hiển thị nổi bật: dấu ★ và viền đậm trong lịch và trang Hôm nay; trong Lịch Apple dùng tiền tố
  "★ " ở tiêu đề sự kiện và `priority = 1` cho lời nhắc.

**Lý do**: Một hàm tính mốc giúp test dễ và tránh lệch giữa iPhone và trình duyệt. Đặt cờ ở môn kèm
ghi đè ở buổi tránh phải bật từng buổi trong 15 tuần.

**Cần kiểm chứng khi làm (T159)**: EventKit cho thêm nhiều `EKAlarm` vào một sự kiện/lời nhắc và
iPhone báo đủ cả 5 mốc (ứng dụng Lịch trên iPhone chỉ hiện 2 ô "Thông báo" khi sửa tay, nhưng mục tạo
bằng EventKit có thể có nhiều hơn). Nếu iPhone chỉ báo 2 mốc đầu, giới hạn mục quan trọng ở 2 mốc
trong sự kiện và ghi thêm các mốc còn lại thành lời nhắc riêng, rồi cập nhật contract.

**Phương án đã cân nhắc**: dùng `priority` sẵn có của task làm "quan trọng": không áp dụng cho buổi
học và buổi thi, và trộn hai ý nghĩa khác nhau (thứ tự làm việc và mức nhắc).

