# Implementation Plan: Quản lý công việc và lịch học cá nhân

**Branch**: `001-task-class-scheduler` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-task-class-scheduler/spec.md`

## Summary

Ứng dụng cá nhân quản lý task, lịch học và lịch thi, giao diện tiếng Việt. Ứng dụng chạy trên Mac qua Docker
Compose (OrbStack), gồm:
- `db`: PostgreSQL, lưu trong named volume.
- `backend`: Flask REST API; nhận diện ảnh offline bằng EasyOCR, model được tải sẵn vào image lúc
  build.
- `web`: React + Vite, phục vụ bằng nginx, chỉ mở trên `127.0.0.1`.

Ngoài Docker có `mac-agent` (Python + PyObjC, đóng gói `.app`, tự chạy khi đăng nhập). Agent
long-poll backend và đối chiếu buổi học, buổi thi và task vào Lịch và Lời nhắc của Apple kèm báo
trước (mục "Quan trọng" có nhiều mốc; buổi thi mặc định quan trọng, thêm mốc 7 ngày), cùng bản tóm
tắt hằng ngày (sự kiện cả ngày có lời báo lúc 05:00, ghi sẵn 14 ngày), để iCloud đồng bộ sang
iPhone. Thông báo trình duyệt chỉ là dự phòng khi chưa bật đồng bộ.

Lõi nghiệp vụ được viết thành các hàm thuần, có test pytest:
- Sinh buổi học lặp.
- Ca học.
- Phát hiện trùng.
- Quy tắc deadline tự tạo.
- Phân tích bố cục ảnh: lưới tuần của lịch học và bảng lịch thi, tự nhận biết loại ảnh (R14).
- Đối chiếu đồng bộ.

Hai rủi ro lớn nhất được kiểm chứng bằng spike trước: độ chính xác EasyOCR tiếng Việt, và quyền
EventKit qua PyObjC ([research R2, R4](research.md)).

## Technical Context

**Language/Version**: Python 3.12 (backend, trong Docker); Python 3.11 Homebrew dạng framework
(mac-agent, vì py2app cần Python framework, xem research R4); TypeScript 5 + React 18 (frontend);
Node 22 LTS (chỉ dùng lúc build)

**Primary Dependencies**:
- Backend: Flask 3, Flask-SQLAlchemy 3.1 (SQLAlchemy 2), Flask-Migrate 4, psycopg 3, pydantic 2
  (validate request), gunicorn, EasyOCR 1.7 + PyTorch CPU, Pillow + pillow-heif, rapidfuzz.
- Frontend: Vite, React Router, TanStack Query, FullCalendar 6 (daygrid/timegrid/interaction,
  locale `vi`).
- Agent: pyobjc-framework-EventKit, py2app, requests.

**Storage**: PostgreSQL 16 trong named volume `lichhoc_pgdata`. Agent lưu `state.json` cục bộ (chỉ
ID lịch và fingerprint).

**Testing**: pytest (backend, agent); Vitest + Testing Library (logic frontend); ruff, ESLint,
Prettier.

**Target Platform**: macOS 14+ với OrbStack (container Linux arm64/amd64); trình duyệt Safari hoặc
Chrome trên Mac; iPhone nhận nhắc qua iCloud.

**Project Type**: Web application (frontend + backend) cộng một tiến trình nền macOS.

**Performance Goals**:
- Trang Hôm nay < 2 giây với 6 môn + 200 task (SC-005).
- Chuyển chế độ xem và lọc nhãn < 1 giây (SC-006, SC-016).
- Đồng bộ sang Lịch < 5 giây sau khi lưu (SC-018).
- Nhận diện một ảnh toàn màn hình ≤ 60 giây trên CPU.

**Constraints**:
- Không kết nối ra ngoài máy lúc chạy; cổng chỉ mở trên `127.0.0.1`; model OCR có sẵn trong image.
- Toàn bộ chữ hiển thị là tiếng Việt; múi giờ Asia/Ho_Chi_Minh.
- Dữ liệu không mất qua `down`/`up` hoặc khởi động lại máy.

**Scale/Scope**:
- 1 người dùng.
- Khoảng 2 học kỳ/năm × 6–8 môn × 15 tuần ≈ 100 buổi mỗi học kỳ; vài trăm task.
- Khoảng 11 màn hình: Hôm nay, Lịch, Task, Môn học, Lịch thi, Nhập ảnh, Học kỳ, Ca, Nhãn, Danh
  sách, Cài đặt. Vài chục buổi thi mỗi học kỳ.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Đối chiếu với constitution v2.2.0:

| Nguyên tắc | Cách plan đáp ứng | Kết quả |
|------------|-------------------|---------|
| **I. Code dễ đọc** | Lõi nghiệp vụ là hàm thuần nhỏ trong `services/` và `ocr/`; ruff (lint + format), ESLint + Prettier bắt buộc; tên tiếng Anh rõ nghĩa | PASS |
| **II. Test chức năng chính** | pytest cho sinh buổi, ca, trùng, deadline tự tạo, parser ảnh, API; test đối chiếu của agent với `CalendarStore` giả; Vitest cho nhắc dự phòng; ảnh mẫu trong `backend/tests/fixtures/timetables/`. **Toàn bộ** lint + test chạy bằng một lệnh duy nhất `./scripts/test.sh` (hoặc `make test`) | PASS |
| **III. Giao diện đơn giản** | Hôm nay là màn hình mặc định; mỗi màn hình một mục đích; bảng 12 màu cố định; không dùng UI kit lớn; FullCalendar chỉ cho lịch | PASS |
| **IV. Chạy offline trên Mac** | Mọi thứ chạy trên Mac. Kết nối chỉ trên localhost (`127.0.0.1:8080`; `db` và `backend` không mở cổng ra ngoài). EasyOCR `download_enabled=False`, model nằm trong image. Không dùng CDN hay font ngoài. iCloud chỉ qua Lịch/Lời nhắc do agent ghi, khi người dùng bật, chỉ các trường tối thiểu (buổi thi không gửi số báo danh, hình thức thi; bản tóm tắt chỉ có ca, tên môn, giờ, phòng và số lượng task, không có tiêu đề task), chỉ trong lịch và danh sách riêng (contract calendar-sync §2, §4). Ảnh lịch thi: cột họ tên, mã số sinh viên bị loại ngay ở bước bố cục, không log, không lưu (R14, FR-061) | PASS, có ghi chú ¹ |
| **V. Dữ liệu bền vững** | PostgreSQL với transaction, `fsync` bật, named volume; README ghi vị trí volume và cách sao lưu/khôi phục (`scripts/backup.sh`, `restore.sh`). Lưu trữ có **test tự động** `scripts/test-persistence.sh` (lưu → `down`/`up` → đọc lại; tắt đột ngột bằng `kill` → đọc lại), được `scripts/test.sh` gọi | PASS, có ghi chú ² |
| **VI. Giao diện tiếng Việt** | Chuỗi tiếng Việt tập trung trong `frontend/src/i18n/vi.ts`; `Intl` vi-VN; FullCalendar locale `vi`, tuần bắt đầu Thứ Hai, 24h; lỗi API trả `message` tiếng Việt | PASS |
| **Ràng buộc bổ sung (YAGNI, ít phụ thuộc, README)** | Docker + PostgreSQL + agent riêng nặng hơn mức tối thiểu cho app một người: xem Complexity Tracking | PASS khi có lý do |
| **Quy trình (lint + test trước khi merge)** | Lệnh lint/test liệt kê trong quickstart; thêm hook `pre-commit` tuỳ chọn | PASS |

¹ Internet chỉ cần **lúc cài đặt/build** (tải image Docker, gói và model). Đây là bước thiết lập
một lần, không phải lúc ứng dụng chạy. Constitution yêu cầu "mọi chức năng PHẢI hoạt động khi không
có internet", và điều đó được kiểm chứng bằng V15.

² Nguyên tắc V lấy "SQLite/JSON" làm *ví dụ* cho cơ sở dữ liệu nhúng. PostgreSQL trong volume cục
bộ vẫn là lưu trữ cục bộ, với vị trí cố định được ghi trong README.

**Kết quả gate trước Phase 0**: PASS. Không có vi phạm nào chưa có lý do.

**Re-check sau Phase 1**: PASS.
- `contracts/calendar-sync.md` giới hạn đúng các trường tối thiểu và phạm vi lịch riêng (IV).
- `data-model.md` dùng transaction và `bump_revision` trong service, không dùng trigger ẩn (I, V).
- Quickstart có kịch bản kiểm chứng offline (V15) và chỉ-localhost (V16).
- Sau `/speckit-analyze` (2026-11-04): bổ sung script chạy toàn bộ test bằng một lệnh và test tự động
  cho lưu trữ (trước đây thiếu, vi phạm Nguyên tắc II và V); tasks.md đã có task tương ứng.
- Không phát sinh vi phạm mới.

## Project Structure

### Documentation (this feature)

```text
specs/001-task-class-scheduler/
├── plan.md              # File này
├── research.md          # Phase 0: quyết định kỹ thuật + 2 spike
├── data-model.md        # Phase 1: bảng, ràng buộc, trạng thái
├── quickstart.md        # Phase 1: chạy, test, kịch bản kiểm chứng V1–V17
├── contracts/
│   ├── rest-api.md      # API cho frontend
│   └── calendar-sync.md # API + hành vi cho mac-agent
└── tasks.md             # Phase 2 (/speckit-tasks, chưa tạo)
```

### Source Code (repository root)

```text
docker-compose.yml            # db, backend, web; chỉ web mở 127.0.0.1:8080
docker-compose.dev.yml        # tuỳ chọn: Vite dev server + mount code
README.md                     # chạy 1 lệnh, vị trí dữ liệu, sao lưu, cài agent
Makefile                      # make test → scripts/test.sh
scripts/
├── test.sh                   # toàn bộ lint + test bằng một lệnh (constitution II)
├── test-persistence.sh       # test lưu trữ qua khởi động lại / tắt đột ngột (constitution V)
├── backup.sh
└── restore.sh

backend/
├── Dockerfile                # PyTorch CPU + EasyOCR; tải model lúc build
├── pyproject.toml            # ruff, pytest config (markers: ocr)
├── migrations/               # Flask-Migrate (Alembic)
├── app/
│   ├── __init__.py           # create_app()
│   ├── config.py
│   ├── models/               # semester, shift, subject, class_session, task, task_list, tag, exam,
│   │                         #   settings, sync
│   ├── api/                  # blueprints: today, calendar, tasks, lists, semesters, shifts,
│   │                         #   subjects, sessions, tags, exams, imports, settings, reminders, sync
│   ├── schemas/              # pydantic request/response
│   ├── services/
│   │   ├── recurrence.py     # sinh buổi học (hàm thuần)
│   │   ├── shifts.py         # khớp ca, áp giờ ca
│   │   ├── duplicates.py     # phát hiện trùng
│   │   ├── auto_deadlines.py # quy tắc + reconcile
│   │   ├── exams.py          # buổi thi: CRUD, trùng giờ, nhãn "Thi" (US11)
│   │   ├── reminders.py      # tính mốc nhắc (thường / quan trọng / buổi thi)
│   │   ├── digest.py         # bản tóm tắt hằng ngày (hàm thuần)
│   │   ├── sync_feed.py      # feed + revision + long-poll
│   │   └── colors.py         # display_color, bảng màu
│   ├── ocr/
│   │   ├── reader.py         # EasyOCR singleton, offline
│   │   ├── preprocess.py     # HEIC, resize, tương phản
│   │   ├── layout.py         # lọc vùng, nhận biết loại ảnh (lưới tuần / bảng thi), gom ô
│   │   ├── exam_table.py     # phân tích bảng lịch thi, loại cột thông tin sinh viên (R14)
│   │   ├── fields.py         # regex trích trường
│   │   ├── month_year.py     # xác định tháng/năm + nguồn
│   │   └── preview.py        # ráp ImportPreview
│   └── cli.py                # flask seed-demo
└── tests/
    ├── unit/                 # recurrence, shifts, duplicates, auto_deadlines, reminders, layout, fields, month_year
    ├── integration/          # API + PostgreSQL thật
    ├── ocr/                  # @pytest.mark.ocr, chạy EasyOCR trên ảnh mẫu
    └── fixtures/timetables/  # *.png + *.expected.json (ảnh thật đã che thông tin + ảnh tổng hợp)

frontend/
├── Dockerfile                # build Vite → nginx
├── nginx.conf                # phục vụ static + proxy /api → backend:8000
├── package.json
├── src/
│   ├── main.tsx, App.tsx, routes.tsx
│   ├── api/                  # client fetch + hooks TanStack Query
│   ├── i18n/vi.ts            # toàn bộ chuỗi tiếng Việt
│   ├── lib/                  # dates (định dạng vi), colors (bảng màu)
│   ├── reminders/            # nhắc dự phòng: scheduler + Web Locks (cả bản tóm tắt)
│   ├── components/           # TaskForm, SubjectForm, ShiftPicker, TagPicker, TagFilter, ConfirmDialog...
│   └── pages/                # Today, Calendar, Tasks, Subjects, Exams, Import, Semesters, Shifts, Tags,
│                             #   Lists, Settings
└── tests/                    # Vitest: reminders, dates, tag filter

mac-agent/
├── pyproject.toml
├── setup.py                  # py2app, Info.plist (NS*FullAccessUsageDescription, LSUIElement)
├── lichhoc_agent/
│   ├── main.py               # vòng long-poll
│   ├── backend_client.py     # gọi /api/sync/*
│   ├── reconcile.py          # đối chiếu thuần: feed + hiện trạng → kế hoạch thêm/sửa/xoá
│   ├── calendar_store.py     # interface CalendarStore + EventKitStore (PyObjC)
│   └── state.py              # state.json
├── launchd/vn.lichhoc.agent.plist
├── scripts/install.sh        # build .app, ký ad-hoc, cài/khởi động LaunchAgent; --uninstall
└── tests/                    # reconcile với FakeCalendarStore
```

**Structure Decision**: Mẫu "Web application" (`backend/` + `frontend/`) cộng thêm `mac-agent/` cho
tiến trình nền macOS. Spec bắt buộc đồng bộ Lịch/Lời nhắc, mà container Docker không truy cập được
EventKit. Ba thư mục tương ứng ba đơn vị triển khai độc lập: image backend, image web, và
LichHocAgent.app.

## Thứ tự triển khai đề xuất (đầu vào cho /speckit-tasks)

1. **Spike** (song song):
   - S1: EasyOCR trên ảnh thật (R2).
   - S2: PyObjC EventKit `.app` tạo sự kiện iCloud (R4).
   Kết quả có thể đổi phương án dự phòng.
2. **Nền tảng**: Docker Compose, migrations, settings/seed, khung API, khung frontend + i18n.
3. **P1**: US1 Task, US2 Học kỳ + môn + sinh buổi (gồm ca ở mức chọn ca, US8 phần cơ bản), US3 Hôm
   nay.
4. **P2**:
   - US4 ngoại lệ buổi học.
   - US5 lịch ngày/tuần/tháng.
   - US9 nhãn + lọc.
   - US8 đổi/xoá ca.
   - US6 nhập ảnh lịch học (sau S1) cùng nhóm với US11 lịch thi (quản lý, nhập ảnh bảng lịch thi,
     hiển thị trên lịch và trang Hôm nay). Migration `0003_exams` thêm bảng mới (sau
     `0002_important_digest` của phần mở rộng US7).
5. **P3**:
   - US10 deadline tự tạo.
   - US7: nhắc dự phòng, rồi mac-agent đồng bộ (sau S2); gồm cả buổi thi với nhiều mốc báo trước.
   - US7 mở rộng (bổ sung sau khi US7 đã xong): mức "Quan trọng" với nhiều mốc nhắc và bản tóm tắt
     hằng ngày (research R15, R16). Migration `0002_important_digest`; feed đổi `alarm_at` →
     `alarms_at` và thêm `digests`, nên backend và agent (0.2.0) phát hành cùng lúc.
6. **Hoàn thiện**: README, backup/restore, kịch bản V1–V20, đo hiệu năng.

## Complexity Tracking

| Vi phạm / độ phức tạp | Vì sao cần | Phương án đơn giản hơn bị loại vì |
|-----------------------|------------|-----------------------------------|
| Docker Compose + 3 service cho app một người dùng | Người dùng chọn rõ kiến trúc này; dễ chạy bằng một lệnh và cô lập môi trường Python/PyTorch nặng của EasyOCR | Chạy trực tiếp trên macOS phải tự cài PyTorch, PostgreSQL, Node; khó tái lập |
| PostgreSQL thay vì SQLite | Người dùng chọn; hỗ trợ tốt ràng buộc `EXCLUDE` (học kỳ không chồng lấn), mảng, `timestamptz`; `pg_dump` sao lưu nóng | SQLite đủ về khối lượng nhưng không phải lựa chọn của người dùng; ràng buộc chồng lấn phải viết tay |
| Thành phần thứ tư `mac-agent` ngoài Docker | FR-051 đến FR-054 cần EventKit, chỉ truy cập được từ tiến trình macOS gốc có Info.plist | Thông báo trình duyệt không nhắc được khi đóng tab hay trên iPhone; file `.ics` không tự cập nhật |
| PyTorch (~1.5 GB) trong image backend | EasyOCR, mà người dùng chọn, chạy trên PyTorch; cần cho nhận diện tiếng Việt offline | Tesseract nhẹ hơn nhưng kém với chữ giao diện web; Apple Vision là dự phòng nếu spike thất bại |
| FullCalendar, TanStack Query | Ba chế độ xem lịch đầy đủ và cache dữ liệu là công sức lớn nếu tự viết | Tự viết lịch tốn nhiều công và dễ lỗi |
