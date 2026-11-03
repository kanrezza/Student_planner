"""Bảng 12 màu cố định (mã c01…c12).

Ánh xạ sang mã hex nằm ở frontend (frontend/src/lib/colors.ts).
"""

from collections import Counter

PALETTE = [f"c{i:02d}" for i in range(1, 13)]


def next_color(used: list[str]) -> str:
    """Chọn màu đang được dùng ít nhất; hoà nhau thì lấy màu đứng trước trong bảng."""
    counts = Counter(c for c in used if c in PALETTE)
    return min(PALETTE, key=lambda c: (counts[c], PALETTE.index(c)))


def display_color(tag_colors: list[str], fallback: str) -> str:
    """Màu hiển thị: màu của nhãn gắn đầu tiên, nếu không có nhãn thì màu môn/danh sách (FR-044)."""
    return tag_colors[0] if tag_colors else fallback


def is_palette_color(code: str) -> bool:
    return code in PALETTE
