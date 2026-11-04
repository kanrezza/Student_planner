"""Đọc và chuẩn bị ảnh cho OCR (FR-028, FR-029). Chỉ xử lý trong bộ nhớ."""

import io

import pillow_heif
from PIL import Image, UnidentifiedImageError

from app.api.errors import ApiError

pillow_heif.register_heif_opener()

ALLOWED_FORMATS = {"PNG", "JPEG", "HEIF"}

# Kết quả spike ảnh thật (specs/001…/research R2): phóng ảnh lên cạnh dài ~3600 px (tối đa ×1.5)
# cho độ chính xác đúng nguyên văn 8/8 dòng; để nguyên cỡ chỉ đạt 5/8. Ảnh quá lớn thì thu nhỏ để
# kịp thời gian (≤ 60 giây/ảnh).
TARGET_LONG_SIDE = 3600
MAX_UPSCALE = 1.5
MAX_LONG_SIDE = 4000


def load_image(data: bytes) -> Image.Image:
    """Mở PNG/JPEG/HEIC và đổi sang RGB; định dạng khác → 415."""
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError):
        raise unsupported() from None
    if image.format not in ALLOWED_FORMATS:
        raise unsupported()
    return image.convert("RGB")


def unsupported() -> ApiError:
    return ApiError(415, "unsupported_image", "Chỉ nhận ảnh PNG, JPEG hoặc HEIC")


def working_scale(size: tuple[int, int]) -> float:
    """Hệ số phóng/thu của ảnh trước khi OCR (xem hằng số ở đầu file)."""
    long_side = max(size)
    if long_side > MAX_LONG_SIDE:
        return MAX_LONG_SIDE / long_side
    return max(1.0, min(MAX_UPSCALE, TARGET_LONG_SIDE / long_side))


def prepare(image: Image.Image) -> tuple[Image.Image, float]:
    """Ảnh đã đổi cỡ để đưa vào OCR và hệ số đã dùng."""
    scale = working_scale(image.size)
    if abs(scale - 1.0) < 0.01:
        return image, 1.0
    size = (round(image.width * scale), round(image.height * scale))
    return image.resize(size, Image.LANCZOS), scale
