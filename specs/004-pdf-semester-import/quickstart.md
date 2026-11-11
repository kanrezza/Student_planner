# Quickstart: kiểm chứng feature 004 — nhập học kỳ từ PDF

Chạy và kiểm tra feature từ đầu đến cuối. Đáp án chi tiết ở
[contracts/timetable-pdf-format.md](contracts/timetable-pdf-format.md); hình dạng dữ liệu ở
[data-model.md](data-model.md); API ở [contracts/rest-api.md](contracts/rest-api.md).

## Chuẩn bị

```sh
cd "/Volumes/BIWIN/MySelf/Lịch Học Cá Nhân"
docker compose build backend && docker compose up -d   # image có pdfplumber, migration 0010/0011 tự chạy
./scripts/test.sh                                        # toàn bộ test (kèm --ocr nếu muốn chạy OCR thật)
```

File thật để thử tay: `samples/tkb-hk2-2026.pdf` (bị `.gitignore` chặn, không có trong repo). File giả lập cho test:
`backend/tests/fixtures/timetables/tkb-synthetic-01.pdf` (sinh lại bằng `samples/synthetic/make_timetable_pdf.py`).

## Kịch bản tự động (chạy trong `./scripts/test.sh`)

| # | Kịch bản | Kết quả mong đợi |
|---|----------|------------------|
| A1 | Đọc `tkb-synthetic-01.pdf` | 8 môn, 17 quy tắc khớp đáp án; tên/mã SV/lớp giả không có trong kết quả (SC-001, SC-006) |
| A2 | Đọc bản 2 trang, bảng tràn trang | đủ mọi hàng |
| A3 | File không có chữ / có mật khẩu / không phải thời khoá biểu / không phải PDF / > 20 MB | đúng mã lỗi ở contract REST |
| A4 | Luật ghép ô | bảng ví dụ ở contract định dạng PDF đều đúng |
| A5 | Bảng tiết mặc định, đổi giờ Ca 2, sửa tay tiết 5 rồi đổi Ca 2 lần nữa | tiết 4–6 theo ca mới, tiết 5 giữ giờ tay |
| A6 | `periods_to_time` với 1–3, 4–6, 1–6, 1–2, 16–18, 13–15 | Ca 1; Ca 2; Ca 1–2; 06:45–08:30 tuỳ chỉnh; 21:05–22:00; lỗi thiếu giờ |
| A7 | Lưu bản xem trước trên DB trống | số buổi = số ngày đúng thứ trong các khoảng; không buổi nào 25/01–14/02/2027 (SC-004) |
| A8 | Nhập lại cùng file | mọi môn `unchanged`, lưu tạo 0 môn, 0 buổi (SC-005) |
| A9 | Nhập lại file đổi phòng một quy tắc, có buổi đã qua và buổi đã sửa riêng | buổi tương lai đổi phòng; buổi đã qua và buổi sửa riêng giữ nguyên |
| A10 | Có sẵn môn tạo từ ảnh cùng tên + mã lớp | khớp `changed`, không tạo môn thứ hai |
| A11 | Học kỳ: chứa trọn / không có / chồng một phần / chồng hai học kỳ | `use` / `create` / `extend` / `conflict` |
| A12 | Migration 0010 trên dữ liệu cũ (môn 2 thứ + buổi đã huỷ, đã dời) | mỗi môn 1 quy tắc, buổi giữ nguyên ngoại lệ, gắn `schedule_id` |
| A13 | Nhập ảnh `real-week-02` sau khi có tên chuẩn | 7/7 tên môn khớp tên chuẩn, lý do "Đã sửa theo thời khoá biểu" (SC-007) |
| A14 | Form môn: thêm/sửa/xoá quy tắc qua API và giao diện (Vitest) | buổi sinh đúng, không xoá được quy tắc cuối cùng |
| A15 | Thời gian đọc PDF | < 3 giây cho file 1–3 trang (SC-002) |

## Kiểm tra tay trên app

1. Mở trang Môn học → **Nhập lịch**, kéo `samples/tkb-hk2-2026.pdf` vào (hoặc bấm "chọn file") → bản xem trước hiện 8 môn, 17 lịch, học kỳ đề xuất "HK2 2026–2027".
2. Mở Finder, chọn file PDF, ⌘C; quay lại trang Môn học, ⌘V → cũng mở màn "Nhập lịch". Nếu WKWebView không cho
   dán file, ghi lại trong `validation.md` (kéo thả và chọn file vẫn phải chạy).
3. Bấm Lưu → lịch tuần 30/11–06/12/2026 hiện đúng các buổi; tuần 01/02/2027 trống; môn "Tích hợp… (COUR01)" có nhãn
   E-Learning và deadline tự tạo.
4. Mở form sửa một môn có nhiều lịch → thấy đủ quy tắc; đổi phòng một quy tắc → buổi tương lai đổi theo.
5. Cài đặt → Ca học → Bảng tiết: thấy tiết 1–12 và 16–18; sửa tiết 2 thành 07:40–08:25 → "Tiết 1–2" của môn Trực quan
   hoá dữ liệu khi nhập lại có giờ mới.
6. Kiểm tra không có họ tên, mã sinh viên trong giao diện, log backend (`docker compose logs backend`) và CSDL.
