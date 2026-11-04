# Research: Thiết kế lại giao diện và đóng gói app macOS

**Feature**: `002-redesign-macos-app` | **Date**: 2026-11-04 | **Plan**: [plan.md](plan.md)

Các quyết định dưới đây dựa trên chỉ dẫn lúc lập plan: giữ backend Flask + PostgreSQL trong Docker
và agent đồng bộ Lịch/Lời nhắc; frontend React + Vite thiết kế lại với Tailwind CSS và bộ component
gọn nhẹ; lịch dùng FullCalendar bản MIT; đóng gói bằng Tauri 2; chia thành các đợt nhỏ.

---

## R1. App Tauri là "vỏ" nạp giao diện từ 127.0.0.1:8080

**Quyết định**: App Tauri 2 (`desktop/`) có một cửa sổ. Lúc mở, cửa sổ hiện trang chờ đóng gói sẵn
trong app (`desktop/splash/index.html`, không cần mạng). Phần Rust kiểm tra `GET
http://127.0.0.1:8080/api/health` mỗi 2 giây; khi trả 200 thì điều hướng cửa sổ sang
`http://127.0.0.1:8080/` (giao diện React do nginx của service `web` phục vụ như hiện nay). Trình
duyệt vẫn mở được cùng địa chỉ để phát triển và dự phòng.

**Lý do**:
- Một bản build frontend duy nhất (trong Docker), không phải đóng gói lại app mỗi lần sửa giao diện;
  app gần như không cần build lại.
- Cùng origin với API (`/api` qua nginx) nên không cần mở CORS trên backend.
- Trang React không cần gọi lệnh Tauri (IPC), nên không phải cấp quyền cho trang tải từ địa chỉ
  ngoài app. Các việc của app (menu, kiểm tra kết nối, mở OrbStack) nằm hết ở phía Rust.
- Kiểm tra kết nối bằng `std::net::TcpStream` + một yêu cầu HTTP/1.1 tối giản, không thêm thư viện
  HTTP.

**Phương án đã cân nhắc**:
- Đóng gói frontend vào app và gọi API qua `http://127.0.0.1:8080/api`: phải bật CORS, phải build
  lại app mỗi khi sửa giao diện, và có hai nơi phục vụ frontend.
- Electron: nặng hơn nhiều (kèm Chromium), trái tinh thần gọn nhẹ của constitution III.
- Swift/WKWebView tự viết: ít phụ thuộc nhất nhưng phải tự làm menu, nhớ cửa sổ, một phiên bản app,
  icon; Tauri có sẵn các phần này.

**Cần kiểm chứng ở đợt 4 (spike nhỏ)**: WKWebView trong app Tauri nạp được `http://127.0.0.1` không
bị App Transport Security chặn (Tauri dev dùng `http://localhost` nên dự kiến được); nếu bị chặn thì
thêm `NSAppTransportSecurity → NSAllowsLocalNetworking = true` vào Info.plist của app.

**Kết quả kiểm chứng (T087, 2026-11-05)**: bản build release (`Lịch Học Cá Nhân.app`) mở được và
nạp `http://127.0.0.1:8080/` — log nginx của service `web` ghi các request `/api/...` kèm user agent
`LichHocDesktop`. App Transport Security **không** chặn nên **không cần** `Info.plist` riêng.

---

## R2. Khi backend chưa chạy: màn hình "Hãy mở OrbStack"

**Quyết định**:
- Trang chờ hiện "Hãy mở OrbStack" + giải thích ngắn, nút **Mở OrbStack** (Rust chạy `open -a
  OrbStack`) và **Thử lại** (kiểm tra ngay), cùng dòng trạng thái "Đang thử kết nối lại…".
- Các service trong `docker-compose.yml` đã có `restart: unless-stopped`, nên khi OrbStack mở thì
  `db`, `backend`, `web` tự chạy lại; app tự vào màn hình chính khi health check thành công
  (SC-001: trong vòng 5 giây sau khi backend sẵn sàng, vì chu kỳ kiểm tra là 2 giây).
- Mất kết nối khi đang dùng: giao diện React đã có xử lý lỗi; bổ sung một dải thông báo "Mất kết nối
  với dữ liệu trên máy — đang thử lại…" khi các truy vấn liên tục lỗi mạng, và TanStack Query tự thử
  lại khi kết nối trở lại.
- Giao tiếp trang chờ ↔ Rust: trang chờ được đóng gói trong app nên được phép gọi lệnh Tauri
  (`invoke('open_orbstack')`, `invoke('retry_now')`); quyền chỉ cấp cho cửa sổ chính khi đang ở
  nguồn nội bộ của app (capability gắn với `local: true`).

**Lý do**: Đúng chỉ dẫn lúc lập plan; không cần quyền điều khiển Docker từ app. Nút "Mở OrbStack"
chỉ mở một app trên máy, không kết nối ra ngoài (constitution IV).

**Phương án đã cân nhắc**: App tự chạy `docker compose up` — cần biết đường dẫn dự án và quyền chạy
lệnh shell từ app; phức tạp và dễ lỗi hơn mà lợi ích nhỏ vì OrbStack đã tự khởi động lại container.

---

## R3. Menu, phím tắt, cửa sổ

**Quyết định**:
- Menu macOS tạo ở phía Rust bằng API menu của Tauri 2, chữ tiếng Việt: "Lịch Học Cá Nhân" (Giới
  thiệu, Cài đặt… ⌘,, Ẩn ⌘H, Thoát ⌘Q), "Sửa" (Hoàn tác, Làm lại, Cắt, Chép, Dán, Chọn tất cả — dùng
  mục có sẵn của hệ thống), "Cửa sổ" (Thu nhỏ, Phóng to), "Trợ giúp" (Phím tắt ⌘/).
- Mục menu cần điều khiển trang (Cài đặt, Phím tắt) được thực hiện bằng `webview.eval(...)` gọi một
  hàm toàn cục do trang React đăng ký (`window.lichhoc?.navigate('/cai-dat')`,
  `window.lichhoc?.showShortcuts()`); không cần IPC từ trang.
- Phím tắt còn lại (⌘N, ⌘1…⌘5, Esc, ⌘⌫, ⌘↩, ↑/↓, ←/→, T, D/W/M) xử lý trong React bằng một hook nhỏ
  tự viết (`useHotkeys`), bỏ qua khi đang gõ trong ô nhập (trừ Esc, ⌘↩). Không thêm thư viện phím tắt.
- Nhớ kích thước/vị trí cửa sổ: `tauri-plugin-window-state`. Một phiên bản app:
  `tauri-plugin-single-instance` (mở lần hai thì đưa cửa sổ lên trước).
- Đóng cửa sổ không thoát app (bắt sự kiện đóng, ẩn cửa sổ; bấm icon Dock thì hiện lại); ⌘Q thoát.
  Thoát app không ảnh hưởng Docker và agent (FR-004).

**Quyết định T088 (2026-11-05)**: WKWebView không hỗ trợ `-webkit-app-region` và trang tải từ ngoài
không dùng được `data-tauri-drag-region`, nên với `titleBarStyle: "Overlay"` cửa sổ sẽ không kéo được.
Dùng `titleBarStyle: "Transparent"` + `hiddenTitle: true`: giữ thanh tiêu đề chuẩn (kéo được, ba nút
cửa sổ nằm trong thanh đó) nhưng trong suốt, nên `--titlebar-inset` giữ 0 và giao diện React không
cần sửa.

**Lý do**: Dùng sẵn tính năng của Tauri cho phần hệ điều hành; giữ trang React không phụ thuộc Tauri
để trình duyệt vẫn dùng được.

---

## R4. Tailwind CSS và bộ component gọn nhẹ

**Quyết định**:
- Tailwind CSS 4 qua plugin `@tailwindcss/vite`; định nghĩa bộ màu riêng của app bằng biến CSS
  (`--color-accent`, `--color-surface`, …) trong `@theme`, với giá trị cho chế độ tối đặt trong
  `@media (prefers-color-scheme: dark)`. Không có nút chọn giao diện trong app: theo macOS (FR-032).
- Component tự viết trong `frontend/src/ui/` (Button, IconButton, Checkbox, Switch, Input, Select,
  Badge, Toast, EmptyState, SidePanel), dùng Radix UI primitives chỉ cho các phần khó làm đúng khả
  năng truy cập: `@radix-ui/react-dialog` (hộp thoại, xác nhận), `@radix-ui/react-popover` (chọn
  ngày, chọn emoji gợi ý), `@radix-ui/react-dropdown-menu` (menu ⋯, chọn chế độ lịch),
  `@radix-ui/react-tooltip` (chú thích thanh biểu tượng).
- Biểu tượng: SVG nội tuyến tự vẽ trong `frontend/src/ui/icons.tsx` (khoảng 25 biểu tượng nét mảnh),
  không thêm thư viện icon.
- Màu nhấn của app: xanh lam ngọc (teal) đậm, khác màu thương hiệu của các app tham khảo; bảng 12 màu
  nhãn/môn hiện có (`c01`…`c12`) giữ mã, thêm biến thể "nhạt" (nền khối lịch) và "đậm" (chữ, viền)
  cho cả hai chế độ, kiểm tra tương phản 4.5:1 bằng test (R9).
- Font: font hệ thống macOS (`-apple-system`, SF Pro), không tải font ngoài.

**Lý do**: Tailwind cho phép giao diện nhất quán (khoảng cách, bo góc, màu qua token) mà không thêm
thư viện UI nặng; Radix headless nhỏ, không áp style, giải quyết focus/bàn phím/ARIA cho hộp thoại và
menu — đúng "bộ component gọn nhẹ" và constitution III.

**Phương án đã cân nhắc**: Thư viện UI đầy đủ (MUI, Chakra, Mantine): nặng và áp phong cách riêng
khó đổi. shadcn/ui: là mã chép vào dự án dựa trên Radix + Tailwind; ta làm tương tự nhưng chỉ chép
phần cần, tự viết cho gọn.

**Phiên bản**: chọn bản ổn định mới nhất đã phát hành ít nhất hai tuần tại thời điểm cài (ghi chính
xác trong `package.json`/`Cargo.toml` và `package-lock.json`/`Cargo.lock`).

---

## R5. Lịch: FullCalendar 6 (MIT) cấu hình theo spec

**Quyết định**: Giữ FullCalendar 6 với các plugin MIT đã dùng: `daygrid` (Tháng), `timegrid`
(Ngày/Tuần), `interaction` (kéo thả, kéo dãn, chọn vùng). Cấu hình:

| Yêu cầu | Cấu hình |
|---------|----------|
| Tuần bắt đầu Thứ Hai, tiếng Việt | `firstDay: 1`, `locale: vi` |
| Đầu trang riêng (tháng/năm, +, chế độ, trước/sau, Hôm nay) | `headerToolbar: false`; tự làm thanh đầu trang bằng component, gọi API của calendar (`prev`, `next`, `today`, `changeView`) |
| Hàng tên thứ trên hàng số ngày, số hôm nay tô tròn | `dayHeaderContent` tự render (T2…CN + số), class cho ngày hôm nay |
| Đường kẻ đỏ giờ hiện tại + nhãn giờ đỏ | `nowIndicator: true`, tô màu bằng CSS; nhãn giờ trong cột giờ bằng `nowIndicatorContent` |
| Hàng "Cả ngày" | `allDaySlot: true`, `allDayText: 'Cả ngày'` |
| Trùng giờ xếp cạnh nhau | `slotEventOverlap: false` |
| Khối màu nhạt có checkbox, tiêu đề, giờ, phòng | `eventContent` render component `CalendarBlock` |
| Kéo thả / kéo dãn / chọn vùng | `editable` theo từng sự kiện (`startEditable`, `durationEditable`), `selectable: true`, `snapDuration: '00:15'`, `eventDrop`, `eventResize`, `select` |
| Cuộn tới giờ hiện tại | `scrollTime` = giờ hiện tại − 1 giờ (tuần có hôm nay), ngược lại `06:00` |
| Lọc theo nhãn | giữ `TagFilter` hiện có (đặt trong cột bên), lọc ở truy vấn `/calendar?tags=` |
| Cột bên: lịch tháng nhỏ + lọc nhãn | component `CalendarSidebar` tự làm (không dùng FullCalendar thứ hai): lưới tháng từ hàm thuần `monthGrid(month)` (tuần bắt đầu Thứ Hai, 6 hàng), bấm ngày → `gotoDate`; tô hôm nay và khoảng đang xem; ẩn/hiện bằng nút ở đầu trang, nhớ trong `localStorage` |

Ánh xạ dữ liệu → sự kiện là hàm thuần `toCalendarEvents` (mở rộng bản hiện có) để test bằng Vitest;
ánh xạ kéo thả → PATCH là hàm thuần `dropToPatch(event, newStart, newEnd, allDay)` (data-model
"Quy tắc kéo thả").

**Lý do**: Đã dùng và test ở feature 001; mọi tính năng cần thiết đều nằm trong bản MIT (bản premium
chỉ thêm timeline/resource, không cần).

---

## R6. Thùng rác: xoá mềm bằng `deleted_at`

**Quyết định**: Cột `tasks.deleted_at timestamptz NULL`. Xoá = đặt `deleted_at = now()`; khôi phục =
`NULL`. Mọi truy vấn task thông thường lọc `deleted_at IS NULL` qua một hàm dùng chung
`active_tasks()` trong `services/tasks.py`; các chỗ đang truy vấn `Task` trực tiếp (today, calendar,
sync_feed, digest, reminders, auto_deadlines, task_lists đếm) chuyển sang dùng nó.
- Xoá hẳn tự động: hàm `purge_expired_trash(now)` xoá task có `deleted_at < now − 30 ngày`; gọi khi
  backend khởi động và ở đầu các request đọc danh sách (`/task-counts`, `/tasks?view=trash`,
  `/today`), và ở `/sync/feed` qua `purge_expired_trash_throttled(now)` (tối đa 1 lần/giờ, mốc lần chạy
  cuối giữ trong bộ nhớ của tiến trình backend). Agent gọi feed mỗi phút nên task quá hạn bị xoá trong
  vòng 1 giờ dù không mở app, đảm bảo SC-006; không cần tiến trình định kỳ riêng. Rẻ (một câu DELETE có
  index).
- Task tự tạo vào Thùng rác: đặt `class_sessions.auto_task_suppressed = true` như khi xoá hiện nay;
  `auto_deadlines.reconcile` bỏ qua task đã ở Thùng rác. Khôi phục: `deleted_at = NULL`,
  `auto_task_suppressed = false`, rồi reconcile buổi đó (task đã có nên không tạo mới).
- Khôi phục task có danh sách đã bị xoá: danh sách bị xoá dùng lựa chọn "xoá luôn các task" → các task
  vào Thùng rác với `list_id` vẫn trỏ danh sách cũ? Không được vì FK. Quyết định: khi xoá danh sách với
  `delete_tasks=true`, task được chuyển sang danh sách "Học tập" **và** vào Thùng rác, kèm cột
  `trashed_from_list_name text NULL` để khi khôi phục báo "Danh sách cũ "X" đã bị xoá, công việc được
  đưa về Học tập" (FR-031).
- Revision: đưa vào hoặc khôi phục từ Thùng rác đều `bump_revision` (agent xoá hoặc tạo lại lời
  nhắc).

**Lý do**: Đơn giản, giữ nguyên mọi quan hệ (nhãn, liên kết buổi học) nên khôi phục đủ 100% thông tin
(SC-006).

**Phương án đã cân nhắc**: Bảng `trash` riêng chứa bản sao JSON: khôi phục phức tạp hơn và dễ lệch
schema.

---

## R7. Khung giờ làm của task

**Quyết định**: Ba cột `tasks.work_date date`, `work_start time`, `work_end time`, cùng `NULL` hoặc
cùng có giá trị, `work_end > work_start` (CHECK). Không ảnh hưởng nhắc, feed đồng bộ, quá hạn, bản
tóm tắt hay deadline tự tạo (FR-019). Danh sách thông minh và `/calendar` xét thêm `work_date`.
Sửa khung giờ làm của task tự tạo cũng đặt `user_modified = true` như mọi trường khác (quy tắc hiện
có của feature 001).

**Lý do**: Ba cột rõ nghĩa, dễ ràng buộc; khung giờ trong một ngày đúng spec (không vắt qua nửa đêm).

---

## R8. Dời buổi học sang ngày khác

**Quyết định**: Cột `class_sessions.original_date date NULL`: `NULL` = chưa dời; có giá trị = buổi đã
dời, `date` là ngày mới. "Đã dời" là một loại ngoại lệ:
- `ExistingSession` (hàm thuần sinh lại buổi, research R8 của feature 001) dùng **ngày khoá**
  `original_date ?? date` để khớp với ngày sinh ra từ quy tắc lặp, và `has_exception` gồm cả
  `original_date IS NOT NULL`. Vì vậy sửa lịch chung của môn không sinh lại buổi tại ngày gốc, và buổi
  đã dời được giữ (hoặc báo xung đột 409 nếu ngày gốc nằm ngoài khoảng mới, như ngoại lệ khác).
- Ràng buộc duy nhất `(subject_id, date, start_at)` giữ nguyên → dời trùng hoàn toàn với buổi khác
  của môn bị từ chối (lỗi 400 tiếng Việt).
- `PATCH /sessions/{id}` nhận thêm `date`; đổi `date` thì đặt `original_date` (nếu đang `NULL`), tính
  lại `start_at`/`end_at`, đặt `time_overridden = true` nếu giờ đổi; dời về đúng ngày gốc thì
  `original_date = NULL`. Gọi `auto_deadlines.reconcile`, `bump_revision` như sửa buổi hiện nay. Ngoài
  học kỳ → trả kèm `warnings: [{code: "outside_semester"}]`.

**Lý do**: Tái dùng cơ chế ngoại lệ đã có; thay đổi nhỏ trong hàm thuần đã có test.

---

## R9. Kiểm thử

- **Backend (pytest)**: Thùng rác (xoá mềm, loại khỏi mọi truy vấn/feed/digest/upcoming, khôi phục đủ
  trường, purge 30 ngày, task tự tạo, danh sách đã xoá), khung giờ làm (ràng buộc, danh sách thông
  minh, calendar), `GET /tasks?view=…` và `/task-counts`, emoji danh sách, dời buổi (ngoại lệ, sinh
  lại, trùng, reconcile, feed), migration khớp model.
- **Frontend (Vitest + Testing Library)**: hàm thuần `groupTasks`, `quickAddDefaults`,
  `toCalendarEvents` (khung giờ làm, khối hạn chót 30 phút, cả ngày, buổi thi, mờ), `dropToPatch`,
  `useHotkeys`, độ tương phản bảng màu (tính tỉ lệ tương phản WCAG cho mọi cặp chữ/nền ở hai chế độ),
  component QuickAdd, TaskRow, TaskDetailPanel, Trash.
- **Desktop (cargo test)**: hàm thuần phân tích phản hồi health check và chu kỳ thử lại.
  `scripts/test.sh` chạy `cargo test` khi máy có Rust; nếu chưa có thì in cảnh báo và bỏ qua bước này
  (không làm hỏng các bước khác), vì Rust chỉ cần cho việc build app.
- **Kiểm thử tay**: quickstart.md của feature này (kéo thả, sáng/tối, app Dock).

---

## R10. Công cụ build app

**Quyết định**: Cần Rust (cài một lần bằng `rustup`, cần internet ở lần cài đầu như việc build image
Docker) và Xcode Command Line Tools (đã có). Thư mục `desktop/` có `package.json` riêng chứa
`@tauri-apps/cli`; `desktop/scripts/install.sh` chạy `tauri build`, ký ad-hoc (`codesign -s -`) và
chép `Lịch Học Cá Nhân.app` vào `~/Applications`. Icon riêng vẽ bằng SVG (`desktop/icon/icon.svg`:
cuốn lịch cách điệu với dấu tích, màu nhấn của app), sinh bộ icon bằng `tauri icon`.

**Lý do**: Giống cách đóng gói agent (R4/R6 của feature 001): ký ad-hoc là đủ cho app cá nhân, không
cần tài khoản Apple Developer.

---

## R11. Các đợt triển khai

| Đợt | Nội dung | User story |
|-----|----------|------------|
| 1 | Backend: thùng rác, khung giờ làm, emoji danh sách, `/tasks?view`, `/task-counts`. Frontend: Tailwind + token màu sáng/tối, `ui/`, khung 3 cột (thanh biểu tượng, cột danh sách, khu vực chính, bảng chi tiết), danh sách thông minh, nhóm task, thêm nhanh, Thùng rác, phím tắt cơ bản; chuyển các trang Môn học, Cài đặt, Lịch thi (giữ chức năng, áp style mới) | US2, US3, US6 (dữ liệu + bảng chi tiết), US7, US8 |
| 2 | Trang Lịch mới (đầu trang, Ngày/Tuần/Tháng, hàng thứ + số ngày, đường giờ hiện tại, Cả ngày, khối màu nhạt, xếp cạnh nhau, khối hạn chót, buổi thi nổi bật, lọc nhãn) | US4, US6 (lịch) |
| 3 | Kéo thả: đổi giờ/ngày task, kéo dãn, chọn vùng tạo task, Hoàn tác; backend dời buổi học + hộp thoại xác nhận | US5 |
| 4 | App Tauri: trang chờ "Hãy mở OrbStack", menu tiếng Việt, cửa sổ nhớ vị trí, một phiên bản, icon, script cài | US1 |

Mỗi đợt kết thúc bằng `./scripts/test.sh` pass, commit và hướng dẫn thử; app vẫn dùng được qua trình
duyệt sau mỗi đợt.
