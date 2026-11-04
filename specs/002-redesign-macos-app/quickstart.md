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
