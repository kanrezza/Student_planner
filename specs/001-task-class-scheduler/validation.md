# Kết quả kiểm chứng (feature 001 — T145)

Ngày chạy: 2026-11-05, máy phát triển (macOS 26, OrbStack). `./scripts/test.sh` pass toàn bộ;
`./scripts/validate.sh` chạy các kịch bản tự động được trên database tạm với OCR thật: **20/20 đạt**.

| Kịch bản | Cách kiểm | Kết quả | Ghi chú |
|----------|-----------|---------|---------|
| V1 Task cơ bản | validate.sh | ✅ | tạo, sửa, hoàn thành, hiện ở Hôm nay |
| V2 Không mất dữ liệu | `test-persistence.sh` (trong test.sh) | ✅ | khởi động lại Mac: chưa thử |
| V3 Học kỳ + 6 môn | validate.sh | ✅ | mỗi môn đúng 15 buổi |
| V4 Ngoại lệ buổi học | validate.sh | ✅ | |
| V5 Đổi giờ ca | validate.sh | ✅ | |
| V6 Lịch & nhãn | validate.sh | ✅ | lọc nhãn 6 ms (SC-016) |
| V7 Nhập ảnh | validate.sh + `pytest -m ocr` | ✅ | ảnh thật 4/4; tổng lịch học 22/26 = 85% (SC-011) |
| V8 Không trùng | validate.sh | ✅ | nhập lại: 0 môn mới (SC-012) |
| V9, V10 Deadline tự tạo | validate.sh | ✅ | |
| V11–V14 Đồng bộ Mac/iPhone | — | ⏳ cần thử tay | V11, V13, V14 trên Mac; V12 cần iPhone; T159 vẫn chờ |
| V15 Offline | rà mã + dist | ◐ | dist và backend không gọi URL ngoài; chưa thử tắt Wi-Fi thật |
| V16 Chỉ localhost | `docker compose port`, `lsof`, curl tới IP LAN | ✅ | cổng chỉ ở 127.0.0.1; IP LAN không kết nối được |
| V17 Hiệu năng | `flask seed-demo` + đo API | ✅ | Hôm nay 29 ms, lịch tuần 13 ms, lịch tháng 64 ms, danh sách task 71 ms |
| V18 Lịch thi | validate.sh + `pytest -m ocr` | ✅ | ảnh thật 5/5; tổng 14/17 = 82% (SC-019); không lộ họ tên/MSSV (SC-020) |
| V19 Tóm tắt hằng ngày | validate.sh (xem trước) + test | ◐ | phần iPhone/Mac gập cần thử tay |
| V20, V21 Quan trọng, nhắc tối | pytest (test_reminders, test_auto_deadlines…) | ✅ | phần hiển thị trên iPhone cần thử tay |

**Chưa làm được (cần người thử):** V11–V14 trên Mac thật, V12/V19/V20 với iPhone khi Mac gập, V15 tắt Wi-Fi,
khởi động lại Mac cho V2.
