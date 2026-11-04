# Quickstart & Validation: Thiết kế lại giao diện và app macOS

**Feature**: `002-redesign-macos-app` | **Plan**: [plan.md](plan.md)

## Yêu cầu

- Như feature 001 ([quickstart 001](../001-task-class-scheduler/quickstart.md)): OrbStack, Node 22,
  Python 3.11 cho agent.
- Thêm cho đợt 4 (build app): Rust qua `rustup` (cài một lần, cần internet lúc cài) và Xcode Command
  Line Tools.

## Chạy

```bash
docker compose up -d --build          # backend + giao diện mới tại http://127.0.0.1:8080
./scripts/test.sh                     # lint + test (thêm cargo test khi có Rust)
desktop/scripts/install.sh            # đợt 4: build, ký ad-hoc, cài "Lịch Học Cá Nhân.app" vào ~/Applications
```

Sau mỗi đợt, giao diện mới dùng được qua trình duyệt tại `http://127.0.0.1:8080`; từ đợt 4 mở bằng
app trên Dock.

## Kịch bản kiểm chứng

| # | Kịch bản | Bước | Kết quả mong đợi | Liên quan |
|---|----------|------|------------------|-----------|
| D1 | Bố cục 3 cột | Chọn một danh sách khác, thoát và mở lại app (hoặc tải lại trang); mở `/`; có task hạn hôm nay, quá hạn, ngày mai, 5 ngày nữa, không hạn | Luôn mở vào Công việc → Hôm nay (không nhớ danh sách trước); số đếm Hôm nay/Ngày mai/7 ngày tới/Tất cả đúng; khối "Lịch hôm nay" có buổi học hôm nay; nhóm Quá hạn, Hôm nay; nhóm thu gọn được | US2, FR-008 đến FR-012 |
| D2 | Bảng chi tiết | Bấm một task; sửa tiêu đề, thêm khung giờ làm 19:00–21:00 Thứ Năm, bật Quan trọng; Esc | Lưu khi rời ô; dòng task hiện ★ và "T5 19:00–21:00"; giờ kết thúc ≤ bắt đầu bị báo lỗi dưới ô | US2, US6 |
| D3 | Thêm nhanh | Ở Hôm nay, Ngày mai, "Cá nhân", nhãn "Gấp": gõ tiêu đề + Enter | Mặc định đúng bảng `quickAddDefaults`; ô giữ con trỏ; Enter với ô trống không tạo gì | US3, SC-002 |
| D4 | Thùng rác | ⌘⌫ một task có nhãn, nhắc, khung giờ làm; bấm Hoàn tác; xoá lại; mở Thùng rác; Khôi phục | Task biến mất khỏi danh sách, lịch, Lời nhắc của Apple; Thùng rác ghi "Còn 30 ngày"; khôi phục đủ thông tin; Dọn sạch hỏi xác nhận | US7, SC-006 |
| D5 | Xoá hẳn sau 30 ngày | `docker compose exec db psql -U lichhoc -c "UPDATE tasks SET deleted_at = now() - interval '31 days' WHERE id = <id>"`; không mở app, chờ agent đồng bộ (≤ 1 giờ) hoặc mở Thùng rác | Task không còn | FR-030 |
| D6 | Emoji danh sách | Sửa danh sách "Cá nhân" → emoji 🏠; thử nhập "ab" | Emoji hiện trước tên; "ab" bị từ chối | FR-015 |
| D7 | Lịch tuần | Mở Lịch tuần có hôm nay; bấm một ngày tuần sau trong lịch tháng nhỏ ở cột bên; ẩn rồi hiện cột bên | Cột bên có lịch tháng nhỏ (hôm nay tô tròn, tuần đang xem tô nhạt) và lọc nhãn; bấm ngày → lịch chuyển tới tuần đó; Thứ Hai đầu tuần; số hôm nay tô tròn; đường kẻ đỏ + nhãn giờ đỏ; Cả ngày có task chỉ ngày; khối hạn chót 30 phút; khối khung giờ làm; buổi học có phòng; buổi đã huỷ/task xong mờ; 3 mục trùng giờ xếp cạnh nhau | US4, SC-004 |
| D8 | Kéo thả task | Kéo task có khung giờ làm sang ngày khác; kéo dãn; kéo task chỉ giờ hạn sang 17:00; kéo task chỉ ngày vào 10:00; Hoàn tác | Dữ liệu đúng bảng "Quy tắc kéo thả"; Lời nhắc của Apple đổi giờ trong 1 phút với task chỉ giờ hạn | US5, SC-005 |
| D9 | Tạo task bằng chọn vùng | Kéo vùng trống Thứ Tư 10:00–11:30; nhập tiêu đề; Enter. Lặp lại rồi Esc với tiêu đề trống | Task có khung giờ làm 10:00–11:30 Thứ Tư, hạn Thứ Tư; lần hai không tạo gì | FR-027 |
| D10 | Dời buổi học | Kéo buổi Thứ Hai sang 13:00 cùng ngày (xác nhận); kéo một buổi khác sang Thứ Bảy (xác nhận); huỷ một lần kéo | Chỉ buổi đó đổi; buổi dời ngày có "Đã dời" (ngày gốc); lịch chung của môn sửa phòng vẫn giữ buổi đã dời; huỷ thì khối về chỗ cũ; deadline tự tạo theo ngày mới | US5, FR-028 |
| D11 | Sáng/Tối | Đổi macOS Cài đặt hệ thống → Giao diện → Tối khi app đang mở | App đổi ngay, chữ đọc rõ | US8, SC-007 |
| D12 | Phím tắt | Thử từng phím trong [ui-shortcuts](contracts/ui-shortcuts.md); ⌘/ | Mọi phím hoạt động; bảng phím tắt liệt kê đủ | SC-008 |
| D13 | App trên Dock | Tắt OrbStack; mở app | Màn hình "Hãy mở OrbStack"; bấm Mở OrbStack → app tự vào màn hình chính trong vòng 5 giây sau khi backend sẵn sàng; không trình duyệt nào mở | US1, SC-001 |
| D14 | Cửa sổ | Đổi kích thước, vị trí; ⌘Q; mở lại; mở app lần hai; đóng cửa sổ rồi bấm Dock | Nhớ kích thước/vị trí; chỉ một cửa sổ; đóng cửa sổ không thoát app | FR-003 |
| D15 | Menu tiếng Việt | Mở từng menu; Cài đặt… ⌘, | Chữ tiếng Việt; ⌘, mở Cài đặt | FR-006 |
| D16 | Giữ chức năng cũ | Chạy lại quickstart 001 V1–V21 trong app mới | Pass (trừ phần feature 001 chưa làm) | SC-003, FR-036 |
| D17 | Offline | Tắt Wi-Fi; dùng app; kiểm tra kết nối của app bằng Activity Monitor → Mạng | Mọi thứ hoạt động; app chỉ kết nối 127.0.0.1 | SC-010 |


## Kết quả kiểm chứng (T093) — 2026-11-05

Chạy tự động được: `./scripts/test.sh` (pass toàn bộ), `./scripts/validate.sh` (20/20), đo thời gian và đếm
bấm bên dưới. Phần cần mắt/tay người dùng ghi ở cuối.

### Đo thời gian mở app (SC-001)

Đo từ lúc `open` app (đã thoát hẳn) tới lúc nginx nhận request `/api/today` đầu tiên từ app (đã có dữ liệu
trang; chưa gồm thời gian vẽ, và có sai số ~0,3 giây do chu kỳ dò log).

| Lần | Giây |
|-----|------|
| 1 (nguội) | 3,57 |
| 2 | 0,61 |
| 3 | 0,68 |
| Trung bình | 1,62 |

**Chưa đạt tiêu chí "cả 3 lần < 3 giây"**: lần mở đầu tiên sau khi app bị thoát chậm hơn 3 giây (khởi động
nguội của WKWebView/Gatekeeper); hai lần sau dưới 1 giây. Đo "tắt OrbStack → mở app → mở OrbStack (< 5 giây)"
chưa làm vì sẽ dừng dịch vụ của bạn.

### Đếm số lần bấm (SC-009)

Từ màn hình mặc định (Công việc → Hôm nay); gõ phím không tính là bấm.

| Chức năng | Đường đi | Số lần bấm |
|-----------|----------|-----------|
| Thêm task | bấm ô *Thêm công việc* (hoặc ⌘N: 0), gõ, Enter | ≤ 1 |
| Xem lịch tuần | Lịch (mặc định chế độ tuần) | 1 |
| Thêm môn | Môn học → Thêm môn → Lưu | 3 |
| Huỷ một buổi học | Lịch → bấm buổi → Huỷ buổi | 3 |
| Bật đồng bộ | Cài đặt (mở sẵn *Nhắc lịch và đồng bộ*) → công tắc | 2 |
| Khôi phục task từ Thùng rác | Thùng rác → Khôi phục | 2 |

**Đạt** (mọi chức năng ≤ 3).

### Kết quả theo kịch bản

| # | Kết quả | Ghi chú |
|---|---------|---------|
| D1–D3, D6 | ✅ bằng test giao diện (Vitest) + `validate.sh` (D6) | |
| D4 Thùng rác | ✅ `validate.sh` (30 ngày, khôi phục) | phần Lời nhắc Apple cần thử tay |
| D5 | ◐ logic được test (pytest) | chưa chạy lệnh SQL thủ công |
| D7–D9 Lịch, kéo thả | ✅ test Vitest (ánh xạ, dropToPatch, vùng chọn) | thao tác kéo thật cần thử tay |
| D10 Dời buổi học | ✅ `validate.sh` + test | |
| D11 Sáng/Tối | ⏳ cần thử tay | test tương phản màu (SC-007) pass |
| D12 Phím tắt | ✅ test `shortcuts.test.tsx` | |
| D13 App trên Dock | ◐ app mở và nạp giao diện từ 127.0.0.1:8080 (log nginx); màn hình "Hãy mở OrbStack" cần thử tay | |
| D14, D15 Cửa sổ, menu | ◐ ⌘Q hoạt động; nhớ cửa sổ, menu cần thử tay | |
| D16 Giữ chức năng cũ | ✅ phần tự động của V1–V10, V17–V19 (xem `validation.md` của feature 001) | |
| D17 Offline | ◐ `lsof` không thấy kết nối nào của app; dist/backend không gọi URL ngoài | chưa tắt Wi-Fi thật |

### Rà constitution (T094)

- Không có URL ngoài được gọi: `frontend/dist` chỉ có URL không gọi (namespace XML/SVG, chuỗi trong thư viện);
  `desktop/` chỉ gọi `127.0.0.1:8080`; cổng Docker chỉ mở trên `127.0.0.1`.
- Không còn chuỗi tiếng Anh hiển thị trong `frontend/src` (ngoài `i18n/vi.ts`) và `message` của `ApiError`.
- Phụ thuộc: mọi gói trong `frontend/package.json` đều được dùng; `Cargo.toml` chỉ có tauri, hai plugin và serde.
