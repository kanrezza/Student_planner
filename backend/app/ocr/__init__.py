"""Nhận diện ảnh thời khoá biểu và lịch thi hoàn toàn offline (research R2, R3, R14).

Chuỗi xử lý (mỗi bước là hàm thuần, test riêng được bằng `TextBox` dựng tay):
`preprocess.load_image` → `reader.read_boxes` → `layout` (bố cục, ô) → `fields` / `exam_table` →
`month_year` → `preview.build_preview`. Ảnh chỉ nằm trong bộ nhớ (FR-035).
"""
