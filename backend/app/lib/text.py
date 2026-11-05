"""Chuẩn hoá chuỗi tiếng Việt: cùng một chữ có thể ở dạng dựng sẵn (NFC) hoặc tổ hợp (NFD)."""

import unicodedata


def nfc(s: str) -> str:
    """Chuẩn hoá NFC và bỏ khoảng trắng hai đầu."""
    return unicodedata.normalize("NFC", s).strip()


def ci_key(s: str) -> str:
    """Khoá so sánh không phân biệt hoa thường: NFC + casefold."""
    return nfc(s).casefold()


def fold_key(s: str) -> str:
    """Khoá so sánh không phân biệt dấu và hoa thường: "Gấp" và "gap" cùng khoá (đ → d)."""
    decomposed = unicodedata.normalize("NFD", nfc(s))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.replace("đ", "d").replace("Đ", "D").casefold()


def contains_ci(haystack: str, needle: str) -> bool:
    return ci_key(needle) in ci_key(haystack)
