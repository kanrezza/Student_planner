"""Đọc chữ bằng EasyOCR (tiếng Việt + Anh), chạy offline: model đã có sẵn trong image Docker."""

import threading
from dataclasses import dataclass

import numpy as np
from PIL import Image

from app.config import EASYOCR_MODEL_DIR
from app.lib.text import nfc
from app.ocr.preprocess import prepare


@dataclass(frozen=True)
class TextBox:
    """Một khối chữ: nội dung, khung bao (px của ảnh gốc) và độ tin cậy 0–1."""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    conf: float = 1.0

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0


_reader = None
_lock = threading.Lock()  # chỉ một yêu cầu OCR chạy cùng lúc (research R2)


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr  # nạp chậm: import PyTorch mất vài giây

        _reader = easyocr.Reader(
            ["vi", "en"],
            gpu=False,
            model_storage_directory=EASYOCR_MODEL_DIR,
            download_enabled=False,  # không bao giờ gọi mạng (FR-025, FR-029)
            verbose=False,
        )
    return _reader


def read_boxes(image: Image.Image) -> list[TextBox]:
    """Nhận diện chữ; toạ độ trả về theo ảnh gốc (đã quy đổi lại hệ số phóng)."""
    prepared, scale = prepare(image)
    with _lock:
        results = _get_reader().readtext(np.array(prepared), paragraph=False)
    boxes = []
    for quad, text, conf in results:
        text = nfc(text)
        if not text:
            continue
        xs = [p[0] / scale for p in quad]
        ys = [p[1] / scale for p in quad]
        boxes.append(TextBox(text, min(xs), min(ys), max(xs), max(ys), float(conf)))
    return boxes
