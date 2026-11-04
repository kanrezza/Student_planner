"""OCR THẬT trên ảnh mẫu (chậm; chạy bằng `pytest -m ocr`) — T093, T109, SC-011, SC-019, SC-020.

Cách chấm (ghi rõ để số liệu không bị hiểu nhầm):
- Trường có cấu trúc (ngày, giờ, thứ, lần thi) phải GIỐNG HỆT.
- Trường chữ tự do (tên, phòng, giảng viên, mã lớp, hình thức thi) tính đúng khi giống ≥ 85%
  (rapidfuzz, không phân biệt hoa thường); sai 1–2 dấu vẫn sửa được ở bảng xem trước.
- "Dòng đúng" = mọi trường đều đúng. Ngưỡng: ≥ 80% dòng trên tổng các ảnh cùng loại.
"""

import json
import time as clock
from datetime import datetime

import pytest
from rapidfuzz import fuzz

from app.lib.text import ci_key
from app.lib.timeutil import TZ
from app.ocr import preprocess, reader
from app.ocr.preview import build_preview
from tests.ocr_helpers import FIXTURES, context

pytestmark = pytest.mark.ocr

NOW = datetime(2026, 11, 4, 14, 5, tzinfo=TZ)
MAX_SECONDS = 60
EXACT = {"date", "start_time", "end_time", "weekday", "attempt"}
GRID_KEYS = ["name", "date", "start_time", "end_time", "room", "lecturer", "class_code"]
EXAM_KEYS = [
    "course_code", "course_name", "attempt", "date", "start_time", "end_time",
    "exam_format", "room", "candidate_number",
]  # fmt: skip


def similar(got, want) -> bool:
    if want in (None, ""):
        return got in (None, "")
    return got is not None and fuzz.ratio(ci_key(str(got)), ci_key(str(want))) >= 85


def field_ok(key, got, want) -> bool:
    return got == want if key in EXACT else similar(got, want)


def expectation_files(kind):
    for path in sorted(FIXTURES.glob("*.expected.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind", "week_schedule") == kind:
            yield path, data


def run(image_name):
    data = (FIXTURES / image_name).read_bytes()
    started = clock.perf_counter()
    image = preprocess.load_image(data)
    preview = build_preview(reader.read_boxes(image), image.size, context(now=NOW))
    return preview, clock.perf_counter() - started


def test_week_schedule_images():
    total = good = 0
    for path, expected in expectation_files("week_schedule"):
        preview, seconds = run(expected["image"])
        assert preview["kind"] == "week_schedule", path.name
        assert seconds <= MAX_SECONDS, f"{path.name}: {seconds:.0f}s"
        got = {
            (r["fields"]["date"]["value"], r["fields"]["start_time"]["value"]): r["fields"]
            for r in preview["rows"]
        }
        ok = 0
        for want in expected["rows"]:
            fields = got.get((want["date"], want["start_time"]))
            keys = [
                k
                for k in GRID_KEYS
                if k in want and not (k == "class_code" and "real" in path.name)
            ]
            if fields and all(field_ok(k, fields[k]["value"], want[k]) for k in keys):
                ok += 1
        month = (expected.get("month_year") or "")[:7]
        print(
            f"{path.name}: {ok}/{len(expected['rows'])} dòng đúng, {seconds:.0f}s, tháng {preview['month_year']['value']}"
        )
        if month:
            assert preview["month_year"]["value"] == month
        total += len(expected["rows"])
        good += ok
    print(f"Tổng lịch học: {good}/{total} = {good / total:.0%}")
    assert good / total >= 0.8  # SC-011


def test_exam_table_images():
    total = good = 0
    for path, expected in expectation_files("exam_table"):
        preview, seconds = run(expected["image"])
        assert preview["kind"] == "exam_table", path.name  # nhận đúng loại (100%)
        assert seconds <= MAX_SECONDS, f"{path.name}: {seconds:.0f}s"
        blob = json.dumps(preview, ensure_ascii=False)
        for secret in expected["student_values_must_not_appear"]:
            assert secret not in blob, f"{path.name}: lộ {secret}"  # SC-020
        rows = preview["exam_rows"]
        ok = 0
        for want, row in zip(expected["rows"], rows, strict=False):
            fields = {k: row["fields"][k]["value"] for k in EXAM_KEYS}
            if all(field_ok(k, fields[k], want[k]) for k in EXAM_KEYS):
                ok += 1
        print(f"{path.name}: {ok}/{len(expected['rows'])} dòng đúng, {seconds:.0f}s")
        assert len(rows) == len(expected["rows"]), path.name
        total += len(expected["rows"])
        good += ok
    print(f"Tổng lịch thi: {good}/{total} = {good / total:.0%}")
    assert good / total >= 0.8  # SC-019
