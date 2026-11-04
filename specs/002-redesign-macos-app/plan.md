# Implementation Plan: Thiết kế lại giao diện và đóng gói app macOS

**Branch**: `002-redesign-macos-app` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-redesign-macos-app/spec.md`

## Summary

Thay giao diện web của feature 001 bằng bố cục 3 cột (thanh biểu tượng, cột danh sách, khu vực chính
và bảng chi tiết) với danh sách thông minh, thêm nhanh, Thùng rác, lịch tuần mới có kéo thả, chế độ
sáng/tối theo macOS và phím tắt; rồi đóng gói thành app macOS bằng Tauri 2.

Cách làm: giữ nguyên backend Flask + PostgreSQL trong Docker và agent đồng bộ; backend chỉ mở rộng ở
ba chỗ spec cần (Thùng rác bằng xoá mềm, khung giờ làm của task, dời buổi học sang ngày khác) cộng hai
endpoint đọc cho danh sách thông minh. Frontend React + Vite được thiết kế lại với Tailwind CSS 4,
component tự viết trong `src/ui/` dựa trên vài Radix primitives, FullCalendar 6 (MIT) cho lịch. App
Tauri là một "vỏ" mỏng: hiện trang chờ đóng gói trong app, kiểm tra `127.0.0.1:8080/api/health`, khi
backend sẵn sàng thì nạp giao diện từ `http://127.0.0.1:8080/`; nếu chưa thì hiện "Hãy mở OrbStack"
và tự thử lại ([research R1, R2](research.md)). Triển khai theo 4 đợt nhỏ ([R11](research.md)).

## Technical Context

**Language/Version**: Python 3.12 (backend, giữ nguyên); TypeScript 5 + React 18 (frontend); Rust
stable (app Tauri, cài qua rustup); Python 3.11 (agent, giữ nguyên)

**Primary Dependencies**:
- Backend: giữ nguyên (Flask 3, Flask-SQLAlchemy, Flask-Migrate, pydantic 2).
- Frontend: thêm `tailwindcss` 4 + `@tailwindcss/vite`; `@radix-ui/react-dialog`,
  `react-popover`, `react-dropdown-menu`, `react-tooltip`; giữ FullCalendar 6 (core, daygrid,
  timegrid, interaction, react — đều MIT), TanStack Query 5, React Router 6.
- Desktop: Tauri 2 (`tauri`, `tauri-build`), `tauri-plugin-window-state`,
  `tauri-plugin-single-instance`; `@tauri-apps/cli` (devDependency) và `@tauri-apps/api` cho trang
  chờ.

**Storage**: PostgreSQL 16 (giữ nguyên, volume `lichhoc_pgdata`); migration mới `0004_redesign`.
Trạng thái giao diện trong `localStorage`; kích thước cửa sổ do plugin window-state lưu.

**Testing**: pytest (backend), Vitest + Testing Library (frontend, gồm hàm thuần nhóm task, mặc định
thêm nhanh, ánh xạ lịch, kéo thả, phím tắt, tương phản màu), `cargo test` (hàm thuần của app Tauri);
tất cả qua `./scripts/test.sh` ([R9](research.md)).

**Target Platform**: macOS 14+ trên Mac của chủ dự án (Apple Silicon); giao diện cũng chạy trong
Safari/Chrome trên chính máy đó.

**Project Type**: ứng dụng web cục bộ (backend + frontend trong Docker) + agent macOS + app macOS
(Tauri) làm cửa sổ riêng.

**Performance Goals**: mở app tới màn hình Hôm nay < 3 giây khi backend đang chạy (SC-001); thêm
nhanh phản hồi ngay khi Enter (cập nhật lạc quan, SC-002); kéo thả và chuyển chế độ lịch mượt, phản
hồi < 1 giây.

**Constraints**: chỉ kết nối `127.0.0.1` (constitution IV); toàn bộ tiếng Việt (VI); không thêm thư
viện UI nặng (III); tương phản chữ ≥ 4.5:1 ở cả hai chế độ (FR-032).

**Scale/Scope**: 1 người dùng; ~200–1000 task, 1 học kỳ ~100 buổi; khoảng 15 màn hình/bảng; 4 đợt
triển khai.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Áp dụng trong feature | Kết quả |
|------------|----------------------|---------|
| **I. Code dễ đọc** | Logic giao diện quan trọng tách thành hàm thuần (`groupTasks`, `quickAddDefaults`, `toCalendarEvents`, `dropToPatch`); component nhỏ trong `ui/` và `features/`; Rust chỉ vài hàm ngắn | PASS |
| **II. Test chức năng chính** | Test cho Thùng rác, khung giờ làm, dời buổi, danh sách thông minh (pytest); nhóm task, thêm nhanh, ánh xạ lịch, kéo thả, phím tắt, tương phản (Vitest); kiểm tra kết nối (cargo test); mọi thứ qua `./scripts/test.sh` | PASS |
| **III. Giao diện đơn giản** | Mỗi màn hình một mục đích; bảng chi tiết chỉ hiện khi chọn task; dùng Tailwind (công cụ CSS, không phải bộ UI) + 4 Radix primitives không style; không thư viện icon, không hiệu ứng nặng | PASS, ghi chú ¹ |
| **IV. Offline trên Mac** | App Tauri và giao diện chỉ gọi `127.0.0.1:8080`; không cập nhật tự động, không telemetry; nút "Mở OrbStack" chỉ mở app trên máy; Rust/npm chỉ cần internet lúc cài công cụ build (như build image Docker) | PASS |
| **V. Dữ liệu bền vững** | Không đổi nơi lưu; migration mới; Thùng rác giữ dữ liệu 30 ngày (giảm rủi ro mất do bấm nhầm); `test-persistence.sh` thêm kiểm tra task trong Thùng rác còn sau khởi động lại | PASS |
| **VI. Tiếng Việt** | Mọi chữ qua `i18n/vi.ts`; menu Rust và trang chờ tiếng Việt; ngày giờ định dạng Việt Nam | PASS |
| Ràng buộc bổ sung: YAGNI, ít phụ thuộc | Mỗi phụ thuộc mới có lý do trong Complexity Tracking | PASS, xem bảng dưới |

¹ Tailwind làm tăng chiều dài `className` nhưng thay được toàn bộ `styles.css` tự viết (~700 dòng) và
giữ màu/khoảng cách nhất quán qua token — đúng mục tiêu "nhất quán" của nguyên tắc III.

**Re-check sau Phase 1**: data-model chỉ thêm 6 cột và không bảng mới; contracts không thêm kênh kết
nối nào ngoài localhost; app Tauri không cấp quyền IPC cho trang tải từ backend. Vẫn PASS.

## Project Structure

### Documentation (this feature)

```text
specs/002-redesign-macos-app/
├── plan.md              # File này
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── rest-api.md      # API mở rộng (Thùng rác, khung giờ làm, dời buổi, danh sách thông minh)
│   ├── desktop-shell.md # App Tauri ↔ giao diện ↔ backend
│   └── ui-shortcuts.md  # Đường dẫn và phím tắt
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/                          # giữ cấu trúc của feature 001
├── app/
│   ├── models/task.py            # + work_date/work_start/work_end, deleted_at, trashed_from_list_name
│   ├── models/task_list.py       # + emoji
│   ├── models/class_session.py   # + original_date
│   ├── services/tasks.py         # active_tasks(), smart views, counts, trash/restore/purge
│   ├── services/recurrence.py    # ngày khoá original_date ?? date, has_exception gồm "đã dời"
│   ├── services/sessions.py      # dời ngày
│   └── api/tasks.py, lists.py, sessions.py, trash (trong tasks.py)
├── migrations/versions/0004_redesign.py
└── tests/ (unit + integration mới cho trash, work window, smart views, move session)

frontend/
├── src/
│   ├── main.tsx, App.tsx, routes.tsx
│   ├── index.css                 # @import "tailwindcss"; @theme token màu sáng/tối
│   ├── ui/                       # Button, IconButton, Checkbox, Switch, Input, Select, Dialog,
│   │                             # Popover, Menu, Tooltip, Toast, SidePanel, EmptyState, icons.tsx
│   ├── app/                      # AppShell (3 cột), IconRail, ConnectionBanner, useHotkeys,
│   │                             # ShortcutsDialog, desktopBridge (window.lichhoc)
│   ├── features/
│   │   ├── tasks/                # ListColumn, SmartListView, TaskGroups, TaskRow, QuickAdd,
│   │   │                         # TaskDetailPanel, TrashView, groupTasks.ts, quickAddDefaults.ts
│   │   ├── calendar/             # CalendarPage, CalendarHeader, CalendarBlock, toCalendarEvents.ts,
│   │   │                         # dropToPatch.ts, MoveSessionDialog
│   │   ├── subjects/             # chuyển từ pages/ + components/ hiện có (SubjectForm, BulkSubjectForm…)
│   │   ├── exams/                # trang Lịch thi ("Sắp có" khi chưa có US11)
│   │   └── settings/             # ReminderSettings, AutoDeadlineSettings, Semesters, Shifts, Tags, Lists
│   ├── api/                      # giữ, thêm tasks views/counts/trash, lists emoji, sessions move
│   ├── i18n/vi.ts
│   └── lib/                      # dates, colors (+ biến thể nhạt/đậm), contrast.ts
└── tests/

desktop/                          # MỚI — app Tauri 2
├── package.json                  # @tauri-apps/cli, @tauri-apps/api
├── splash/index.html, splash.js  # trang chờ "Hãy mở OrbStack" (tiếng Việt, không tải gì từ ngoài)
├── icon/icon.svg                 # icon riêng; `tauri icon` sinh icons/
├── src-tauri/
│   ├── Cargo.toml, tauri.conf.json, capabilities/splash.json, Info.plist
│   ├── icons/
│   └── src/main.rs, health.rs (hàm thuần + test), menu.rs
└── scripts/install.sh            # build, ký ad-hoc, cài vào ~/Applications

mac-agent/                        # giữ nguyên
scripts/test.sh                   # + bước cargo test (bỏ qua có cảnh báo nếu chưa có Rust)
```

**Structure Decision**: Giữ cấu trúc web app của feature 001 (backend, frontend, mac-agent) và thêm
`desktop/` cho app Tauri. Frontend tổ chức lại theo `ui/` (component dùng chung), `app/` (khung và
phần hệ thống) và `features/` (theo màn hình); component hiện có được chuyển vào `features/` và áp
style mới, không viết lại logic nghiệp vụ.

## Đợt triển khai (đầu vào cho /speckit-tasks)

1. **Đợt 1 — Bố cục chung + danh sách công việc** (US2, US3, US6 phần dữ liệu và bảng chi tiết, US7,
   US8): migration `0004_redesign`; API danh sách thông minh, đếm, Thùng rác, khung giờ làm, emoji;
   Tailwind + token màu sáng/tối; `ui/`; AppShell 3 cột; Hôm nay (kèm khối Lịch hôm nay), nhóm task,
   TaskRow, QuickAdd, TaskDetailPanel, Thùng rác; phím tắt; chuyển Môn học, Lịch thi, Cài đặt sang
   bố cục mới; bỏ `styles.css` cũ.
2. **Đợt 2 — Trang Lịch** (US4, US6 phần lịch): CalendarHeader, cấu hình FullCalendar theo R5,
   CalendarBlock, `toCalendarEvents` mở rộng, buổi thi nổi bật (khi có), lọc nhãn.
3. **Đợt 3 — Kéo thả** (US5): `dropToPatch`, Hoàn tác, chọn vùng tạo task; backend dời buổi học
   (`original_date`, ngày khoá trong `plan_regeneration`), MoveSessionDialog.
4. **Đợt 4 — Đóng gói app** (US1): `desktop/` Tauri 2, trang chờ, kiểm tra kết nối, menu, cửa sổ,
   icon, `install.sh`, bước `cargo test`.

Mỗi đợt: `./scripts/test.sh` pass → commit → hướng dẫn thử bằng tiếng Việt.

## Complexity Tracking

| Thêm vào | Vì sao cần | Phương án đơn giản hơn bị loại vì |
|----------|------------|-----------------------------------|
| Thành phần thứ năm `desktop/` (Tauri, Rust) | FR-001: app riêng có icon Dock, cửa sổ riêng, menu tiếng Việt | Mở trình duyệt ở chế độ app (Safari "Thêm vào Dock"): không có màn hình "Hãy mở OrbStack", menu và cửa sổ không kiểm soát được; Swift tự viết: phải tự làm nhớ cửa sổ, một phiên bản, menu |
| Toolchain Rust trên máy | Tauri build bằng Rust | Electron không cần Rust nhưng nặng hơn hàng trăm MB, trái nguyên tắc III |
| Tailwind CSS 4 | Token màu sáng/tối và khoảng cách nhất quán cho ~15 màn hình | CSS tự viết hiện tại đã ~700 dòng và sẽ gấp đôi khi thêm chế độ tối; khó giữ nhất quán |
| 4 Radix primitives | Hộp thoại, popover, menu, tooltip đúng bàn phím/ARIA | Tự viết focus trap, đóng bằng Esc, định vị popover: nhiều lỗi tiềm ẩn; thư viện UI đầy đủ thì nặng |
| Xoá mềm `deleted_at` thay vì xoá hẳn | FR-030 Thùng rác 30 ngày | Không có — xoá hẳn không đáp ứng spec |
