"""SPIKE đầu–cuối cho ảnh tuần thật 30/11–06/12/2026 (vắt qua hai tháng, ô "Lịch thi", ô bị cắt).

Khác `real_spike.py` (chỉ chấm OCR thô theo vùng), script này chạy cả đường ống như ứng dụng
(OCR → bố cục → `build_preview`) rồi so với đáp án viết tay trong
`tests/unit/test_real_week_cross_month.py`, báo độ chính xác theo từng loại trường.
Ảnh thật nằm ngoài git (`samples/`).

  docker run --rm --network none -v "$PWD/samples:/samples:ro" -v "$PWD/backend:/app" \
      -e PYTHONPATH=/app --entrypoint python lichhoc-backend:latest \
      /app/spikes/week_e2e_spike.py /samples/lich-tuan-30-11.jpg.jpg
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from rapidfuzz import fuzz

from app.lib.text import ci_key
from app.lib.timeutil import TZ
from app.ocr import preprocess, reader
from app.ocr.preview import build_preview
from tests.ocr_helpers import context
from tests.unit.test_real_week_cross_month import SESSIONS

EXAM = {"date": "2026-11-30", "start": "18:30", "end": "20:00", "room": "A6-101.102 (PC)"}


def similar(got, want) -> float:
    return fuzz.ratio(ci_key(str(got or "")), ci_key(want))


def main(path: str) -> None:
    image = preprocess.load_image(Path(path).read_bytes())
    boxes = reader.read_boxes(image)
    preview = build_preview(
        boxes, image.size, context(now=datetime(2026, 11, 10, 20, 30, tzinfo=TZ), subject_names=[])
    )
    rows = {(r["fields"]["date"]["value"], r["fields"]["start_time"]["value"]): r for r in preview["rows"]}
    exact: dict[str, list[bool]] = defaultdict(list)
    fuzzy: dict[str, list[float]] = defaultdict(list)
    for day, start, end, name, room, lecturer, code in SESSIONS:
        row = rows.get((day, start))
        exact["buổi đọc được (ngày+giờ bắt đầu)"].append(row is not None)
        if row is None:
            continue
        f = row["fields"]
        exact["giờ kết thúc"].append(f["end_time"]["value"] == end)
        if code:
            exact["nhóm lớp"].append(f["class_code"]["value"] == code)
        fuzzy["tên môn"].append(similar(f["name"]["value"], name))
        if room:
            fuzzy["phòng"].append(similar(f["room"]["value"], room))
        if lecturer:
            fuzzy["giảng viên"].append(similar(f["lecturer"]["value"], lecturer))
    exams = preview["exam_rows"]
    exact["ô Lịch thi → buổi thi"].append(len(exams) == 1 and len(preview["rows"]) == len(SESSIONS))
    if exams:
        f = exams[0]["fields"]
        got = (f["date"]["value"], f["start_time"]["value"], f["end_time"]["value"], f["room"]["value"])
        exact["buổi thi: ngày/giờ/phòng"].append(got == tuple(EXAM.values()))
    exact["tháng/năm"].append(preview["month_year"]["value"] == "2026-12")
    cut = rows.get(("2026-12-01", "21:05"))
    exact["ô cắt: đánh dấu chưa chắc chắn"].append(
        bool(cut) and cut["truncated"] and not cut["fields"]["name"]["certain"]
    )
    print(f"{len(boxes)} khối chữ; {len(preview['rows'])} buổi học, {len(exams)} buổi thi")
    for key, values in exact.items():
        print(f"  {key}: {sum(values)}/{len(values)} đúng hoàn toàn")
    for key, values in fuzzy.items():
        ok = sum(v >= 85 for v in values)
        print(f"  {key}: TB giống {sum(values) / len(values):.0f}%, ≥85%: {ok}/{len(values)}")


if __name__ == "__main__":
    main(sys.argv[1])
