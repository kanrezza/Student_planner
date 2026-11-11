# Contract: lệnh của app macOS (Tauri) — feature 005

Capability mới `attachments` (`desktop/src-tauri/capabilities/attachments.json`), chỉ cho trang
`http://127.0.0.1:8080/*` trong cửa sổ `main`; không thêm plugin. Mọi lệnh chỉ gọi `http://127.0.0.1:8080`.

| Lệnh | Tham số | Trả | Ghi chú |
|------|---------|-----|---------|
| `open_attachment` | `id: number` | `()` | Lấy metadata; `is_executable` → lỗi "Không mở trực tiếp file có thể chạy chương trình". Tải về `~/Library/Caches/<bundle-id>/attachments/<sha256>/<tên>` (dùng lại nếu đã có, kiểm tra kích thước) rồi `/usr/bin/open` |
| `save_attachment` | `id: number` | `path: string` | Lưu vào `~/Downloads/<tên>`, trùng tên thêm " (2)"…; dùng `reveal_in_finder` có sẵn để hiện |
| `clipboard_file_paths` | — | `string[]` | Đường dẫn file đang chép trong Finder (NSPasteboard `public.file-url`); rỗng nếu không có |
| `upload_paths` | `owner_type, owner_id, paths: string[]` | `{uploaded: number, errors: [{name, message}]}` | Gọi `POST /api/attachments` từng file; thư mục → lỗi "Chỉ gắn được file, không gắn thư mục" |

Thư mục cache được dọn khi app khởi động: xoá mục cũ hơn 7 ngày. Lỗi của lệnh trả chuỗi tiếng Việt để giao diện hiện
thẳng.

Trên trình duyệt (không có `window.__TAURI__`): Mở → tải về; Dán chỉ nhận ảnh trong clipboard.
