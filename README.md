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
mac-agent/scripts/install.sh              # cài LichHocAgent.app + Python riêng vào ~/Library/Application Support/LichHocAgent, cài LaunchAgent, chạy ngay (tháo SSD vẫn chạy)
mac-agent/scripts/install.sh --uninstall
```

Vào **Cài đặt → Nhắc lịch và đồng bộ → Bật** và cho phép khi macOS hỏi quyền Lịch và Lời nhắc. Cần iCloud
bật cho Lịch và Lời nhắc để iPhone nhận. Khi build lại agent, chữ ký ad-hoc đổi nên macOS có thể hỏi lại
quyền. Sau khi cập nhật backend, chạy lại `install.sh` để agent dùng định dạng feed mới.

## Dùng

- **Công việc**: Hôm nay, Ngày mai, 7 ngày tới, Tất cả, các danh sách riêng, **Thùng rác** (giữ task 30 ngày
  rồi xoá hẳn). Gõ vào ô *Thêm công việc* + Enter; bấm task để mở bảng chi tiết (khung giờ làm, nhãn, nhắc).
- **Thêm nhanh bằng câu tiếng Việt**: gõ cả câu vào ô *Thêm công việc*, phần hiểu được sẽ được tô sáng và
  hiện trước kết quả (bấm vào chữ tô sáng để giữ nó làm chữ thường). Không cần gõ dấu, mọi xử lý chạy trên máy.

  | Gõ | Hiểu là |
  |----|---------|
  | `mai`, `ngày mai`, `mốt`, `thứ 6`, `thứ 6 tuần sau`, `20/11`, `20/11/2027` | ngày hạn |
  | `9h`, `9h30`, `9 giờ tối`, `9 rưỡi`, `tối nay`, `sáng mai` | giờ hạn (giờ 1–5 không ghi buổi là chiều) |
  | `#Gấp` · `~Học tập` | nhãn (nhãn chưa có sẽ được tạo) · danh sách |
  | `*` hoặc `quan trọng` · `!cao` `!tb` `!thấp` | Quan trọng · mức ưu tiên |
  | `hằng ngày`, `mỗi 3 ngày`, `thứ 2 hàng tuần`, `ngày 5 hằng tháng` | lặp lại |
  | `từ 6/11 đến 11/11`, `6/11 - 11/11`, `đến hết 20/11` | khoảng ngày: có cụm lặp thì lần đầu là ngày bắt đầu và lặp kết thúc vào ngày cuối; không có thì hạn là ngày cuối, ghi chú "Bắt đầu: …" |

  Ví dụ: `Nộp bài QTDA thứ 6 9h #Gấp * !cao`, `Họp lớp thứ 2 hàng tuần 7h`.
- **Tìm kiếm** (⌘F): task, danh sách, nhãn, môn học, buổi học, buổi thi, tên file đính kèm; không phân biệt dấu và hoa thường,
  tô sáng chỗ khớp, có công tắc *Gồm cả đã hoàn thành*. Esc để thoát và quay lại màn hình trước.
- **Bảng Kanban**: ở trang Công việc bấm *Danh sách | Bảng* (nhớ lựa chọn). Bảng có 3 cột *Chưa làm / Đang làm /
  Xong*; kéo thẻ giữa các cột để đổi trạng thái, kéo lên xuống để sắp thứ tự (lưu ngay). Kéo sang *Xong* giống
  tick hoàn thành (task lặp vẫn sinh lần kế tiếp ở *Chưa làm*; có nút *Hoàn tác*). Cột *Xong* mặc định chỉ hiện 7
  ngày gần nhất (*Hiện tất cả* để xem hết). Lọc theo danh sách, nhãn, môn học. Thẻ hiện hạn chót, nhãn màu, ★,
  biểu tượng lặp và số file đính kèm. Bàn phím: mũi tên chọn thẻ, **⌘←/⌘→** đổi cột, **⌘↑/⌘↓** đổi chỗ, **↩** mở
  chi tiết, **X** Xong/bỏ Xong, **Space** nhấc/thả thẻ (xem bảng phím tắt ⌘/).
- **File đính kèm**: gắn file (PDF, ảnh, Word, PowerPoint, Excel…) vào **task, môn học, buổi học, buổi thi** bằng
  kéo thả vào mục *File đính kèm*, nút *Thêm file* hoặc **⌘V** (ảnh chụp màn hình, file chép trong Finder).
  Mỗi file tối đa **50 MB** (đổi 1–500 MB ở Cài đặt → File đính kèm). Ảnh và PDF xem ngay trong app; loại khác
  *Mở* bằng ứng dụng mặc định của macOS; *Tải về* lưu vào thư mục Tải về. File có thể chạy chương trình
  (.app, .command, .sh, .pkg…) chỉ cho tải về, app không mở trực tiếp. File trùng nội dung chỉ lưu một bản. Xoá
  task vào Thùng rác thì file đi theo và khôi phục được; xoá hẳn thì file bị xoá nếu không còn nơi nào dùng. Xoá
  môn, buổi thi hoặc học kỳ có file sẽ hỏi lại và nêu số file. Tên file tìm được bằng ⌘F.
- **Task lặp lại**: trong bảng chi tiết chọn *Lặp lại* (hằng ngày, mỗi N ngày, hằng tuần chọn nhiều thứ, hằng
  tháng vào ngày D; kết thúc không/vào ngày/sau N lần). Hoàn thành một lần thì lần kế tiếp xuất hiện; sửa hoặc
  xoá sẽ hỏi *Chỉ lần này* hay *Lần này và các lần sau*. Lịch và bản tóm tắt hằng ngày hiện các lần dự kiến;
  Lời nhắc/iPhone luôn theo lần hiện tại.
- **Lịch**: ngày/tuần/tháng; kéo thả task, kéo dãn khung giờ làm, kéo chọn vùng trống để tạo task, kéo
  buổi học sang giờ/ngày khác (có xác nhận).
- **Môn học**: học kỳ, thêm một hoặc nhiều môn, ca học; mỗi môn có một hoặc nhiều lịch lặp hằng tuần
  (thứ, khoảng ngày, ca/giờ, phòng); **Nhập lịch** từ ảnh hoặc file PDF thời khoá biểu.
- **Lịch thi**: thêm tay hoặc nhập từ ảnh "Lịch thi cá nhân"; cảnh báo trùng giờ; nhắc theo mức *Quan trọng*.
- **Nhập lịch**: dán (⌘V), kéo thả hoặc chọn ảnh PNG/JPEG/HEIC hoặc file PDF (≤ 20 MB).
  - *Ảnh*: chờ tới ~1 phút, kiểm tra bảng xem trước (ô vàng là chưa chắc chắn), rồi Lưu. Cột họ tên/MSSV
    của bảng lịch thi bị bỏ qua.
  - *PDF thời khoá biểu chính thức* (file có chữ, không phải ảnh quét): đọc cả học kỳ trong vài giây, không
    cần OCR. Bản xem trước hiện học kỳ đề xuất, từng môn và các lịch lặp (đổi tiết sang giờ theo **bảng
    tiết**); bỏ chọn hoặc sửa được từng ô, rồi Lưu. Nhập lại file mới thì môn đã có được nhận ra và chỉ
    cập nhật phần từ hôm nay trở đi (buổi đã qua, đã huỷ hoặc sửa riêng giữ nguyên). Phòng trực tuyến
    được đề xuất nhãn E-Learning.
  - File chỉ được xử lý trong bộ nhớ, không được lưu; họ tên, mã sinh viên, lớp trong PDF bị bỏ ngay
    khi đọc. Không đưa file thật vào git: thư mục `samples/` bị chặn trừ `samples/synthetic/` (file giả lập).
- **Bảng tiết** (Cài đặt → Ca học): giờ từng tiết suy từ 4 ca (50 phút, nghỉ 5 phút), tiết 16–18 mặc
  định 21:05–22:00; sửa tay được, thêm tiết 13–30. Dùng để đổi "Tiết 4–6" trong PDF sang giờ.
- **Tên môn chuẩn** (Cài đặt → Tên môn chuẩn): tên lấy từ PDF, giúp tự sửa tên môn khi nhập từ ảnh; xoá
  được toàn bộ danh sách.
- **Cài đặt**: nhắc lịch và đồng bộ, bản tóm tắt hằng ngày, mốc *Quan trọng*, học kỳ, ca học (kèm bảng
  tiết), nhãn, danh sách, tự tạo deadline, tên môn chuẩn, sao lưu. Giao diện sáng/tối theo macOS.

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

Đầy đủ: ⌘/ trong app, hoặc `specs/002-redesign-macos-app/contracts/ui-shortcuts.md` (phím tắt thêm ở feature 003:
`specs/003-backup-nl-recurring-search/contracts/ui.md`).

## Dữ liệu nằm ở đâu, sao lưu

- CSDL ở volume Docker **`lichhoc_pgdata`**; trong OrbStack: `~/OrbStack/docker/volumes/lichhoc_pgdata`.
- File đính kèm ở volume Docker **`lichhoc_attachments`** (`~/OrbStack/docker/volumes/lichhoc_attachments`), mỗi file
  đặt tên theo SHA-256 nội dung. Nằm trên ổ trong của Mac, **không** phụ thuộc thư mục dự án hay ổ SSD rời. Xem dung
  lượng ở Cài đặt → File đính kèm (hoặc `docker system df -v`).
- Trạng thái cửa sổ app: `~/Library/Application Support/vn.lichhoc.desktop`. Agent:
  `~/Library/Application Support/LichHocAgent`, log `~/Library/Logs/LichHocAgent/agent.log`.

> ⚠️ **`docker compose down -v` xoá toàn bộ dữ liệu**, gồm cả `lichhoc_pgdata` và `lichhoc_attachments`. Dùng
> `docker compose down` (không `-v`) để dừng.

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
- Bản sao lưu `.lhbackup` (định dạng 2) gồm **cả database lẫn file đính kèm**; khôi phục đưa file trở lại. Khi tổng
  file đính kèm vượt ngưỡng (mặc định 1 GB) có cảnh báo nhẹ trong Cài đặt → Sao lưu và thông báo macOS (tối đa 1
  lần/ngày) kèm dung lượng ước tính mỗi bản.
- Script `backup.sh`/`restore.sh` ở dưới **chỉ sao lưu database**, không gồm file đính kèm — hãy dùng sao lưu tự
  động/`.lhbackup` (Cài đặt → Sao lưu → Sao lưu ngay) khi cần giữ cả file.

```bash
./scripts/backup.sh     # → ~/Library/Application Support/LichHocAgent/backups/lichhoc-YYYYmmdd-HHMM.dump
./scripts/restore.sh "<file .dump>"   # khôi phục (hỏi xác nhận, ghi đè dữ liệu hiện tại)
```

(Thủ công: `docker compose exec -T db pg_dump -U lichhoc -Fc lichhoc > lichhoc.dump`, khôi phục bằng
`pg_restore --clean --if-exists -U lichhoc -d lichhoc`.) Đổi nơi lưu bằng biến `LICHHOC_BACKUP_DIR`; script không ghi gì vào thư mục dự án.

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
| PDF báo "không có chữ" | File là ảnh quét: dùng Nhập lịch bằng ảnh chụp màn hình thay cho PDF |
| PDF báo "có mật khẩu" | Mở khoá file rồi xuất lại PDF không mật khẩu |
| "Ổ đĩa không đủ chỗ" khi gắn file | Giải phóng dung lượng trên Mac (volume Docker nằm trên ổ trong); xoá bớt file ở Cài đặt → File đính kèm |
| "Không xem trước được file này" (PDF/ảnh) | File hỏng hoặc có mật khẩu: vẫn *Tải về* hoặc *Mở bằng ứng dụng khác* được |
| Nhận diện sai dấu | Sửa trực tiếp ở bảng xem trước (ô vàng là chưa chắc chắn) |

## Cấu trúc thư mục

`backend/` (Flask, OCR, migration) · `frontend/` (React) · `desktop/` (app Tauri) · `mac-agent/` (agent nhắc
lịch) · `scripts/` (test, sao lưu, kiểm chứng) · `samples/` (ảnh giả lập) · `specs/` (đặc tả, kế hoạch,
nhiệm vụ của các feature 001–004).
