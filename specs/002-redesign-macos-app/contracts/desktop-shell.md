# Contract: App macOS (Tauri) ↔ giao diện web ↔ backend

**Bên tham gia**: app `Lịch Học Cá Nhân.app` (Tauri 2, thư mục `desktop/`), trang chờ đóng gói trong
app (`desktop/splash/`), giao diện React do service `web` phục vụ tại `http://127.0.0.1:8080/`, và
backend qua `http://127.0.0.1:8080/api`. Cơ chế xem [research R1–R3](../research.md).

## 1. Khởi động và kiểm tra kết nối

| Bước | Hành vi |
|------|---------|
| Mở app | Cửa sổ chính (bundle id `vn.lichhoc.desktop`) hiện trang chờ nội bộ: "Đang kết nối…" |
| Kiểm tra | Rust gửi `GET /api/health` tới `127.0.0.1:8080` (timeout 1 giây) ngay lập tức rồi mỗi 2 giây |
| Thành công (`200`) | Điều hướng cửa sổ chính tới `http://127.0.0.1:8080/` và dừng kiểm tra |
| Thất bại lần đầu | Trang chờ chuyển sang nội dung "Hãy mở OrbStack" (tiêu đề, 2 dòng giải thích, nút **Mở OrbStack**, **Thử lại**, dòng "Đang thử kết nối lại…") |
| Bấm Mở OrbStack | `invoke('open_orbstack')` → Rust chạy `open -a OrbStack`; không tìm thấy OrbStack → trả lỗi, trang chờ hiện "Không tìm thấy OrbStack trên máy. Hãy cài OrbStack rồi chạy `docker compose up -d` trong thư mục dự án." |
| Bấm Thử lại | `invoke('retry_now')` → kiểm tra ngay |

Trang chờ nhận trạng thái qua sự kiện Tauri `connection-status` với payload
`{"state": "connecting" | "waiting_for_backend" | "orbstack_missing"}`.

**Quyền (capability)**: chỉ trang nội bộ của app (`local: true`) được gọi `open_orbstack`,
`retry_now` và nghe sự kiện; trang tải từ `http://127.0.0.1:8080` không có quyền gọi lệnh Tauri nào.

## 2. Mất kết nối khi đang dùng

Giao diện React tự xử lý (không cần Tauri): khi các truy vấn lỗi mạng liên tiếp, hiện dải thông báo
"Mất kết nối với dữ liệu trên máy — đang thử lại…" và tự ẩn khi truy vấn thành công.

## 3. Menu macOS (tiếng Việt)

| Menu | Mục | Phím | Hành vi |
|------|-----|------|---------|
| Lịch Học Cá Nhân | Giới thiệu Lịch Học Cá Nhân | | hộp giới thiệu (tên, phiên bản) |
| | Cài đặt… | ⌘, | `eval("window.lichhoc?.navigate('/cai-dat')")` |
| | Ẩn Lịch Học Cá Nhân · Ẩn ứng dụng khác · Hiện tất cả | ⌘H · ⌥⌘H | mục hệ thống |
| | Thoát Lịch Học Cá Nhân | ⌘Q | thoát app (không dừng Docker, agent) |
| Sửa | Hoàn tác, Làm lại, Cắt, Chép, Dán, Chọn tất cả | ⌘Z, ⇧⌘Z, ⌘X, ⌘C, ⌘V, ⌘A | mục hệ thống |
| Cửa sổ | Thu nhỏ, Phóng to | ⌘M | mục hệ thống |
| Trợ giúp | Phím tắt | ⌘/ | `eval("window.lichhoc?.showShortcuts()")` |

## 4. API toàn cục do giao diện React đăng ký

```ts
window.lichhoc = {
  navigate(path: string): void;     // ví dụ '/cai-dat', '/lich', '/cong-viec/hom-nay'
  showShortcuts(): void;            // mở bảng phím tắt
};
```

Trang chạy được bình thường trong trình duyệt khi không có app (đối tượng vẫn được đăng ký nhưng
không ai gọi).

## 5. Cửa sổ

- Một cửa sổ chính, kích thước mặc định 1280 × 820, tối thiểu 720 × 520; nhớ kích thước và vị trí
  (plugin window-state).
- Mở app lần hai → đưa cửa sổ đang có lên trước (plugin single-instance).
- Đóng cửa sổ (nút đỏ hoặc ⌘W) → ẩn cửa sổ, app vẫn chạy; bấm icon Dock → hiện lại.
- Thanh tiêu đề trong suốt (`titleBarStyle: Transparent`), vẫn kéo được cửa sổ; nội dung nằm dưới
  thanh tiêu đề nên `--titlebar-inset` giữ 0 (xem research R3, quyết định T088). Trang nhận biết đang
  chạy trong app qua `navigator.userAgent` chứa `LichHocDesktop`, do app đặt.

## 6. Không kết nối ra ngoài

App chỉ kết nối `127.0.0.1:8080` (constitution IV). Không có cập nhật tự động, không telemetry;
plugin Tauri chỉ dùng: window-state, single-instance.
