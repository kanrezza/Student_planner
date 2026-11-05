# Lịch Học Cá Nhân

Ứng dụng quản lý **công việc và lịch học** cho một người dùng trên Mac: danh sách việc cần làm, học kỳ và
môn học lặp hàng tuần, lịch ngày/tuần/tháng có kéo thả, lịch thi, nhập thời khoá biểu và lịch thi từ
**ảnh chụp** (nhận diện hoàn toàn offline), và nhắc việc/lịch học trên Mac và iPhone.

Toàn bộ chạy **trên máy bạn**, chỉ kết nối `127.0.0.1`; không có tài khoản, không có cập nhật tự động, không
có telemetry. Giao diện hoàn toàn bằng tiếng Việt.

## Thành phần

| Thành phần | Công nghệ | Chạy ở đâu |
|------------|-----------|------------|
| Backend + CSDL | Flask, PostgreSQL 16, EasyOCR | Docker (OrbStack) |
| Giao diện | React + Tailwind, FullCalendar | Docker (nginx, cổng `127.0.0.1:8080`) |
| App macOS "Lịch Học Cá Nhân" | Tauri 2 (cửa sổ riêng, icon Dock) | `/Applications` |
| Agent nhắc lịch (`LichHocAgent`) | Python + EventKit | Chạy nền, đẩy vào Lịch/Lời nhắc của Apple |

## Yêu cầu

- macOS 14 trở lên (Apple Silicon hoặc Intel).
- [OrbStack](https://orbstack.dev) (hoặc Docker Desktop), bật "Start at login".
- Node 22 (chỉ để chạy test frontend).
- Python 3.11 của Homebrew (`brew install python@3.11`), chỉ để build agent nhắc lịch.
- Rust (`rustup`) và Xcode Command Line Tools, **chỉ khi build app macOS**.
- **Internet chỉ cần ở lần build/cài đầu** (tải image Docker, gói npm/pip/cargo, model EasyOCR). Sau đó
  mọi thứ chạy offline.

## Chạy

```bash
docker compose up -d --build     # lần đầu vài phút (image backend có PyTorch + EasyOCR)
open http://127.0.0.1:8080       # dùng trên trình duyệt
```

Các lần sau chỉ cần `docker compose up -d` (các dịch vụ cũng tự chạy lại khi OrbStack khởi động).

### App macOS

```bash
desktop/scripts/install.sh               # build, ký ad-hoc, chép vào /Applications (xoá bản cũ ở ~/Applications)
desktop/scripts/install.sh --uninstall   # gỡ
```

Mở bằng Spotlight ("Lịch Học Cá Nhân") rồi chọn **Tuỳ chọn → Giữ trong Dock** ở menu chuột phải icon Dock.
Nếu OrbStack chưa chạy, app hiện **"Hãy mở OrbStack"** (nút *Mở OrbStack*, *Thử lại*) và tự vào màn hình
chính khi dịch vụ sẵn sàng. Đóng cửa sổ chỉ ẩn app; ⌘Q mới thoát. Lần đầu mở, macOS có thể báo nhà phát
triển không xác định (chữ ký ad-hoc): chuột phải vào app → **Mở**.

### Agent nhắc lịch (iPhone nhận nhắc khi Mac gập)

```bash
mac-agent/scripts/install.sh              # build LichHocAgent.app, cài LaunchAgent, chạy ngay
mac-agent/scripts/install.sh --uninstall
```

Vào **Cài đặt → Nhắc lịch và đồng bộ → Bật** và cho phép khi macOS hỏi quyền Lịch và Lời nhắc. Cần iCloud
bật cho Lịch và Lời nhắc để iPhone nhận. Khi build lại agent, chữ ký ad-hoc đổi nên macOS có thể hỏi lại
quyền. Sau khi cập nhật backend, chạy lại `install.sh` để agent dùng định dạng feed mới.

## Dùng

- **Công việc**: Hôm nay, Ngày mai, 7 ngày tới, Tất cả, các danh sách riêng, **Thùng rác** (giữ task 30 ngày
  rồi xoá hẳn). Gõ vào ô *Thêm công việc* + Enter; bấm task để mở bảng chi tiết (khung giờ làm, nhãn, nhắc).
- **Lịch**: ngày/tuần/tháng; kéo thả task, kéo dãn khung giờ làm, kéo chọn vùng trống để tạo task, kéo
  buổi học sang giờ/ngày khác (có xác nhận).
- **Môn học**: học kỳ, thêm một hoặc nhiều môn, ca học; **Nhập từ ảnh** cho thời khoá biểu.
- **Lịch thi**: thêm tay hoặc nhập từ ảnh "Lịch thi cá nhân"; cảnh báo trùng giờ; nhắc theo mức *Quan trọng*.
- **Nhập từ ảnh**: kéo thả ảnh PNG/JPEG/HEIC (≤ 20 MB), chờ tới ~1 phút, kiểm tra bảng xem trước (ô vàng là
  chưa chắc chắn), rồi Lưu. Ảnh không được lưu; cột họ tên/MSSV của bảng lịch thi bị bỏ qua.
- **Cài đặt**: nhắc lịch và đồng bộ, bản tóm tắt hằng ngày, mốc *Quan trọng*, học kỳ, ca học, nhãn, danh
  sách, tự tạo deadline. Giao diện sáng/tối theo macOS.

### Phím tắt

| Phím | Việc |
|------|------|
| ⌘N | Thêm công việc mới |
| ⌘F | Tìm kiếm (task, danh sách, nhãn, môn học, buổi học, buổi thi; không cần gõ dấu) |
| ⌘1 … ⌘5 | Công việc, Lịch, Môn học, Lịch thi, Cài đặt |
| ⌘, / ⌘/ | Cài đặt / bảng phím tắt |
| ⌘⌫ | Chuyển task vào Thùng rác |
| ↩ / ⌘↩ | Mở chi tiết / đánh dấu xong |
| Esc | Đóng bảng, bỏ chọn |
| ↑ ↓ | Chọn task trước/sau |
| ← → | Tuần/tháng trước/sau (Lịch) |
| T, D, W, M | Lịch: hôm nay, ngày, tuần, tháng |

Đầy đủ: ⌘/ trong app, hoặc `specs/002-redesign-macos-app/contracts/ui-shortcuts.md`.

## Dữ liệu nằm ở đâu, sao lưu

- CSDL ở volume Docker **`lichhoc_pgdata`**; trong OrbStack: `~/OrbStack/docker/volumes/lichhoc_pgdata`.
- Trạng thái cửa sổ app: `~/Library/Application Support/vn.lichhoc.desktop`. Agent:
  `~/Library/Application Support/LichHocAgent`, log `~/Library/Logs/LichHocAgent/agent.log`.

> ⚠️ **`docker compose down -v` xoá toàn bộ dữ liệu.** Dùng `docker compose down` (không `-v`) để dừng.

### Sao lưu tự động (Cài đặt → Sao lưu)

- Mỗi ngày lúc **21:00** (đổi được) agent `LichHocAgent` tự sao lưu toàn bộ dữ liệu thành một file
  `LichHoc-YYYY-MM-DD-HHMM-<loại>.lhbackup` (loại: `tu-dong`, `thu-cong`, `truoc-khoi-phuc`).
  Máy tắt hoặc ngủ lúc đến giờ thì sao lưu bù ngay khi có thể (chỉ một bản bù).
- Mặc định ghi vào `iCloud Drive/Lịch Học Cá Nhân/Sao lưu` (macOS tự đưa lên iCloud); đổi sang thư
  mục khác, ví dụ ổ SSD rời, ngay trong trang Sao lưu. Giữ 14 bản gần nhất (chỉnh được 1–365).
  Ổ không có thì bỏ qua, cảnh báo nhẹ và thử lại; quá 3 ngày chưa sao lưu được thì có thông báo macOS.
- **Khôi phục**: bấm "Khôi phục" ở một bản trong danh sách (hoặc "Chọn bản sao lưu khác…" sau khi
  cài lại máy). App tự sao lưu dữ liệu hiện tại thành bản `truoc-khoi-phuc` trước khi thay.
- Lần đầu macOS hỏi quyền cho LichHocAgent ghi vào iCloud Drive / ổ rời và gửi thông báo: bấm "Cho phép".
  Nếu bị từ chối: Cài đặt hệ thống → Quyền riêng tư & Bảo mật → Tệp và thư mục.
- Log của sao lưu nằm cùng file log của agent: `~/Library/Logs/LichHocAgent/agent.log`.
- Script `backup.sh`/`restore.sh` ở trên vẫn dùng được để sao lưu thủ công.

```bash
./scripts/backup.sh                              # → backups/lichhoc-YYYYmmdd-HHMM.dump
./scripts/restore.sh backups/lichhoc-....dump    # khôi phục (hỏi xác nhận, ghi đè dữ liệu hiện tại)
```

(Thủ công: `docker compose exec -T db pg_dump -U lichhoc -Fc lichhoc > lichhoc.dump`, khôi phục bằng
`pg_restore --clean --if-exists -U lichhoc -d lichhoc`.) Thư mục `backups/` không được đưa lên git.

## Chạy test

```bash
./scripts/test.sh            # (hoặc: make test) toàn bộ lint + test: backend, frontend, agent, app Tauri, lưu trữ
./scripts/test.sh --ocr      # thêm OCR thật trên ảnh mẫu (chậm, ~4 phút)
./scripts/validate.sh        # chạy các kịch bản quickstart tự động được trên database tạm (~3 phút)
docker compose run --rm backend flask seed-demo   # dữ liệu mẫu: 6 môn + 200 task (đo hiệu năng)
```

Kịch bản kiểm chứng thủ công: `specs/001-task-class-scheduler/quickstart.md` (V1–V21) và
`specs/002-redesign-macos-app/quickstart.md` (D1–D17); kết quả lần chạy gần nhất ở `validation.md`.

## Xử lý sự cố

| Hiện tượng | Cách xử lý |
|------------|-----------|
| App hiện "Hãy mở OrbStack" | Mở OrbStack, đợi vài giây; hoặc `docker compose up -d` trong thư mục dự án |
| Trang không mở được ở `127.0.0.1:8080` | `docker compose ps`; xem log: `docker compose logs backend web` |
| Agent không chạy / không đồng bộ | Xem `~/Library/Logs/LichHocAgent/agent.log`; cài lại bằng `mac-agent/scripts/install.sh`; kiểm tra Cài đặt → trạng thái đồng bộ |
| macOS từ chối quyền Lịch/Lời nhắc | Cài đặt hệ thống → Quyền riêng tư & Bảo mật → Lịch / Lời nhắc → bật `LichHocAgent`, rồi cài lại agent |
| Không thấy Lịch trên iPhone | Bật iCloud cho Lịch và Lời nhắc; nếu Mac chỉ có nguồn "Trên máy Mac" thì iPhone không nhận |
| Nhận diện ảnh quá lâu (> 1 phút) | Ảnh quá lớn/mờ: chụp lại ở cỡ màn hình thường; backend dùng CPU nên mất 25–60 giây là bình thường |
| Nhận diện sai dấu | Sửa trực tiếp ở bảng xem trước (ô vàng là chưa chắc chắn) |

## Cấu trúc thư mục

`backend/` (Flask, OCR, migration) · `frontend/` (React) · `desktop/` (app Tauri) · `mac-agent/` (agent nhắc
lịch) · `scripts/` (test, sao lưu, kiểm chứng) · `samples/` (ảnh giả lập) · `specs/` (đặc tả, kế hoạch,
nhiệm vụ của feature 001 và 002).
