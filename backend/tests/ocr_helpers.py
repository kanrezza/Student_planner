"""Tiện ích dựng `TextBox` và ảnh giả cho test OCR."""

import io
import json
from datetime import date, datetime, time
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from app.lib.timeutil import TZ
from app.ocr.preview import PreviewContext
from app.ocr.reader import TextBox

FIXTURES = Path(__file__).parent / "fixtures" / "timetables"
H = 20  # chiều cao dòng mặc định


def box(text: str, x: float, y: float, w: float | None = None, h: float = H, conf: float = 0.95):
    return TextBox(text, x, y, x + (w if w is not None else 9 * len(text)), y + h, conf)


def load_boxes(name: str) -> tuple[list[TextBox], tuple[int, int]]:
    """Khối chữ đã dump từ OCR thật (đã che thông tin sinh viên)."""
    data = json.loads((FIXTURES / f"{name}.boxes.json").read_text(encoding="utf-8"))
    boxes = [TextBox(t, x0, y0, x1, y1, c) for t, x0, y0, x1, y1, c in data["boxes"]]
    return boxes, tuple(data["size"])


def png_bytes(size: tuple[int, int] = (2000, 1000)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, "white").save(out, "PNG")
    return out.getvalue()


def shifts():
    spans = [((6, 45), (9, 25)), ((9, 35), (12, 10)), ((13, 0), (15, 40)), ((15, 45), (18, 25))]
    return [
        SimpleNamespace(id=i + 1, position=i + 1, start_time=time(*a), end_time=time(*b))
        for i, (a, b) in enumerate(spans)
    ]


def context(**overrides) -> PreviewContext:
    values = {
        "now": datetime(2026, 11, 5, 9, 0, tzinfo=TZ),
        "shifts": shifts(),
        "semesters": [
            SimpleNamespace(id=7, start_date=date(2026, 8, 17), end_date=date(2026, 12, 20))
        ],
    }
    values.update(overrides)
    return PreviewContext(**values)
