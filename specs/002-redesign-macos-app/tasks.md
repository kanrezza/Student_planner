---

description: "Danh sách task cho feature 002 — thiết kế lại giao diện và đóng gói app macOS"
---

# Tasks: Thiết kế lại giao diện và đóng gói app macOS

**Input**: Design documents from `specs/002-redesign-macos-app/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Có — constitution II bắt buộc test cho chức năng chính; mọi test chạy qua
`./scripts/test.sh`. Test viết trước và phải FAIL trước khi làm phần cài đặt tương ứng.

**Organization**: Theo user story của spec. Thứ tự phase đi theo **4 đợt** của plan (chỉ dẫn của
người dùng: bố cục + danh sách công việc → Lịch → kéo thả → đóng gói app), nên US1 (đóng gói, P1) nằm
ở đợt cuối dù là P1: app Tauri chỉ là cửa sổ bọc giao diện, giao diện phải có trước.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Chạy song song được (khác file, không phụ thuộc task chưa xong)
- **[Story]**: User story của spec (US1…US8)
- Đường dẫn tính từ gốc repo: `backend/`, `frontend/`, `desktop/`, `scripts/`

## Đợt và phase

| Đợt | Phase | User story |
|-----|-------|------------|
| — | 1 Setup, 2 Foundational | — |
| 1 | 3 (US2), 4 (US3), 5 (US6), 6 (US7), 7 (US8) | Bố cục 3 cột, thêm nhanh, khung giờ làm, Thùng rác, sáng/tối + phím tắt + các trang khác |
| 2 | 8 (US4) | Lịch tuần mới |
| 3 | 9 (US5) | Kéo thả |
| 4 | 10 (US1) | App macOS (Tauri) |
| — | 11 Polish | — |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Thêm công cụ cho giao diện mới; chưa đổi giao diện đang chạy.

- [ ] T001 Cài phụ thuộc frontend (bản ổn định mới nhất đã phát hành ≥ 2 tuần, ghi chính xác phiên
  bản trong `frontend/package.json` và `package-lock.json`, research R4): `tailwindcss`,
  `@tailwindcss/vite`, `@radix-ui/react-dialog`, `@radix-ui/react-popover`,
  `@radix-ui/react-dropdown-menu`, `@radix-ui/react-tooltip`. Không thêm thư viện icon, phím tắt
  hay UI kit.
- [ ] T002 Bật Tailwind: thêm plugin `tailwindcss()` vào `frontend/vite.config.ts`; tạo
  `frontend/src/index.css` với `@import "tailwindcss";` và import trong `frontend/src/main.tsx`
  (song song với `styles.css` cũ cho tới Phase 7). Kiểm tra `npm run build` và Docker build của
  service `web` vẫn chạy.
- [ ] T003 [P] Cấu hình Prettier/ESLint cho class Tailwind: không thêm plugin; xác nhận
  `npm run lint` pass với file `.css` mới (bỏ qua `@theme`, `@custom-variant` nếu Prettier báo lỗi
  bằng cách cập nhật `frontend/.prettierignore` chỉ khi cần).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dữ liệu mới, lọc task trong Thùng rác ở mọi nơi, token màu, component dùng chung và
khung 3 cột. Mọi user story phụ thuộc phase này.

**⚠️ CRITICAL**: Không bắt đầu user story nào trước khi phase này xong.

### Backend: migration và model

- [ ] T004 Tạo `backend/migrations/versions/0004_redesign.py` (`down_revision =
  "0003_auto_deadline_reminder"`) theo [data-model](data-model.md):
  - `tasks`: `work_date date NULL`, `work_start time NULL`, `work_end time NULL`, `deleted_at
    timestamptz NULL`, `trashed_from_list_name text NULL`; CHECK `(work_date IS NULL) = (work_start
    IS NULL) AND (work_date IS NULL) = (work_end IS NULL)`; CHECK `work_end IS NULL OR work_end >
    work_start`; index một phần `(deleted_at) WHERE deleted_at IS NOT NULL`; index `(work_date)`.
  - `task_lists`: `emoji text NULL` với CHECK `emoji IS NULL OR octet_length(emoji) <= 16`.
  - `class_sessions`: `original_date date NULL`.
  - `downgrade()` xoá đúng các cột/ràng buộc trên.
- [ ] T005 Cập nhật model: `backend/app/models/task.py` (5 cột + 2 CheckConstraint cùng tên với
  migration), `backend/app/models/task_list.py` (`emoji` + CHECK), `backend/app/models/class_session.py`
  (`original_date`; `has_exception` gồm `original_date is not None`; property `is_moved`).
  `test_migrations_match_models` phải pass.
- [ ] T006 Hàm dùng chung `active_tasks()` (select `Task` với `deleted_at IS NULL`) trong
  `backend/app/services/tasks.py`; thay mọi truy vấn `select(Task)` đọc task cho người dùng/đồng bộ
  bằng nó: `services/tasks.py` (`list_tasks`, `get_task` — task trong Thùng rác → 404 trừ khi gọi với
  `include_trashed=True`), `services/today.py`, `services/calendar.py`, `services/sync_feed.py`,
  `services/digest.py`, `services/reminders.py` (`upcoming`), `services/task_lists.py` (số đếm),
  `services/auto_deadlines.py` (`reconcile` bỏ qua task trong Thùng rác, `drop_for_sessions` không
  xoá task trong Thùng rác).
- [ ] T007 [P] Test trong `backend/tests/integration/test_trash_filtering.py`: đặt `deleted_at` trực
  tiếp cho một task có nhãn, hạn hôm nay, nhắc → task không có trong `/api/tasks`, `/api/today`,
  `/api/calendar`, `/api/sync/feed` (`reminders`), `/api/digest`, `/api/reminders/upcoming`, số đếm
  `/api/lists`; task tự tạo trong Thùng rác không bị reconcile cập nhật hay tạo lại.

### Frontend: token, component, khung

- [ ] T008 Token màu và kiểu chữ trong `frontend/src/index.css` (research R4): `@theme` với
  `--color-bg`, `--color-surface`, `--color-surface-2`, `--color-border`, `--color-text`,
  `--color-muted`, `--color-accent` (xanh lam ngọc đậm), `--color-accent-contrast`,
  `--color-danger`, `--color-warning`, `--color-today`, `--radius-*`, font `-apple-system`; giá trị
  chế độ tối trong `@media (prefers-color-scheme: dark)`. Không có nút chọn giao diện.
- [ ] T009 [P] Bảng màu nhãn/môn hai biến thể trong `frontend/src/lib/colors.ts`: giữ `colorHex`
  hiện có; thêm `colorSoft(code, scheme)` (nền khối lịch) và `colorStrong(code, scheme)` (chữ, viền)
  cho `c01`…`c12` ở cả `light` và `dark`.
- [ ] T010 [P] `frontend/src/lib/contrast.ts`: `contrastRatio(fg, bg)` theo công thức WCAG 2.x.
  Test `frontend/tests/contrast.test.ts`: mọi cặp chữ/nền dùng trong app (text/bg, muted/surface,
  accent-contrast/accent, `colorStrong`/`colorSoft` của 12 màu, cả hai chế độ) ≥ 4.5 (FR-032).
- [ ] T011 [P] Biểu tượng SVG nét mảnh tự vẽ trong `frontend/src/ui/icons.tsx` (component nhận
  `size`, `className`, `aria-hidden`): checklist, calendar, book, exam, gear, sun, sunrise, week,
  inbox, check-circle, trash, tag, star, star-filled, plus, chevron-left/right/down, close, more,
  clock, flag (hạn chót), repeat (tự tạo), sidebar, alert, link.
- [ ] T012 [P] Component dùng chung trong `frontend/src/ui/`: `Button.tsx` (primary, secondary,
  ghost, danger), `IconButton.tsx` (bắt buộc `label` tiếng Việt cho aria/tooltip), `Checkbox.tsx`
  (vuông bo góc, trạng thái mờ khi xong), `Switch.tsx`, `Input.tsx`, `Textarea.tsx`, `Select.tsx`,
  `Badge.tsx`, `EmptyState.tsx` — chỉ dùng class Tailwind và token.
- [ ] T013 [P] Bọc Radix trong `frontend/src/ui/`: `Dialog.tsx` (thay `components/Modal.tsx`,
  `ConfirmDialog.tsx` giữ API cũ để không phải sửa nơi dùng), `Popover.tsx`, `Menu.tsx`
  (dropdown-menu), `Tooltip.tsx`.
- [ ] T014 [P] Toast có nút hành động trong `frontend/src/ui/Toast.tsx` + `useToast()`: hàng đợi, tự
  ẩn sau 5 giây, nút "Hoàn tác" (FR-029, FR-030); thay `components/WarningToast.tsx`.
- [ ] T015 [P] `frontend/src/app/useHotkeys.ts`: đăng ký phím theo [ui-shortcuts](contracts/ui-shortcuts.md)
  (⌘ = `metaKey`), bỏ qua phím một ký tự khi đang gõ trong `input`/`textarea`/`contenteditable`,
  ⌘ và Esc luôn chạy; test `frontend/tests/hotkeys.test.ts` (bỏ qua trong ô nhập, ⌘N vẫn chạy, gỡ
  đăng ký khi unmount).
- [ ] T016 Khung `frontend/src/app/AppShell.tsx` + `frontend/src/app/IconRail.tsx`: thanh biểu tượng
  hẹp (Công việc, Lịch, Môn học, Lịch thi, Cài đặt; Tooltip tiếng Việt; mục đang chọn tô màu nhấn),
  vùng nội dung theo route; `frontend/src/routes.tsx` theo [ui-shortcuts](contracts/ui-shortcuts.md)
  ("/" → `/cong-viec/hom-nay`); các route chưa làm tạm dùng trang hiện có bọc trong khung mới. Xoá
  `components/Layout.tsx` khi không còn dùng.
- [ ] T017 [P] `frontend/src/app/ConnectionBanner.tsx`: lắng nghe lỗi mạng của TanStack Query
  (QueryCache `onError` với `TypeError`/không có phản hồi ≥ 2 lần liên tiếp) → dải "Mất kết nối với
  dữ liệu trên máy — đang thử lại…"; ẩn khi có truy vấn thành công (desktop-shell §2).
- [ ] T018 [P] `frontend/src/app/desktopBridge.ts`: đăng ký `window.lichhoc = { navigate,
  showShortcuts }` (desktop-shell §4) dùng router và trạng thái mở bảng phím tắt; gọi trong `App.tsx`.

**Checkpoint**: Backend lọc Thùng rác ở mọi nơi; giao diện cũ vẫn chạy trong khung mới.

---

## Phase 3: User Story 2 — Bố cục 3 cột và danh sách thông minh (Priority: P1) 🎯 MVP (Đợt 1)

**Goal**: Màn hình Công việc với cột danh sách (thông minh có số đếm, danh sách có emoji, nhãn, Đã
hoàn thành, Thùng rác), task nhóm theo ngày, bảng chi tiết bên phải.

**Independent Test**: quickstart D1, D2 (phần sửa thông tin), D6.

### Tests for User Story 2 ⚠️

- [ ] T019 [P] [US2] Test API trong `backend/tests/integration/test_smart_views_api.py` (giờ cố định
  Thứ Hai 09/11/2026 09:00): tạo task hạn hôm nay, quá hạn, ngày mai, D+5, D+10, không hạn, đã xong,
  có `work_date` = D+1 nhưng hạn D+10 → `GET /api/tasks?view=today|tomorrow|next7|all|completed`
  trả đúng tập theo bảng "Danh sách thông minh" của data-model; `list_id=`, `tag_id=` lọc đúng;
  `GET /api/task-counts` = `{today, tomorrow, next7, all, lists}` khớp; task trong Thùng rác không
  được đếm.
- [ ] T020 [P] [US2] Test emoji trong `backend/tests/integration/test_lists_api.py`: POST/PATCH
  `emoji: "🏠"` lưu và trả về; `"👨‍👩‍👧"` (một cụm) hợp lệ; `"ab"`, `"🏠🏠"`, `""` → 400
  `fields.emoji = "Chỉ chọn một emoji"`; `null` bỏ emoji.
- [ ] T021 [P] [US2] Test hàm thuần `frontend/tests/groupTasks.test.ts` cho
  `frontend/src/features/tasks/groupTasks.ts`: nhóm Quá hạn/Hôm nay/Ngày mai/từng ngày trong 7 ngày
  tới (tiêu đề "Thứ Năm, 12/11")/Sau này/Không có hạn; ngày tham chiếu `min(due_date, work_date)`;
  sắp xếp trong nhóm (giờ, không giờ cuối, ưu tiên); nhóm trống bị bỏ; sang ngày mới (đổi `now`) thì
  nhóm đổi.
- [ ] T022 [P] [US2] Test component `frontend/tests/taskRow.test.tsx`: `TaskRow` hiện checkbox,
  ★ khi Quan trọng, chấm màu nhãn, biểu tượng Tự tạo, giờ hạn canh phải (đỏ khi quá hạn), khung giờ
  làm "T5 19:00–21:00"; bấm checkbox gọi complete; bấm dòng gọi `onOpen`.
- [ ] T023 [P] [US2] Test `frontend/tests/useNow.test.tsx` cho `frontend/src/app/useNow.ts` bằng giờ
  giả lập (`vi.useFakeTimers()` + `vi.setSystemTime`): đặt 23:59:30 → sau 30 giây `today` đổi sang ngày
  mới và các query `task-counts`, `tasks` (danh sách thông minh), `today` được làm mới đúng một lần;
  đổi giờ hệ thống sang ngày hôm sau rồi phát sự kiện `focus`/`visibilitychange` → cập nhật ngay; focus
  lại trong cùng ngày → không làm mới; gỡ timer và listener khi unmount.

### Implementation for User Story 2

- [ ] T024 [US2] Backend `GET /api/tasks?view=` và `GET /api/task-counts` trong
  `backend/app/services/tasks.py` (`smart_view(view, now)`, `counts(now)` theo data-model) và
  `backend/app/api/tasks.py`; giữ tham số cũ (`list_id`, `tags`, `include_completed`); `view=trash`
  để Phase 6. Cập nhật contract nếu khác.
- [ ] T025 [US2] Backend emoji, **không thêm thư viện**: trong `backend/app/schemas/tasks.py` (`ListIn`)
  thêm `emoji: str | None` và hàm thuần `is_single_emoji(text)` tự kiểm tra theo dải mã (quy tắc ở
  data-model, bảng `task_lists`): ký tự đầu thuộc dải mã emoji; theo sau chỉ được là VS16 (U+FE0F),
  modifier màu da (U+1F3FB–U+1F3FF), cặp ZWJ (U+200D) + emoji, hoặc đúng một chỉ báo vùng nữa (cờ);
  tối đa 16 byte; sai → "Chỉ chọn một emoji". Test đơn vị `backend/tests/unit/test_emoji.py`: 🏠, ❤️,
  👍🏽, 👨‍👩‍👧, 🇻🇳 hợp lệ; "a", "ab", "🏠🏠", "🏠a", " 🏠", "1️⃣", "" không hợp lệ.
  `backend/app/services/task_lists.py`, `backend/app/api/lists.py` lưu và trả `emoji`.
- [ ] T026 [P] [US2] API frontend: `frontend/src/api/tasks.ts` thêm `useSmartTasks(view | {listId} |
  {tagId})`, `useTaskCounts()`; mọi mutation task làm mới cả hai key; `frontend/src/api/types.ts`
  thêm `work_date`, `work_start`, `work_end`, `deleted_at`, `days_left_in_trash`,
  `trashed_from_list_name` cho `Task`, `emoji` cho `TaskList`.
- [ ] T027 [US2] `frontend/src/features/tasks/groupTasks.ts` (hàm thuần, làm T021 pass).
- [ ] T028 [US2] `frontend/src/app/useNow.ts` (làm T023 pass): context `NowProvider` đặt trong
  `App.tsx` cung cấp `now` (cập nhật mỗi phút) và `today` (`YYYY-MM-DD`); hẹn timer tới 00:00 kế tiếp,
  khi đổi ngày thì `queryClient.invalidateQueries` cho `task-counts`, `tasks`, `today`, `calendar`; nghe
  `focus` và `visibilitychange` để kiểm tra lại ngày (máy ngủ qua nửa đêm). `groupTasks`, `ListColumn`
  (biểu tượng số ngày), `quickAddDefaults` và `CalendarScreen` lấy giờ từ đây (edge case "Sang ngày
  mới").
- [ ] T029 [US2] `frontend/src/features/tasks/ListColumn.tsx`: Hôm nay (biểu tượng có số ngày hôm
  nay), Ngày mai, 7 ngày tới, Tất cả kèm số đếm xám canh phải; tiêu đề nhỏ "Danh sách" + danh sách
  người dùng (emoji hoặc biểu tượng mặc định, tên, số đếm); "Nhãn" (chấm màu, tên); phần dưới cùng tách
  riêng "Đã hoàn thành", "Thùng rác"; mục đang chọn có nền nhạt bo tròn; điều hướng theo route.
- [ ] T030 [US2] `frontend/src/features/tasks/TaskRow.tsx` (làm T022 pass): dòng cao vừa, nền nhạt
  bo tròn khi rê/chọn; dùng `Checkbox`, `icons`; giờ canh phải màu nhấn (đỏ nếu quá hạn).
- [ ] T031 [US2] `frontend/src/features/tasks/TaskGroups.tsx`: tiêu đề nhóm đậm + số lượng + mũi tên
  thu gọn; trạng thái thu gọn lưu `localStorage` theo khoá view+nhóm (bọc try/catch).
- [ ] T032 [US2] `frontend/src/features/tasks/SmartListView.tsx`: tiêu đề lớn của view, vùng cho ô thêm
  nhanh (Phase 4), `TaskGroups`; view `completed` nhóm theo ngày hoàn thành (mới nhất trước), bỏ chọn
  checkbox thì task quay lại danh sách cũ (FR-014); trạng thái trống dùng `EmptyState`.
- [ ] T033 [US2] Khối "Lịch hôm nay" trong `frontend/src/features/tasks/TodaySchedule.tsx`: dùng
  `useToday()` hiện có — buổi thi (khi có) rồi buổi học (giờ, tên, phòng, "Đã huỷ"), các `notices`
  hiện có; bấm buổi học mở `SessionDetail`; chỉ hiện ở view Hôm nay (FR-012).
- [ ] T034 [US2] `frontend/src/features/tasks/TaskDetailPanel.tsx` (bảng bên phải, `SidePanel` trong
  `frontend/src/ui/SidePanel.tsx`): mở theo `?task=:id`; các trường tiêu đề, ghi chú, hạn chót (ngày,
  giờ), ưu tiên, danh sách, nhãn (`TagPicker`), Quan trọng (`ImportantToggle`), nhắc
  (`ReminderSelect`), liên kết buổi học nếu tự tạo (`SessionLink`), nút Xoá; lưu từng trường khi
  rời ô/Enter (PATCH chỉ trường đổi), lỗi hiện dưới ô; Esc đóng. Tái dùng logic validate của
  `components/TaskForm.tsx`; khung giờ làm thêm ở Phase 5.
- [ ] T035 [US2] Trang `frontend/src/features/tasks/TasksScreen.tsx` ghép `ListColumn` +
  `SmartListView` + `TaskDetailPanel`; route `/cong-viec/*` theo ui-shortcuts; cửa sổ hẹp
  (< 900px) bảng chi tiết phủ lên, (< 700px) cột danh sách thu gọn bằng nút `sidebar` (edge case).
- [ ] T036 [US2] Quản lý danh sách (thêm, đổi tên, màu, emoji, xoá) chuyển từ
  `frontend/src/pages/TasksPage.tsx` sang menu ⋯ của từng danh sách trong `ListColumn` + hộp thoại
  `frontend/src/features/tasks/ListDialog.tsx` (ô emoji: gõ hoặc bảng chọn emoji của macOS ⌃⌘Space,
  gợi ý 24 emoji thường dùng trong Popover); xoá `TasksPage.tsx` khi không còn dùng.
- [ ] T037 [US2] Chuỗi tiếng Việt mới trong `frontend/src/i18n/vi.ts` (nhóm `smart`, `groups`,
  `detail`, `listColumn`).

**Checkpoint**: Dùng được Công việc → Hôm nay/Ngày mai/7 ngày tới/Tất cả/danh sách/nhãn/Đã hoàn
thành, sửa task trong bảng chi tiết.

---

## Phase 4: User Story 3 — Thêm công việc nhanh (Priority: P1) (Đợt 1)

**Goal**: Ô "Thêm công việc" ở đầu khu vực chính, Enter là tạo với mặc định theo view.

**Independent Test**: quickstart D3.

### Tests for User Story 3 ⚠️

- [ ] T038 [P] [US3] Test hàm thuần `frontend/tests/quickAddDefaults.test.ts` cho
  `frontend/src/features/tasks/quickAddDefaults.ts`: đúng bảng "Giá trị mặc định khi thêm nhanh"
  của data-model cho today, tomorrow, next7, all, `list:{id}`, `tag:{id}` (không có completed,
  trash: ô thêm nhanh bị ẩn ở hai view này, FR-017).
- [ ] T039 [P] [US3] Test component `frontend/tests/quickAdd.test.tsx`: Enter với "Nộp bài Toán" gọi
  POST đúng payload, ô xoá trống và vẫn focus; Enter với ô trống/chỉ khoảng trắng không gọi API; Esc
  bỏ focus; task hiện ngay trong danh sách (cập nhật lạc quan).

### Implementation for User Story 3

- [ ] T040 [US3] `frontend/src/features/tasks/quickAddDefaults.ts` (hàm thuần, làm T038 pass).
- [ ] T041 [US3] `frontend/src/features/tasks/QuickAdd.tsx`: ô nền xám nhạt bo tròn có "+ Thêm công
  việc", Enter tạo, cập nhật lạc quan cache `useSmartTasks`/`useTaskCounts` rồi đồng bộ lại; lỗi hiện
  bằng Toast; đặt trong `SmartListView` (ẩn ở Đã hoàn thành, Thùng rác).
- [ ] T042 [US3] Phím ⌘N trong `frontend/src/app/AppShell.tsx`: về Công việc (giữ view nếu đang ở
  Công việc) và focus ô thêm nhanh (ref qua context `QuickAddFocusContext`).

**Checkpoint**: Thêm task dưới 5 giây từ mọi view (SC-002).

---

## Phase 5: User Story 6 — Khung giờ làm của task (Priority: P2) (Đợt 1: dữ liệu + bảng chi tiết)

**Goal**: Task có khung giờ làm tuỳ chọn; sửa trong bảng chi tiết; hiện trong dòng task và danh
sách thông minh. Phần hiển thị trên lịch nằm ở Phase 8.

**Independent Test**: quickstart D2 (phần khung giờ làm).

### Tests for User Story 6 ⚠️

- [ ] T043 [P] [US6] Test API `backend/tests/integration/test_work_window_api.py`: POST/PATCH đủ ba
  trường lưu được; thiếu một trường → 400 `fields.work_date` "Cần chọn đủ ngày, giờ bắt đầu và giờ
  kết thúc"; `work_end <= work_start` → 400 `fields.work_end` "Giờ kết thúc phải sau giờ bắt đầu"; ba
  trường `null` bỏ khung giờ làm; `work_date > due_date` → cảnh báo `work_after_due`; feed đồng bộ,
  `reminder_times`, `is_overdue`, bản tóm tắt không đổi khi thêm/sửa khung giờ làm (FR-019); sửa
  khung giờ làm của task tự tạo đặt `user_modified = true`; `/api/today` và `/api/calendar` gồm task
  có `work_date` trong ngày/khoảng (mỗi task một lần).

### Implementation for User Story 6

- [ ] T044 [US6] Backend: `backend/app/schemas/tasks.py` (`work_date`, `work_start`, `work_end`,
  validator "cả ba hoặc không" và "kết thúc sau bắt đầu", serialize), `backend/app/services/tasks.py`
  (cảnh báo `work_after_due`, trả `{task, warnings}` cho POST/PATCH nếu có cảnh báo — giữ dạng trả
  hiện tại khi không có), `backend/app/services/today.py`, `backend/app/services/calendar.py`
  (điều kiện `due_date` hoặc `work_date`), làm T043 pass.
- [ ] T045 [US6] Bảng chi tiết: mục "Khung giờ làm" trong `TaskDetailPanel.tsx` (Switch bật/tắt, ngày,
  giờ bắt đầu, giờ kết thúc, lỗi dưới ô, cảnh báo "Khung giờ làm sau hạn chót"); `TaskRow.tsx` hiện
  khung giờ làm; `groupTasks` đã xét `work_date` (T021).

**Checkpoint**: Khung giờ làm lưu/sửa/xoá được, không ảnh hưởng nhắc.

---

## Phase 6: User Story 7 — Thùng rác (Priority: P2) (Đợt 1)

**Goal**: Xoá task vào Thùng rác, Hoàn tác, khôi phục trong 30 ngày, xoá hẳn tự động/tay.

**Independent Test**: quickstart D4, D5.

### Tests for User Story 7 ⚠️

- [ ] T046 [P] [US7] Test API `backend/tests/integration/test_trash_api.py`:
  - `DELETE /api/tasks/{id}` → 200 kèm task, `deleted_at` có giá trị, `revision` tăng, task biến mất
    khỏi feed; gọi lại → 404.
  - `POST /api/tasks/{id}/restore` → mọi trường (tiêu đề, ghi chú, hạn, khung giờ làm, ưu tiên, danh
    sách, nhãn, Quan trọng, `reminder_minutes`) như trước khi xoá; `revision` tăng.
  - Task tự tạo: xoá → `auto_task_suppressed = true`, reconcile không tạo lại; khôi phục →
    `auto_task_suppressed = false`, vẫn liên kết buổi, không sinh task trùng.
  - `GET /api/tasks?view=trash` sắp `deleted_at` giảm dần, có `days_left_in_trash` (30 khi vừa xoá, làm
    tròn lên, tối thiểu 0).
  - `purge_expired_trash`: task có `deleted_at` 31 ngày trước bị xoá hẳn khi gọi `view=trash`,
    `/task-counts` hoặc `/today`; 29 ngày thì còn.
  - `/api/sync/feed` gọi `purge_expired_trash_throttled(now)`: lần gọi đầu xoá task quá 30 ngày; gọi
    lại sau 10 phút (giờ giả lập) không chạy purge (task mới quá hạn vẫn còn); sau 61 phút thì chạy lại
    và xoá; phản hồi feed không đổi dạng.
  - `DELETE /api/tasks/{id}?permanent=true` chỉ cho task trong Thùng rác (task đang dùng → 409);
    `DELETE /api/trash` trả `{deleted: n}`.
  - `DELETE /api/lists/{id}?delete_tasks=true` → task vào Thùng rác, chuyển sang Học tập,
    `trashed_from_list_name` = tên cũ; khôi phục trả cảnh báo `list_replaced`.
- [ ] T047 [P] [US7] Test component `frontend/tests/trash.test.tsx`: ⌘⌫ trên task đang chọn gọi
  DELETE và hiện Toast "Đã chuyển vào Thùng rác" có "Hoàn tác" (gọi restore); TrashView hiện "Còn N
  ngày", nút Khôi phục, "Xoá vĩnh viễn" và "Dọn sạch Thùng rác" hỏi xác nhận; Thùng rác rỗng hiện
  "Thùng rác trống".

### Implementation for User Story 7

- [ ] T048 [US7] Backend trong `backend/app/services/tasks.py`: `trash_task`, `restore_task`,
  `delete_permanently`, `empty_trash`, `purge_expired_trash(now)` (data-model "Vòng đời Thùng rác");
  `backend/app/api/tasks.py`: đổi `DELETE /tasks/{id}`, thêm `/restore`, `?permanent=true`,
  `DELETE /trash`, `view=trash`; gọi `purge_expired_trash` ở `/task-counts`, `view=trash`, `/today`
  và khi `create_app` khởi động (bọc try/except để lỗi purge không chặn khởi động, ghi log);
  `purge_expired_trash_throttled(now)` (mốc lần chạy cuối trong bộ nhớ của tiến trình, tối đa 1 lần/giờ)
  gọi ở đầu `GET /api/sync/feed` trong `backend/app/api/sync.py` (lỗi purge chỉ ghi log, không làm hỏng
  feed).
- [ ] T049 [US7] Backend xoá danh sách với `delete_tasks=true` trong `backend/app/services/task_lists.py`
  theo data-model (chuyển sang Học tập + vào Thùng rác + `trashed_from_list_name`).
- [ ] T050 [US7] Cập nhật test cũ của feature 001 phụ thuộc xoá hẳn (`tests/integration/test_tasks_api.py`,
  `test_lists_api.py`, `test_auto_deadlines_api.py`) sang hành vi Thùng rác; ghi lý do trong commit.
- [ ] T051 [US7] Frontend: `frontend/src/api/tasks.ts` (`useTrashTask`, `useRestoreTask`,
  `useDeletePermanently`, `useEmptyTrash`), `frontend/src/features/tasks/TrashView.tsx` (ngày xoá,
  "Còn N ngày", Khôi phục, Xoá vĩnh viễn, Dọn sạch), nút Xoá trong bảng chi tiết và ⌘⌫ dùng Toast
  Hoàn tác; Toast cảnh báo `list_replaced` khi khôi phục.
- [ ] T052 [US7] `scripts/test-persistence.sh`: thêm bước tạo task, chuyển vào Thùng rác, khởi động lại
  → task vẫn ở Thùng rác (constitution V).

**Checkpoint**: Không còn mất task do bấm nhầm.

---

## Phase 7: User Story 8 — Giao diện gọn, sáng/tối, phím tắt, các trang khác (Priority: P3) (Đợt 1)

**Goal**: Mọi màn hình theo phong cách mới, theo chế độ sáng/tối macOS, phím tắt đủ; Môn học, Lịch
thi, Cài đặt giữ đủ chức năng.

**Independent Test**: quickstart D11, D12, D16 (phần không thuộc lịch).

### Tests for User Story 8 ⚠️

- [ ] T053 [P] [US8] Test `frontend/tests/shortcuts.test.tsx`: ⌘1…⌘5 đổi route; ⌘, mở Cài đặt; ⌘/ mở
  `ShortcutsDialog` liệt kê đủ phím của ui-shortcuts; ↑/↓ đổi task đang chọn, ↩ mở chi tiết, ⌘↩ hoàn
  thành; Esc đóng theo thứ tự hộp thoại → bảng chi tiết → bỏ focus.
- [ ] T054 [P] [US8] Cập nhật test hiện có trong `frontend/tests/components.test.tsx` cho component đã
  chuyển chỗ/đổi giao diện (SessionDetail, ShiftPicker, ImportantToggle, EveReminderField) — giữ nguyên
  hành vi được kiểm tra.

### Implementation for User Story 8

- [ ] T055 [US8] Phím tắt toàn cục trong `frontend/src/app/AppShell.tsx` và
  `frontend/src/features/tasks/SmartListView.tsx` theo ui-shortcuts (⌘1…⌘5, ⌘,, ⌘/, ↑/↓, ↩, ⌘↩, ⌘⌫,
  Esc); `frontend/src/app/ShortcutsDialog.tsx` (bảng tiếng Việt).
- [ ] T056 [P] [US8] Trang Môn học `frontend/src/features/subjects/SubjectsScreen.tsx`: chuyển
  `pages/SubjectsPage.tsx`, `pages/SemestersPage.tsx`, `components/SubjectForm.tsx`,
  `BulkSubjectForm.tsx`, `SemesterForm.tsx`, `ShiftPicker.tsx`, `WeekdayPicker.tsx`, `ColorPicker.tsx`
  sang `features/subjects/` và style Tailwind; giữ mọi chức năng (học kỳ, thêm một/nhiều môn, sửa,
  xoá có xác nhận, xem buổi); chỗ cho "Nhập từ ảnh" (hiện "Sắp có" tới khi US6 của feature 001 xong).
- [ ] T057 [P] [US8] Trang Lịch thi `frontend/src/features/exams/ExamsScreen.tsx`: `EmptyState` "Sắp có —
  lịch thi sẽ có khi phần Lịch thi được làm xong" (FR-036, US8 kịch bản 5).
- [ ] T058 [P] [US8] Trang Cài đặt `frontend/src/features/settings/SettingsScreen.tsx`: cột mục bên
  trái (Nhắc lịch và đồng bộ, Thông báo tổng hợp, Mốc nhắc quan trọng, Học kỳ, Ca học, Nhãn, Danh
  sách, Tự tạo deadline) + nội dung; chuyển `pages/ReminderSettings.tsx`, `AutoDeadlineSettings.tsx`,
  `ShiftsPage.tsx`, `TagsPage.tsx` vào `features/settings/` với style mới; mục Danh sách dùng lại
  `ListDialog`.
- [ ] T059 [P] [US8] Chuyển các component còn lại sang style Tailwind: `SessionDetail`, `TagPicker`,
  `TagFilter`, `ReminderSelect`, `ImportantToggle`, `SessionLink`, `SyncPrompt`, `FormField` (giữ
  API).
- [ ] T060 [US8] Xoá `frontend/src/styles.css` và các trang/component cũ không còn dùng
  (`pages/TodayPage.tsx`, `pages/PlaceholderPage.tsx`, `components/TaskItem.tsx`,
  `components/TaskForm.tsx` nếu đã thay hết); `npm run build` không còn tham chiếu.
- [ ] T061 [US8] Rà toàn bộ giao diện ở chế độ Tối (macOS → Giao diện → Tối): sửa chỗ thiếu token;
  trạng thái `prefers-color-scheme` đổi khi app đang mở không cần tải lại (D11).

**Checkpoint (hết Đợt 1)**: `./scripts/test.sh` pass; commit; hướng dẫn thử D1–D6, D11, D12.

---

## Phase 8: User Story 4 — Lịch tuần mới (Priority: P2) (Đợt 2)

**Goal**: Trang Lịch với đầu trang mới, Ngày/Tuần/Tháng, hàng thứ + số ngày, đường giờ hiện tại, Cả
ngày, khối màu nhạt, xếp cạnh nhau, khối hạn chót, buổi thi nổi bật, lọc nhãn.

**Independent Test**: quickstart D7.

### Tests for User Story 4 ⚠️

- [ ] T062 [P] [US4] Test `frontend/tests/calendarEvents.test.ts` cho
  `frontend/src/features/calendar/toCalendarEvents.ts` (mở rộng bản trong `lib/calendarEvents.ts`)
  theo bảng "Khối trên lịch" của data-model: task có khung giờ làm → khối khung giờ làm; chỉ giờ hạn
  → `due_at`…+30 phút, cờ `deadline`; chỉ ngày → `allDay`; task xong và buổi huỷ có class mờ; buổi
  thi (dữ liệu giả) có class nổi bật, không kéo được; `startEditable`/`durationEditable` đúng bảng;
  màu nền `colorSoft`, chữ `colorStrong`.
- [ ] T063 [P] [US4] Test hàm thuần `frontend/tests/calendarTitle.test.ts`: tiêu đề tháng/năm "Tháng 11,
  2026"; tuần vắt hai tháng "Tháng 11 – Tháng 12, 2026"; vắt hai năm "Tháng 12, 2026 – Tháng 1, 2027";
  `scrollTime` (tuần có hôm nay → giờ hiện tại − 1 giờ, tuần khác → 06:00); `monthGrid(month)` cho
  `frontend/src/features/calendar/monthGrid.ts`: 6 hàng × 7 ngày, bắt đầu Thứ Hai, có ngày tháng
  trước/sau (cờ `outside`), tháng 2/2027 và tháng bắt đầu Chủ Nhật (11/2026 bắt đầu Chủ Nhật 01/11).

### Implementation for User Story 4

- [ ] T064 [US4] `frontend/src/features/calendar/toCalendarEvents.ts`, `calendarTitle.ts` và
  `monthGrid.ts` (làm T062, T063 pass); xoá `lib/calendarEvents.ts` sau khi chuyển.
- [ ] T065 [US4] `frontend/src/features/calendar/CalendarHeader.tsx`: nút ẩn/hiện cột bên, tiêu đề
  tháng/năm lớn, nút "+", menu chế độ Ngày/Tuần/Tháng (`Menu`), cụm trước/"Hôm nay"/sau; trạng thái
  lấy từ URL `/lich?che-do=&ngay=&nhan=`; nút ẩn/hiện cột bên (nhớ trong `localStorage`).
- [ ] T066 [US4] Cột bên `frontend/src/features/calendar/CalendarSidebar.tsx` (FR-021, FR-037): lịch
  tháng nhỏ dựng từ `monthGrid` (hàng T2…CN, nút tháng trước/sau, hôm nay tô tròn màu nhấn, khoảng đang
  xem tô nền nhạt, ngày ngoài tháng chữ mờ; bấm một ngày → `gotoDate` và cập nhật `ngay=` trên URL)
  và bộ lọc nhãn `TagFilter` bên dưới (cập nhật `nhan=`); test component trong
  `frontend/tests/calendarSidebar.test.tsx` (bấm ngày gọi `onSelectDate` đúng ngày, tô hôm nay).
- [ ] T067 [US4] `frontend/src/features/calendar/CalendarBlock.tsx` (`eventContent`): khối nền nhạt bo
  góc, checkbox cho task (bấm hoàn thành ngay, không mở chi tiết), tiêu đề đậm (★ nếu quan trọng), dòng
  "08:00–10:00", phòng cho buổi học, "Đã dời"/"Đã huỷ", biểu tượng hạn chót; buổi thi nền đậm + viền +
  nhãn "Thi"; khối hẹp hiện tiêu đề rút gọn và tooltip đầy đủ (FR-024).
- [ ] T068 [US4] `frontend/src/features/calendar/CalendarScreen.tsx` thay `pages/CalendarPage.tsx`:
  cấu hình FullCalendar theo bảng research R5 (`headerToolbar: false`, `firstDay: 1`, `locale: vi`,
  `dayHeaderContent` hàng T2…CN + số ngày, số hôm nay tô tròn màu nhấn, `nowIndicator` + nhãn giờ đỏ
  ở cột giờ, `allDayText: 'Cả ngày'`, `slotEventOverlap: false`, `scrollTime`), bấm khối mở bảng chi
  tiết task (`?task=`) / `SessionDetail`; chế độ Tháng hiện tóm tắt như hiện tại; ghép
  `CalendarSidebar`. **Chế độ tạo mới** của `TaskDetailPanel.tsx` (làm ở đây, Phase 9 dùng lại): mở
  qua `?task=new&due=YYYY-MM-DD[&work_date=&work_start=&work_end=]`, mọi trường để trống trừ giá trị
  truyền vào, focus ô tiêu đề, chỉ gọi POST khi rời ô tiêu đề/Enter với tiêu đề không trống (rồi đổi
  URL sang `?task=:id` để các trường khác lưu như bình thường), Esc khi tiêu đề trống thì đóng và không
  tạo gì; test trong `frontend/tests/taskDetailCreate.test.tsx`. Nút "+" mở chế độ này với ngày đang
  chọn (US4 kịch bản 9).
- [ ] T069 [US4] Phím tắt Lịch (←/→, T, D/W/M) đăng ký trong `CalendarScreen.tsx`.
- [ ] T070 [US4] CSS ghi đè FullCalendar trong `frontend/src/features/calendar/calendar.css` (import
  sau `index.css`): đường lưới mảnh, nền theo token, đường giờ hiện tại đỏ, hai chế độ sáng/tối.

**Checkpoint (hết Đợt 2)**: `./scripts/test.sh` pass; commit; hướng dẫn thử D7.

---

## Phase 9: User Story 5 — Kéo thả trên lịch (Priority: P2) (Đợt 3)

**Goal**: Kéo đổi giờ/ngày task, kéo dãn khung giờ làm, chọn vùng tạo task, dời buổi học có xác
nhận, Hoàn tác.

**Independent Test**: quickstart D8, D9, D10.

### Tests for User Story 5 ⚠️

- [ ] T071 [P] [US5] Test unit `backend/tests/unit/test_recurrence.py` (bổ sung): `plan_regeneration`
  dùng ngày khoá `original_date ?? date`; buổi đã dời được giữ khi đổi phòng/giờ chung của môn, không
  sinh buổi mới ở ngày gốc; ngày gốc nằm ngoài khoảng mới → thuộc `exception_conflicts`.
- [ ] T072 [P] [US5] Test API `backend/tests/integration/test_move_session_api.py`: PATCH `date` dời
  Thứ Hai 16/11 → Thứ Bảy 21/11 08:00 → `original_date = 2026-11-16`, `is_moved`, `revision` tăng,
  feed có sự kiện ở ngày mới; dời về ngày gốc → `original_date = null`; trùng `(môn, ngày, giờ bắt
  đầu)` → 400 `fields.date` "Môn này đã có buổi học vào ngày và giờ đó"; ngoài học kỳ → thành công kèm
  `outside_semester`; buổi có task tự tạo → deadline tính theo ngày mới; buổi đã dời rồi sửa lịch
  chung của môn → vẫn giữ.
- [ ] T073 [P] [US5] Test hàm thuần `frontend/tests/dropToPatch.test.ts` cho
  `frontend/src/features/calendar/dropToPatch.ts`: đủ các dòng của bảng "Quy tắc kéo thả" (data-model),
  làm tròn 15 phút, kéo dãn tối thiểu 15 phút, `undoPatch` trả đúng giá trị cũ của các trường đã đổi.

### Implementation for User Story 5

- [ ] T074 [US5] Backend dời buổi: `backend/app/services/recurrence.py` (`ExistingSession` thêm
  `original_date`, ngày khoá, `has_exception`), `backend/app/services/subjects.py` (`_existing` truyền
  `original_date`), `backend/app/services/sessions.py` + `backend/app/api/sessions.py` (`date` trong
  PATCH theo research R8, trả `{session, warnings}`), `backend/app/schemas/subjects.py`
  (`original_date`, `is_moved` trong `serialize_session`); làm T071, T072 pass. Cập nhật
  `frontend/src/api/sessions.ts` cho dạng trả mới.
- [ ] T075 [US5] `frontend/src/features/calendar/dropToPatch.ts` (làm T073 pass).
- [ ] T076 [US5] Kéo thả task trong `CalendarScreen.tsx`: `editable`, `snapDuration: '00:15'`,
  `eventDrop`/`eventResize` → `dropToPatch` → PATCH (cập nhật lạc quan; lỗi thì `info.revert()` +
  Toast); Toast "Đã đổi giờ" có "Hoàn tác" 5 giây; Esc khi đang kéo huỷ (mặc định FullCalendar).
- [ ] T077 [US5] Chọn vùng tạo task: `selectable`, `select` → mở bảng chi tiết bằng chế độ tạo mới đã
  có từ T068 (`?task=new&due=&work_date=&work_start=&work_end=` theo vùng đã kéo); không sửa thêm
  `TaskDetailPanel.tsx` ngoài việc truyền tham số; bỏ vùng chọn sau khi mở.
- [ ] T078 [US5] Dời buổi học: `frontend/src/features/calendar/MoveSessionDialog.tsx` ("Chỉ đổi giờ buổi
  học ngày … sang …? Các buổi khác của môn không đổi." hoặc "Dời buổi học ngày … sang …?"); đồng ý →
  PATCH session; huỷ → `revert()`; hiện cảnh báo trùng giờ/ngoài học kỳ nếu có. Thêm ô ngày "Dời sang
  ngày" vào `SessionDetail` (FR-028).
- [ ] T079 [US5] Khoá kéo thả cho buổi thi, buổi đã huỷ, task đã hoàn thành (theo `toCalendarEvents`);
  khối buổi đã dời hiện "Đã dời (từ T2 16/11)".

**Checkpoint (hết Đợt 3)**: `./scripts/test.sh` pass; commit; hướng dẫn thử D8–D10.

---

## Phase 10: User Story 1 — App macOS riêng (Priority: P1) (Đợt 4)

**Goal**: "Lịch Học Cá Nhân.app" (Tauri 2) có icon riêng, cửa sổ riêng, menu tiếng Việt, màn hình
"Hãy mở OrbStack", nhớ cửa sổ, một phiên bản.

**Independent Test**: quickstart D13, D14, D15, D17.

**Phụ thuộc người dùng**: cài Rust (`rustup`) một lần trước task T080.

- [ ] T080 [US1] Khởi tạo `desktop/` theo plan: `desktop/package.json` (`@tauri-apps/cli`,
  `@tauri-apps/api`, script `tauri`), `desktop/src-tauri/Cargo.toml` (`tauri` 2,
  `tauri-plugin-window-state`, `tauri-plugin-single-instance`, không thêm crate HTTP),
  `desktop/src-tauri/tauri.conf.json` (`productName: "Lịch Học Cá Nhân"`, `identifier:
  "vn.lichhoc.desktop"`, cửa sổ `main` 1280×820, tối thiểu 720×520, `titleBarStyle: "Overlay"`,
  `hiddenTitle: true`, `url` = trang chờ nội bộ, `userAgent` thêm `LichHocDesktop`), `.gitignore` cho
  `desktop/node_modules`, `desktop/src-tauri/target`.
- [ ] T081 [P] [US1] `desktop/src-tauri/src/health.rs`: hàm thuần `parse_status_line(&str) ->
  Option<u16>`, `is_ready(status) -> bool`, `check_health(addr, timeout) -> HealthResult` dùng
  `std::net::TcpStream` gửi `GET /api/health HTTP/1.1` tới `127.0.0.1:8080` (timeout 1 giây); test
  `cargo test` cho phân tích phản hồi 200, 502, rác, và kết nối bị từ chối (cổng không mở).
- [ ] T082 [US1] `desktop/src-tauri/src/main.rs`: vòng kiểm tra mỗi 2 giây ở luồng nền; phát sự kiện
  `connection-status` (`connecting`, `waiting_for_backend`, `orbstack_missing`); khi sẵn sàng điều
  hướng cửa sổ `main` tới `http://127.0.0.1:8080/` và dừng vòng; lệnh `open_orbstack` (`open -a
  OrbStack`, lỗi → `orbstack_missing`) và `retry_now`; đóng cửa sổ thì ẩn, bấm Dock (`RunEvent::Reopen`)
  thì hiện lại; plugin window-state và single-instance (đưa cửa sổ lên trước).
- [ ] T083 [P] [US1] `desktop/src-tauri/capabilities/splash.json`: chỉ cửa sổ `main` với nguồn nội bộ
  (`local: true`) được gọi `open_orbstack`, `retry_now` và nghe `connection-status`; không cấp quyền
  cho `http://127.0.0.1:8080`.
- [ ] T084 [P] [US1] Trang chờ `desktop/splash/index.html` + `splash.js` + style nội tuyến (không tải
  gì từ ngoài, có chế độ sáng/tối): "Đang kết nối…" → "Hãy mở OrbStack" (2 dòng giải thích, nút Mở
  OrbStack, Thử lại, dòng "Đang thử kết nối lại…") → "Không tìm thấy OrbStack trên máy…" theo
  desktop-shell §1; chữ tiếng Việt.
- [ ] T085 [P] [US1] `desktop/src-tauri/src/menu.rs`: menu tiếng Việt theo desktop-shell §3; Cài đặt…
  (⌘,) và Phím tắt (⌘/) gọi `eval("window.lichhoc?.navigate('/cai-dat')")` /
  `showShortcuts()`; Giới thiệu hiện tên và phiên bản.
- [ ] T086 [P] [US1] Icon riêng `desktop/icon/icon.svg` (cuốn lịch cách điệu + dấu tích, màu nhấn của
  app, nền bo góc kiểu macOS; không giống icon app khác) và sinh `desktop/src-tauri/icons/` bằng
  `npx tauri icon desktop/icon/icon.svg` (chuyển sang PNG 1024 nếu công cụ yêu cầu).
- [ ] T087 [US1] Kiểm chứng R1: chạy `npx tauri dev`, xác nhận cửa sổ nạp được
  `http://127.0.0.1:8080`; nếu App Transport Security chặn thì thêm `desktop/src-tauri/Info.plist`
  với `NSAppTransportSecurity → NSAllowsLocalNetworking = true`; ghi kết quả vào `research.md` R1.
- [ ] T088 [US1] Giao diện React: chừa khoảng cho nút cửa sổ khi chạy trong app (`--titlebar-inset` khi
  `navigator.userAgent` có `LichHocDesktop`) trong `frontend/src/app/AppShell.tsx`; vùng kéo cửa sổ
  (`data-tauri-drag-region` không dùng được vì trang ngoài — dùng thanh tiêu đề trong suốt, kéo ở vùng
  trống trên cùng bằng CSS `-webkit-app-region` nếu WKWebView hỗ trợ; nếu không, giữ thanh tiêu đề
  chuẩn và bỏ `titleBarStyle: Overlay`). Ghi quyết định vào research R3.
- [ ] T089 [US1] `desktop/scripts/install.sh`: kiểm tra `cargo` (thiếu → hướng dẫn cài rustup bằng
  tiếng Việt), `npm ci`, `npx tauri build --bundles app`, `codesign --force --deep -s -`, chép
  `Lịch Học Cá Nhân.app` vào `~/Applications` (thay bản cũ); tuỳ chọn `--build-only`, `--uninstall`.
- [ ] T090 [US1] `scripts/test.sh`: thêm bước "Desktop: cargo test" (trong `desktop/src-tauri`) khi có
  `cargo`; nếu không có thì in "⚠️ Bỏ qua: chưa cài Rust" và không tính là lỗi.

**Checkpoint (hết Đợt 4)**: `./scripts/test.sh` pass; app cài được; commit; hướng dẫn thử D13–D15,
D17.

---

## Phase 11: Polish & Cross-Cutting Concerns

- [ ] T091 [P] Cập nhật `specs/001-task-class-scheduler/quickstart.md` các bước dùng giao diện mới
  (đường dẫn trang, tên nút) để V1–V21 chạy được trong app mới (SC-003).
- [ ] T092 [P] Tạo hoặc cập nhật `README.md` tiếng Việt ở gốc repo (constitution "Ràng buộc bổ sung" và
  V; gộp T141 của feature 001 vào đây): giới thiệu; yêu cầu (macOS 14+, OrbStack, Node, Python 3.11 cho
  agent, Rust chỉ khi build app; internet chỉ cần ở lần build/cài đầu); chạy `docker compose up -d
  --build`; cài app (`desktop/scripts/install.sh`) và màn hình "Hãy mở OrbStack"; cài agent
  (`mac-agent/scripts/install.sh`), bật đồng bộ, lưu ý chữ ký ad-hoc; **chỗ lưu dữ liệu** (volume
  `lichhoc_pgdata`, trong OrbStack tại `~/OrbStack/docker/volumes/lichhoc_pgdata`; trạng thái cửa sổ
  của app trong `~/Library/Application Support/vn.lichhoc.desktop`); ⚠️ `docker compose down -v` xoá
  dữ liệu; **sao lưu và khôi phục** (`scripts/backup.sh`/`scripts/restore.sh` nếu đã có, nếu chưa thì
  lệnh `docker compose exec db pg_dump -U lichhoc -Fc lichhoc > lichhoc.dump` và `pg_restore --clean
  --if-exists`); Thùng rác giữ task 30 ngày; phím tắt (bảng ui-shortcuts); chạy test
  `./scripts/test.sh`; xử lý sự cố (OrbStack chưa mở, agent không chạy, bị từ chối quyền, không có
  iCloud). Đánh dấu T141 của feature 001 là đã làm khi xong.
- [ ] T093 Chạy quickstart D1–D17 và V1–V21 (feature 001) trong app; ghi kết quả và chỗ chưa đạt vào
  cuối `specs/002-redesign-macos-app/quickstart.md`, kèm:
  - **Đo thời gian mở app (SC-001)**: backend đang chạy, app đã thoát → bấm icon Dock, bấm giờ tới khi
    danh sách Hôm nay hiện đủ; đo 3 lần, ghi từng lần và trung bình (đạt khi cả 3 lần < 3 giây). Tắt
    OrbStack → mở app → mở OrbStack, đo từ lúc `curl -s 127.0.0.1:8080/api/health` trả 200 tới khi vào
    màn hình chính (đạt khi < 5 giây).
  - **Đếm số lần bấm (SC-009)**: từ màn hình mặc định (Công việc → Hôm nay), đếm số lần bấm để: thêm
    task, xem lịch tuần, thêm môn, huỷ một buổi học, bật đồng bộ, khôi phục task từ Thùng rác; ghi
    bảng chức năng → số lần bấm → đường đi (đạt khi mọi chức năng ≤ 3; gõ phím không tính là bấm).
- [ ] T094 Rà constitution: không có kết nối ra ngoài (D17), mọi chữ tiếng Việt (tìm chuỗi tiếng Anh
  còn sót trong `frontend/src` và `desktop/`), không phụ thuộc thừa trong `package.json`/`Cargo.toml`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)** → **Foundational (2)** → các phase user story.
- **Đợt 1**: Phase 3 (US2) trước; Phase 4 (US3), 5 (US6), 6 (US7) cần khung của US2 (`SmartListView`,
  `TaskDetailPanel`); Phase 7 (US8) cuối đợt vì xoá `styles.css` cũ sau khi mọi màn hình đã chuyển.
- **Đợt 2** (Phase 8, US4): cần Phase 2 (token, ui) và Phase 5 (dữ liệu khung giờ làm).
- **Đợt 3** (Phase 9, US5): cần Phase 8.
- **Đợt 4** (Phase 10, US1): chỉ cần giao diện chạy ở `127.0.0.1:8080` (có thể làm sau Phase 3 nếu
  muốn thấy app sớm), nhưng theo chỉ dẫn làm cuối.
- **Polish (11)**: sau khi các đợt mong muốn xong.

### User Story Dependencies

| Story | Phụ thuộc | Ghi chú |
|-------|-----------|---------|
| US2 Bố cục 3 cột (P1) | Phase 2 | MVP |
| US3 Thêm nhanh (P1) | US2 | |
| US6 Khung giờ làm (P2) | US2 (bảng chi tiết) | phần lịch ở US4 |
| US7 Thùng rác (P2) | US2; T006 | |
| US8 Phong cách + trang khác (P3) | US2 | dọn CSS cũ cuối đợt 1 |
| US4 Lịch tuần (P2) | Phase 2, US6 (dữ liệu) | |
| US5 Kéo thả (P2) | US4 | |
| US1 App macOS (P1) | giao diện chạy được | làm cuối theo chỉ dẫn |

### Within Each User Story

Test (FAIL) → backend (schema/service/API) → API frontend → hàm thuần → component → ghép màn hình.

### Parallel Opportunities

- Phase 2: T007, T009–T015, T017, T018 song song sau T004–T006 (backend) và T008 (token).
- US2: T019–T022 và T023 song song; T025, T026 song song với T024.
- US7: T046, T047 song song; T049 song song với T051.
- US8: T056–T059 song song (khác thư mục).
- US4: T062, T063 song song; T066 song song với T067.
- US5: T071–T073 song song; backend T074 song song với T075.
- US1: T081, T083–T086 song song sau T080.

---

## Parallel Example: User Story 2

```bash
# Viết test song song:
Task: "Test smart views API trong backend/tests/integration/test_smart_views_api.py"   # T019
Task: "Test emoji trong backend/tests/integration/test_lists_api.py"                   # T020
Task: "Test groupTasks trong frontend/tests/groupTasks.test.ts"                        # T021
Task: "Test TaskRow trong frontend/tests/taskRow.test.tsx"                             # T022
Task: "Test useNow trong frontend/tests/useNow.test.tsx"                               # T023

# Sau đó backend và API frontend song song:
Task: "Backend view/counts trong backend/app/services/tasks.py + api/tasks.py"         # T024
Task: "Backend emoji trong schemas + services/task_lists.py + api/lists.py"           # T025
Task: "API frontend trong frontend/src/api/tasks.ts + types.ts"                        # T026
```

## Parallel Example: User Story 1

```bash
# Sau T080 (khung desktop/):
Task: "health.rs + cargo test"            # T081
Task: "capabilities/splash.json"          # T083
Task: "Trang chờ desktop/splash/"         # T084
Task: "menu.rs"                           # T085
Task: "Icon desktop/icon/icon.svg"        # T086
```

---

## Implementation Strategy

### MVP (Đợt 1, Phase 1–3)

1. Phase 1 Setup, Phase 2 Foundational.
2. Phase 3 (US2): màn hình Công việc mới với danh sách thông minh và bảng chi tiết.
3. **Dừng và kiểm chứng**: D1, D2 trong trình duyệt.

### Giao từng đợt

1. **Đợt 1**: Phase 1–7 → test → commit → hướng dẫn thử (D1–D6, D11, D12).
2. **Đợt 2**: Phase 8 → test → commit → hướng dẫn thử D7.
3. **Đợt 3**: Phase 9 → test → commit → hướng dẫn thử D8–D10.
4. **Đợt 4**: Phase 10 (sau khi người dùng cài Rust) → test → cài app → commit → hướng dẫn thử
   D13–D15, D17.
5. Phase 11 khi muốn khép feature.

Sau mỗi đợt, giao diện vẫn dùng được đầy đủ qua `http://127.0.0.1:8080`.

### Notes

- Commit không có dòng `Co-Authored-By` hay "Generated with Claude Code" (CLAUDE.md).
- Không xoá chức năng của feature 001 khi chuyển giao diện; test cũ được cập nhật chứ không bỏ (trừ
  khi hành vi đổi theo spec 002, ví dụ xoá task → Thùng rác, ghi rõ trong commit).
