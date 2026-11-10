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


def fold_with_map(s: str) -> tuple[str, list[int]]:
    """Như `fold_key` nhưng kèm vị trí trong chuỗi gốc của từng ký tự đã gập (để cắt đoạn trích)."""
    folded: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(unicodedata.normalize("NFC", s)):
        piece = unicodedata.normalize("NFD", char)
        piece = "".join(ch for ch in piece if not unicodedata.combining(ch))
        piece = piece.replace("đ", "d").replace("Đ", "D").casefold()
        folded.append(piece)
        positions.extend([index] * len(piece))
    return "".join(folded), positions
