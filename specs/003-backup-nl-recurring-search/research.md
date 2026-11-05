# Research — Feature 003

Mỗi mục: **Quyết định** · **Lý do** · **Phương án đã cân nhắc**. Kiến trúc giữ nguyên theo yêu cầu: Flask +
PostgreSQL 16 trong Docker, agent Python trên Mac (launchd), frontend React, app Tauri 2.

---

## R1. Ai thực hiện sao lưu và dữ liệu đi đường nào

**Quyết định**: Agent trên Mac (`LichHocAgent`, đã chạy nền qua launchd) điều phối sao lưu. Backend tạo file
dump bằng `pg_dump` rồi trả qua `GET /api/backup/dump` (localhost); agent ghi file vào thư mục đích. Khôi phục
thì ngược lại: agent đọc file, gửi lên `POST /api/backup/restore`, backend chạy `pg_restore`.

**Lý do**: Container không thấy iCloud Drive hay `/Volumes/...` của máy; agent chạy cả khi app Tauri đã thoát
(FR-002), đã có vòng lặp, cơ chế thử lại và file log (`~/Library/Logs/LichHocAgent/agent.log`, FR-010a).
`pg_dump` qua backend giữ nguyên quy ước "chỉ backend nói chuyện với CSDL" và chỉ dùng kết nối localhost
(constitution IV).

**Đã cân nhắc**: mount thư mục iCloud vào container (không đổi được thư mục lúc chạy, SSD tháo ra làm hỏng
mount, Docker Desktop/OrbStack không theo dõi được file iCloud chưa tải); agent tự chạy `pg_dump` (CSDL
không mở cổng ra máy — cố ý theo constitution IV, mở cổng chỉ để sao lưu là không đáng); app Tauri làm sao
lưu (không chạy khi app đã thoát).

## R2. `pg_dump` trong image backend

**Quyết định**: Cài `postgresql-client-16` từ kho apt chính thức của PostgreSQL (PGDG) trong
`backend/Dockerfile`. Dùng định dạng custom (`-Fc`, đã nén).

**Lý do**: Image `python:3.12-slim` (Debian bookworm) chỉ có client 15, mà `pg_dump` phải cùng hoặc mới hơn
server 16. Internet chỉ cần lúc build image (như PyTorch, EasyOCR hiện tại).

**Đã cân nhắc**: dump bằng SQL tự viết (mất ràng buộc, sequence; dễ sai); chuyển backend sang image Alpine
(phá build EasyOCR/PyTorch).

## R3. Định dạng file sao lưu

**Quyết định**: Một file `.lhbackup` là file ZIP (không nén lại, chế độ `STORED`) gồm:
- `manifest.json`: `format: 1`, `created_at` (ISO, giờ Việt Nam), `kind` (`tu-dong` | `thu-cong` |
  `truoc-khoi-phuc`), `schema_revision` (revision Alembic), `app_version`, `dump_sha256`, `dump_size`,
  số lượng từng loại bản ghi (để hiện và để test SC-002).
- `data.dump`: kết quả `pg_dump -Fc`.

Tên file: `LichHoc-YYYY-MM-DD-HHMM-<kind>.lhbackup` (ví dụ `LichHoc-2026-11-05-2100-tu-dong.lhbackup`); trùng
tên (đồng hồ bị chỉnh lùi, hai bản trong cùng phút) thì thêm `-2`, `-3`… — không bao giờ ghi đè.

**Lý do**: Manifest cho biết phiên bản dữ liệu (từ chối bản mới hơn app, nâng cấp bản cũ hơn), loại bản và
checksum mà không phải đọc dump. ZIP mở được bằng Finder nếu cần cứu dữ liệu thủ công; `STORED` vì dump đã nén.

**Đã cân nhắc**: chỉ file `.dump` trần (không có loại bản, phiên bản schema → khó từ chối bản không tương
thích); JSON xuất từng bảng (phải tự viết và duy trì cho mọi bảng mới — dễ quên, trái FR-001).

## R4. Ghi an toàn và kiểm tra bản sao lưu

**Quyết định**: Backend chạy `pg_dump` vào file tạm trong container, kiểm tra bằng `pg_restore --list`, đóng
gói ZIP, tính SHA-256 của cả file và trả kèm header `X-Backup-Sha256`, `X-Backup-Name`. Agent ghi vào
`<thư mục đích>/.LichHoc-…lhbackup.partial`, `fsync`, đọc lại tính SHA-256, khớp thì `os.replace` sang tên
thật; không khớp thì xoá file tạm và coi là thất bại. File `.partial` của app cũ hơn 1 ngày bị dọn.

**Lý do**: FR-005 / SC-004 — bản dở dang không bao giờ có tên hợp lệ. `os.replace` trong cùng thư mục là
nguyên tử trên APFS và trên ổ rời exFAT/APFS. Đọc lại sau ghi bắt được lỗi ổ đĩa.

## R5. Lịch sao lưu, sao lưu bù và thử lại

**Quyết định**: Mỗi vòng lặp của agent (long-poll tối đa 25 giây) gọi hàm thuần
`backup_due(now, schedule_time, enabled, last_success_at, last_attempt_at) -> bool`:
- `slot` = thời điểm `schedule_time` gần nhất ≤ `now` (hôm nay hoặc hôm qua);
- đến hạn khi `enabled` và (`last_success_at` trống hoặc < `slot`) và (`last_attempt_at` trống hoặc
  `now − last_attempt_at ≥ 4 phút`).

Không có hàng đợi theo ngày → lỡ nhiều ngày vẫn chỉ một bản bù (FR-003). Mac ngủ/tắt: vòng lặp chạy lại ngay
khi thức (long-poll hết hạn hoặc lỗi mạng → thử lại sau ≤ 30 giây lúc đầu), nên bản bù trong vòng 5 phút.

**Lý do**: Một hàm thuần, test được mọi trường hợp (đúng giờ, ngủ qua giờ, tắt 3 ngày, đổi giờ, đồng hồ lùi)
mà không cần launchd `StartCalendarInterval` (launchd chỉ chạy bù một lần sau khi thức nhưng không biết về
SSD tháo hay backend chưa chạy).

**Lưu ý**: Backoff khi backend chưa chạy hiện tối đa 5 phút → giảm `RETRY_MAX` xuống 120 giây để giữ SC-001
"trong vòng 5 phút".

## R6. Thư mục đích, iCloud Drive và quyền truy cập file

**Quyết định**:
- Thư mục mặc định: `~/Library/Mobile Documents/com~apple~CloudDocs/Lịch Học Cá Nhân/Sao lưu`. Agent chỉ tự
  tạo thư mục mặc định, và chỉ khi `com~apple~CloudDocs` tồn tại (iCloud Drive đang bật). Thư mục người dùng
  chọn mà không tồn tại → coi là "không có" (SSD đã tháo), không tự tạo.
- Agent là app không sandbox; macOS (TCC) sẽ hỏi quyền một lần khi agent lần đầu ghi vào iCloud Drive hoặc
  ổ rời. `PermissionError` → trạng thái lỗi "Chưa được cấp quyền ghi vào thư mục sao lưu. Mở Cài đặt hệ
  thống → Quyền riêng tư & Bảo mật → Tệp và thư mục, bật cho LichHocAgent."
- File chỉ có trên iCloud (đã bị macOS "tối ưu dung lượng", hiện là `.Tên.lhbackup.icloud`): danh sách vẫn
  hiện với nhãn "Trên iCloud"; khi khôi phục, agent gọi
  `NSFileManager.startDownloadingUbiquitousItemAtURL_error_` rồi chờ tối đa 5 phút (FR edge case "Đang tải
  bản sao lưu từ iCloud…").

**Lý do**: Đúng ngoại lệ 2 của constitution IV — app chỉ ghi file vào thư mục, macOS lo đồng bộ iCloud.

**Đã cân nhắc**: API CloudKit/ubiquity container riêng của app (cần tài khoản developer, kết nối ra ngoài do
app khởi tạo — trái constitution).

## R7. Giao diện ↔ agent: lệnh "Sao lưu ngay", "Khôi phục" và danh sách bản

**Quyết định**: Backend là trung gian (agent không mở cổng):
- Giao diện tạo **việc sao lưu** (`backup_jobs`: `backup_now` hoặc `restore` kèm đường dẫn file); backend
  `bump_revision` để long-poll của agent trả về ngay; `GET /sync/changes` thêm `backup_jobs_pending`.
- Agent lấy việc (`POST /backup/jobs/claim`), làm, báo kết quả (`PUT /backup/jobs/{id}`).
- Agent gửi **báo cáo thư mục** (`PUT /backup/agent-report`): thư mục có/không, lỗi, danh sách bản hợp lệ
  (tên, loại, thời điểm, dung lượng, trên máy/trên iCloud), lần thử và lần thành công gần nhất. Gửi sau mỗi
  lần sao lưu/xoá/khôi phục và mỗi 60 giây cùng heartbeat hiện có.
- Giao diện đọc `GET /backup/status` (poll 2 giây khi có việc đang chạy, nếu không thì 30 giây).

**Lý do**: Dùng lại đúng kênh long-poll + heartbeat hiện có; không thêm cổng, không thêm tiến trình.

## R8. Khôi phục trọn vẹn và an toàn

**Quyết định**: Trình tự do agent điều phối (FR-012):
1. Tạo bản `truoc-khoi-phuc` như sao lưu thường — thất bại thì dừng.
2. Với bản trên iCloud: tải về (R6). Đọc manifest; kiểm tra SHA-256 của `data.dump`.
3. Gửi file lên `POST /api/backup/restore`. Backend: từ chối nếu `schema_revision` không có trong thư mục
   migrations (bản mới hơn app) → 409 `backup_too_new`; bật **chế độ bảo trì** (file cờ
   `/tmp/lichhoc-restoring`, mọi API khác trả 503 `restoring` — giao diện hiện "Đang khôi phục dữ liệu…");
   giữ lại trong bộ nhớ các bảng không khôi phục (R9); `engine.dispose()`; chạy
   `pg_restore --clean --if-exists --single-transaction --no-owner --exit-on-error`; nếu bản cũ hơn thì chạy
   `flask db upgrade`; ghi lại các bảng không khôi phục; đặt `sync_state.revision = max(cũ, mới) + 1`; tắt
   chế độ bảo trì. Nếu `flask db upgrade` lỗi: trả 500 `upgrade_failed` (vẫn ở chế độ bảo trì cho tới khi
   agent xử lý xong); agent tự khôi phục lại bản `truoc-khoi-phuc` vừa tạo (cùng phiên bản schema nên không
   cần nâng cấp) rồi đánh job `failed` "Không nâng cấp được dữ liệu của bản sao lưu cũ; dữ liệu đã được đưa
   về như trước khi khôi phục." — giữ đúng FR-012(d).
4. `--single-transaction` → lỗi giữa chừng thì PostgreSQL huỷ toàn bộ, dữ liệu cũ còn nguyên (FR-012d).

Sau khôi phục, agent đồng bộ toàn phần Lịch/Lời nhắc (`force=True`) — FR-013.

**Đã cân nhắc**: khôi phục vào database tạm rồi đổi tên database (phải ngắt mọi kết nối, cần quyền tạo DB,
phức tạp hơn mà `--single-transaction` đã cho tính trọn vẹn); `pg_restore` không transaction (có thể để lại
dữ liệu nửa vời — trái FR-012).

## R9. Những gì không đi theo bản sao lưu

**Quyết định**: `pg_dump --exclude-table-data` cho `backup_config`, `backup_status`, `backup_jobs`,
`agent_status`. Khôi phục giữ nguyên giá trị hiện tại của các bảng này.

**Lý do**: Khôi phục bản cũ không được làm đổi thư mục đích/giờ sao lưu hay xoá trạng thái việc đang chạy
(chính việc khôi phục đang được theo dõi qua `backup_jobs`).

## R10. Thông báo macOS khi quá 3 ngày chưa sao lưu

**Quyết định**: Agent gửi thông báo qua `UNUserNotificationCenter` (thêm `pyobjc-framework-UserNotifications`).
Để nhận sự kiện bấm vào thông báo, agent chạy vòng lặp sự kiện Cocoa trên luồng chính
(`PyObjCTools.AppHelper.runConsoleEventLoop`) và chuyển vòng lặp đồng bộ + sao lưu hiện có sang một luồng nền.
Bấm thông báo → agent chạy `open "lichhoc://cai-dat/sao-luu"`; app Tauri (plugin deep-link, scheme `lichhoc`)
mở cửa sổ và điều hướng webview tới `http://127.0.0.1:8080/cai-dat/sao-luu`.

Hàm thuần `stale_notice_due(now, last_success_at, enabled_since, notified_for)`: gửi khi
`now − (last_success_at ?? enabled_since) > 3 ngày` và chưa gửi cho mốc `last_success_at` đó (FR-008: một
lần, chỉ gửi lại sau khi có bản thành công mới). Agent nhớ `notified_for` trong `state.json`.

Không được cấp quyền thông báo → chỉ cảnh báo trong app, ghi log.

**Rủi ro**: chuyển agent sang hai luồng — làm một spike nhỏ ở đầu đợt 1 (EventKit gọi từ luồng nền, nhận
click thông báo). Nếu spike thất bại: dùng `osascript -e 'display notification'` (không mở được Cài đặt khi
bấm) và ghi lệch spec vào Complexity Tracking.

**Đã cân nhắc**: app Tauri gửi thông báo (không chạy khi đã thoát); thông báo qua Lời nhắc của Apple (lẫn vào
dữ liệu người dùng, cần đồng bộ bật).

## R11. Chọn thư mục / file trong app Tauri

**Quyết định**: Thêm ba lệnh Rust: `pick_backup_folder() -> Option<String>`, `pick_backup_file() ->
Option<String>` (lọc `.lhbackup`), `reveal_in_finder(path)` (chỉ nhận đường dẫn tuyệt đối tới thư mục hoặc
file `.lhbackup`). Dùng `tauri-plugin-dialog` **từ phía Rust**; capability mới `backup.json` chỉ cấp đúng ba
lệnh này cho origin `http://127.0.0.1:8080` (`remote.urls`). Giao diện gọi qua `desktopBridge.ts`; mở trong
trình duyệt thường (không có Tauri) thì hiện ô nhập đường dẫn thay cho nút chọn.

**Lý do**: Feature 002 cố ý không cấp quyền IPC nào cho trang tải từ backend; cấp đúng ba lệnh hẹp giữ nguyên
tinh thần đó. Không cấp quyền plugin dialog/shell trực tiếp cho trang.

## R12. Bộ hiểu câu tiếng Việt (thêm nhanh)

**Quyết định**: Viết riêng bằng TypeScript, hàm thuần chạy trong trình duyệt:
`parseQuickAdd(text, ctx) -> QuickParse` trong `frontend/src/features/tasks/quickParse/`.
- **Chuẩn hoá**: so khớp trên bản gập (`foldVi`: NFD, bỏ dấu, `đ→d`, chữ thường) nhưng giữ bảng ánh xạ vị trí
  về chuỗi gốc để tô sáng đúng ký tự.
- **Nhận diện bằng bảng mẫu có thứ tự** (dài trước ngắn): mỗi mẫu là biểu thức trên từ đã gập, có ranh giới
  từ (FR-029). Loại: `date`, `time`, `daypart`, `recurrence`, `tag`, `list`, `important`, `priority`. Cụm ghép
  được nhận như một khối ("thứ 6 tuần sau", "9 giờ tối", "thứ 2 và thứ 5 hàng tuần", "tối nay").
- **Giải nghĩa** riêng (`resolve.ts`): từ các cụm → `due_date`, `due_time`, `recurrence`, theo FR-028 và
  Clarifications (giờ 1–5 là chiều, ghép giờ với ngày mặc định của danh sách đang xem).
- **Huỷ hiểu**: `ctx.dismissed` là tập khoá `kind:start:text`; khoá mất hiệu lực khi chữ tại vị trí đó đổi
  (FR-031).
- **Tiêu đề**: bỏ các khoảng đã hiểu, gộp khoảng trắng, bỏ dấu câu thừa ở hai đầu (FR-032).
- **Cờ `recurrence`**: tắt ở đợt 2, bật ở đợt 4 (khi đó mới có task lặp). Khi tắt, cụm lặp không được nhận
  (giữ là chữ).

**Kiểm thử**: bộ test lớn dạng bảng (`quickParse.cases.ts`, mục tiêu ≥ 400 ca) chia nhóm: ngày, thứ, tuần sau,
DD/MM(/YYYY), giờ các dạng, buổi, giờ 1–5, ghép giờ với ngày mặc định, nhãn/danh sách (có/không dấu, có
khoảng trắng qua gợi ý), Quan trọng, ưu tiên, lặp, không dấu, hoa/thường, ranh giới từ ("maintain", "Lab 3",
"Mai" là tên người), nhiều cụm cùng loại, ngày không hợp lệ, huỷ hiểu, tiêu đề rỗng. Mọi ca cố định
`now = 2026-11-05T10:00` (Thứ Năm). Thêm vài test bất biến: tiêu đề không bao giờ chứa khoảng đã hiểu; parse
một chuỗi 300 ký tự < 2 ms (SC-005 cần < 100 ms cả vòng render).

**Đã cân nhắc**: thư viện chrono/date-parsing (không hỗ trợ tiếng Việt, khó tuỳ biến); làm ở backend (phải gọi
API mỗi phím, khó đạt 0,1 giây và tô sáng tức thì).

## R13. Ô nhập có tô sáng

**Quyết định**: Giữ `<input>` thật (để gõ tiếng Việt bằng bộ gõ macOS, chọn chữ, ⌘Z hoạt động tự nhiên), đặt
một lớp "gương" phía sau cùng font/padding hiển thị chữ với các `<mark>` tô nền; chữ của input trong suốt
màu nền, con trỏ giữ màu. Bấm vào vùng tô sáng: tính vị trí ký tự từ `selectionStart` sau click, nếu nằm trong
một cụm thì huỷ hiểu cụm đó. Gợi ý `#`/`~` là popover Radix đã có. Đang soạn chữ bằng bộ gõ (IME
composition) thì không parse lại để tránh nhảy tô sáng.

**Đã cân nhắc**: `contentEditable` (lỗi với bộ gõ tiếng Việt, khó giữ con trỏ); thư viện editor (nặng, trái
nguyên tắc III).

## R14. Tạo nhãn mới từ câu

**Quyết định**: `POST /api/tasks` nhận thêm `tag_names: string[]`; backend so khớp tên nhãn bằng khoá gập dấu
+ chữ thường, chưa có thì tạo nhãn (màu mặc định), trong cùng transaction với task (FR-035).

**Đã cân nhắc**: frontend gọi `POST /tags` rồi `POST /tasks` (hai bước, có thể để lại nhãn thừa khi lỗi).

## R15. Tìm kiếm không dấu

**Quyết định**: Migration bật extension `unaccent` (có sẵn trong `postgres:16-alpine`; user `lichhoc` là
superuser của container) và tạo hàm `vn_fold(text)` `IMMUTABLE` = `lower(public.unaccent('public.unaccent',
$1))`. Truy vấn: mỗi từ khoá đã gập phải `LIKE '%từ%'` trên `vn_fold` của chuỗi ghép các trường được tìm
(FR-038). Không cần index: ~1.000 task + 1 học kỳ quét tuần tự < 50 ms. Bộ quy tắc `unaccent` mặc định đã có
`đ→d`, `Đ→D`.

Tô sáng làm ở frontend bằng `foldVi` (R12) với bảng ánh xạ vị trí; có test đối chiếu bảng chữ tiếng Việt đầy
đủ (134 ký tự có dấu) giữa `vn_fold` (test tích hợp) và `foldVi` (Vitest) để hai bên cho cùng kết quả.

**Đã cân nhắc**: cột chuẩn hoá lưu sẵn cho 6 loại đối tượng (phải cập nhật ở mọi chỗ ghi, dễ lệch; chỉ đáng
khi dữ liệu lớn); full-text search `tsvector` (tách từ, không khớp được tiền tố giữa chữ như "nop ba").

## R16. Mô hình task lặp

**Quyết định**: Bảng mới `task_series` giữ quy tắc + **mẫu** (template JSONB: tiêu đề, ghi chú, danh sách, ưu
tiên, Quan trọng, nhắc, nhãn, giờ hạn, khung giờ làm tương đối). `tasks` thêm `series_id`, `occurrence_no`,
`spawned_from_task_id`, `trash_scope`. Mỗi chuỗi có đúng một **lần hiện tại** — bảo đảm bằng unique index
một phần `tasks(series_id) WHERE completed_at IS NULL AND deleted_at IS NULL` (chống trùng khi bấm hoàn thành
liên tiếp — edge case). Lần dự kiến chỉ tính ra từ quy tắc (không lưu).
- Hoàn thành → tạo lần kế tiếp từ **mẫu** (không phải từ lần vừa xong — để "Chỉ lần này" không lan sang lần
  sau); ngày = `next_due(rule, after=hạn lần vừa xong, not_before=hôm nay, due_time, now)` (FR-017).
- Bỏ hoàn thành → xoá lần kế tiếp nếu `spawned_from_task_id` khớp và `user_modified = false` (dùng lại cột
  có sẵn, nghĩa mở rộng: "đã bị người dùng sửa từ khi được tạo tự động") — FR-019.
- "Lần này và các lần sau" → cập nhật lần hiện tại và mẫu; đổi ngày thì `shift_rule` (FR-020a).
- Xoá: `trash_scope = 'this'` (lần kế tiếp được tạo ngay) hoặc `'following'` (`task_series.stopped_at`).
  Khôi phục `this` → `series_id = NULL` (thành task thường); `following` → `stopped_at = NULL` (FR-025).

Hàm thuần trong `backend/app/services/task_recurrence.py` (tên khác `recurrence.py` của buổi học):
`occurrences(rule, start, end)`, `next_due(...)`, `shift_rule(rule, old_date, new_date)`, `is_finished(...)`.
Frontend có `describeRule(rule)` (chuỗi tiếng Việt cho tooltip, FR-021) và trình chỉnh quy tắc.

**Lý do**: Spec chọn mô hình "một lần hiện tại" (Assumptions) → task thật chỉ một, mọi danh sách thông minh,
đếm, nhắc, đồng bộ Lời nhắc và tìm kiếm **không phải sửa** (chúng đã làm việc trên task). Chỉ lịch và bản tóm
tắt cần thêm lần dự kiến.

**Đã cân nhắc**: chuỗi RRULE (RFC 5545) + thư viện `dateutil.rrule` (biểu diễn thừa sức, khó kiểm "ngày 31 →
cuối tháng" theo spec, khó `shift_rule`; hàm tự viết cho 4 kiểu ngắn hơn và test rõ hơn); sinh trước nhiều
lần thành task thật (trái mô hình spec, làm bẩn danh sách và Lời nhắc).

## R17. Lịch và bản tóm tắt với lần dự kiến

**Quyết định**: `services/calendar.py` thêm mục `kind: "projected_task"` cho mỗi lần dự kiến trong khoảng đang
xem (bỏ ngày trùng lần hiện tại; giới hạn 400 mục/khoảng); `toCalendarEvents` vẽ khối mờ có biểu tượng lặp,
không kéo được, bấm mở lần hiện tại. `services/digest.py` gộp lần dự kiến vào bản tóm tắt của mỗi ngày tới;
mọi thay đổi chuỗi đã `bump_revision` nên agent tự cập nhật các bản tóm tắt đã tạo sẵn (FR-023).

## R18. API sửa/xoá task lặp

**Quyết định**: `PATCH /api/tasks/{id}` và `DELETE /api/tasks/{id}` nhận `scope: "this" | "following"`. Task
có `series_id` mà thiếu `scope` (và không chỉ sửa trường `recurrence`) → 409 `scope_required`; giao diện hỏi
"Chỉ lần này / Lần này và các lần sau / Huỷ" rồi gửi lại. Kéo thả trên lịch dùng cùng cơ chế.

## R19. Thứ tự triển khai

**Quyết định** (theo yêu cầu): Đợt 1 sao lưu & khôi phục (US1, US2, FR-001…FR-014) → Đợt 2 thêm nhanh tự nhiên
(US4, trừ phần lặp) → Đợt 3 tìm kiếm (US5) → Đợt 4 task lặp (US3) + bật cụm lặp trong thêm nhanh. Mỗi đợt kết
thúc bằng `./scripts/test.sh` pass, commit, hướng dẫn thử tiếng Việt.
