"""Trích trường của một ô buổi học bằng regex và từ khoá (research R3 bước 5).

Hai kiểu ô được hỗ trợ:
- Cổng thông tin thật: dòng giờ "06:45 - 09:25 (Tiết 1-3)", rồi dòng "Tên môn-1-1-26(N01)" (có thể
  xuống dòng), dòng phòng (có thể dính tiền tố "Có mặt"), dòng giảng viên.
- Dạng có nhãn: tên môn trên dòng giờ, rồi "Phòng: A2-301", "GV: ThS. Nguyễn Văn An", mã lớp riêng.
"""

import re
from datetime import time

from app.lib.text import nfc
from app.ocr.geometry import find_times
from app.ocr.reader import TextBox

E_LEARNING_RE = re.compile(r"e[\s-]?learning|\bonline\b", re.IGNORECASE)
_TIET_RE = re.compile(r"t[il1]\S{0,2}t\s*(\d{1,2})\s*[-–—]\s*(\d{1,2})", re.IGNORECASE)
# Hậu tố nhóm lớp của cổng thông tin: "-1-1-26(N01)", "-1-1-26(COUR01.LT2)", "-1-1-26(N01).TH".
_SUFFIX_START_RE = re.compile(r"-\s*\d\s*-\s*\d\s*-")
_CLASS_SUFFIX_RE = re.compile(r"\s*-\s*(\d)\s*-\s*(\d)\s*-\s*(\d{2})\s*\((.*?)\)\s*(\.\w+)?\s*$")
_CODE_LINE_RE = re.compile(r"^[A-Z]{2,5}\d{3,}[\w\-.]*(\(\w+\))?$")
_ROOM_PREFIX_RE = re.compile(
    r"^(?:có\s*mặt|vắng(?:\s*mặt)?|nghỉ|phòng|p\.)\s*[:.]?\s*", re.IGNORECASE
)
_ROOM_LABEL_RE = re.compile(r"^(?:phòng|p\.)\s*:", re.IGNORECASE)
_TIET_OPEN_RE = re.compile(r"\(\s*t[il1]\S{0,2}t\s*$", re.IGNORECASE)
_TIET_TAIL_RE = re.compile(r"^\d{1,2}\s*[-–—]\s*\d{1,2}\s*\)?$")
_ROOM_RE = re.compile(
    r"^(?:[A-Za-z]{1,2}\d{1,2}\s*[-.]\s*\d{2,3}(?:\.\d{1,3})?|[A-Za-z]\d{3,4})(?:\s*\(\w{1,4}\))?"
)
_SHIFT_RE = re.compile(r"\bca\s*(\d)\b", re.IGNORECASE)
_LECTURER_LABEL_RE = re.compile(r"^(?:gv|giảng viên)\s*[:.]\s*", re.IGNORECASE)
_WORD = r"[A-ZÀ-Ỵ][a-zà-ỹ]+"
_NAME_TAIL_RE = re.compile(rf"^{_WORD}(?:\s+{_WORD})?$")
_LECTURER_RE = re.compile(
    rf"^(?:(?:ThS|TS|PGS|GS|CN|KS|PGS\.TS)\.?\s+)*{_WORD}(?:\s+{_WORD}){{1,4}}$"
)


def fix_digit_letters(token: str) -> str:
    """Sửa lỗi OCR nhầm O↔0 ngay cạnh chữ số: "NO1" → "N01", "COURO1" → "COUR01"."""
    chars = list(token)
    for i, ch in enumerate(chars):
        if ch in "Oo":
            before = chars[i - 1] if i else ""
            after = chars[i + 1] if i + 1 < len(chars) else ""
            if after.isdigit() or (before.isdigit() and not after.isalpha()):
                chars[i] = "0"
    return "".join(chars)


_CODE_TOKEN_RE = re.compile(r"^([A-Z]{2,5}?)([0-9OIl]{3,5})$")


def fix_code_token(token: str) -> str:
    """Sửa lỗi OCR trong mã học phần/lớp: "MATI101" → "MAT1101", "ENG10O1" → "ENG1001"."""
    match = _CODE_TOKEN_RE.match(token)
    if not match:
        return token
    digits = match.group(2).translate(str.maketrans("OIl", "011"))
    return match.group(1) + digits


def parse_time_line(text: str) -> tuple[time | None, time | None, tuple[int, int] | None]:
    """(giờ bắt đầu, giờ kết thúc, (tiết đầu, tiết cuối)) của dòng "13.00 - 15.40 (Tiết 7-9)"."""
    tiet = _TIET_RE.search(text)
    # Bỏ "(Tiết 7-9)" trước khi tìm giờ để "7-9" không bị đọc nhầm thành giờ.
    times = find_times(_TIET_RE.sub(" ", text))
    start = time(*times[0]) if times else None
    end = time(*times[1]) if len(times) > 1 else None
    return start, end, (int(tiet.group(1)), int(tiet.group(2))) if tiet else None


def is_time_line(text: str) -> bool:
    """Dòng giờ: có hai giờ, hoặc có "(Tiết a-b)" (kể cả khi giờ không đọc được)."""
    return len(find_times(_TIET_RE.sub(" ", text))) >= 2 or bool(_TIET_RE.search(text))


def is_e_learning(text: str) -> bool:
    return bool(E_LEARNING_RE.search(text))


def parse_room(text: str) -> str | None:
    """Phòng của một dòng ("Có mặtA6-101.102 (PC)" → "A6-101.102 (PC)"); None nếu không phải phòng.

    Dòng có nhãn "Phòng:" nhận mọi nội dung ("Phòng: Sân thể thao"); dòng không nhãn chỉ nhận mã
    phòng dạng "A6-101".
    """
    text = nfc(text)
    cleaned = _ROOM_PREFIX_RE.sub("", text)
    if is_e_learning(cleaned):
        return "E-Learning"
    if match := _ROOM_RE.match(cleaned):
        return re.sub(r"\s*([-.])\s*", r"\1", match.group(0)).replace("(", " (").replace("  ", " ")
    if _ROOM_LABEL_RE.match(text) and cleaned.strip():
        return cleaned.strip()
    return None


def parse_lecturer(text: str) -> str | None:
    text = nfc(text)
    labelled = _LECTURER_LABEL_RE.sub("", text)
    if labelled != text:
        return labelled or None
    return text if _LECTURER_RE.match(text) else None


def split_class_label(text: str) -> tuple[str, str | None]:
    """ "Tên môn-1-1-26(N01).TH" → ("Tên môn", "1-1-26(N01).TH"); không có hậu tố → (text, None)."""
    text = nfc(text)
    match = _CLASS_SUFFIX_RE.search(text)
    if not match:
        return text, None
    group = fix_digit_letters(match.group(4).strip())
    tail = (match.group(5) or "").upper()
    return text[
        : match.start()
    ].strip(), f"{match.group(1)}-{match.group(2)}-{match.group(3)}({group}){tail}"


def _mean_conf(lines: list[TextBox]) -> float:
    return sum(line.conf for line in lines) / len(lines) if lines else 0.0


def _label_span(texts: list[str]) -> tuple[int, int] | None:
    """Chỉ số [đầu, cuối] của các dòng chứa hậu tố nhóm lớp (có thể ngắt thành hai dòng)."""
    for i, text in enumerate(texts):
        if not _SUFFIX_START_RE.search(text):
            continue
        for j in range(i, min(i + 2, len(texts))):
            if _CLASS_SUFFIX_RE.search(" ".join(texts[i : j + 1])):
                return i, j
        return i, i
    return None


def _join_tiet_continuation(lines: list[TextBox]) -> list[TextBox]:
    """ "15:45 - 18:25 (Tiết" xuống dòng "10-12)" → ghép lại thành một dòng giờ."""
    joined: list[TextBox] = []
    for line in lines:
        if (
            joined
            and _TIET_OPEN_RE.search(joined[-1].text)
            and _TIET_TAIL_RE.match(line.text.strip())
        ):
            prev = joined.pop()
            line = TextBox(
                f"{prev.text} {line.text.strip()}",
                min(prev.x0, line.x0),
                prev.y0,
                max(prev.x1, line.x1),
                line.y1,
                (prev.conf + line.conf) / 2,
            )
        joined.append(line)
    return joined


def extract_fields(lines: list[TextBox]) -> dict[str, tuple[object, float]]:
    """Trường của một ô: {tên trường: (giá trị, độ tin cậy)}; trường không thấy thì không có khoá.

    Khoá: name, class_code, start_time, end_time, tiet, room, lecturer, e_learning.
    """
    fields: dict[str, tuple[object, float]] = {}
    lines = _join_tiet_continuation(lines)
    texts = [nfc(line.text) for line in lines]
    time_idx = next((i for i, t in enumerate(texts) if is_time_line(t)), None)
    if time_idx is not None:
        start, end, tiet = parse_time_line(texts[time_idx])
        for key, value in (("start_time", start), ("end_time", end), ("tiet", tiet)):
            if value:
                fields[key] = (value, lines[time_idx].conf)
        header, body = lines[:time_idx], lines[time_idx + 1 :]
    else:
        header, body = [], lines
    body_texts = [nfc(line.text) for line in body]

    rest_from = 0
    if span := _label_span(body_texts):
        first, last = span
        # Tên môn bị ngắt dòng nằm ngay trước dòng có hậu tố (mọi dòng phía trên trong thân ô).
        label_lines = body[: last + 1]
        name, class_code = split_class_label(" ".join(body_texts[: last + 1]))
        conf = _mean_conf(label_lines)
        if name and header and _CODE_TOKEN_RE.match(name):
            # Cổng dạng có nhãn: dòng này là mã lớp ("MAT1101-1-1-26(N01)"), tên môn ở dòng giờ.
            fields["class_code"] = (f"{fix_code_token(name)}{body_texts[first][len(name) :]}", conf)
            fields["class_code"] = (fix_digit_letters(fields["class_code"][0]), conf)
        else:
            if name:
                fields["name"] = (name, conf)
            if class_code:
                fields["class_code"] = (class_code, conf)
        rest_from = last + 1

    tail = list(zip(body[rest_from:], body_texts[rest_from:], strict=True))
    for k, (line, text) in enumerate(tail):
        if "room" not in fields and (room := parse_room(text)):
            fields["room"] = (room, line.conf)
        elif "class_code" not in fields and _CODE_LINE_RE.match(text):
            fields["class_code"] = (fix_digit_letters(text), line.conf)
        elif "lecturer" not in fields and (lecturer := parse_lecturer(text)):
            nxt = tail[k + 1][1] if k + 1 < len(tail) else ""
            if _LECTURER_LABEL_RE.match(text) and _NAME_TAIL_RE.match(nxt):
                lecturer = f"{lecturer} {nxt}"  # tên giảng viên bị xuống dòng
            fields["lecturer"] = (lecturer, line.conf)

    if "name" not in fields:
        # Không có hậu tố nhóm lớp: tên môn là phần tiêu đề phía trên dòng giờ; nếu ô không có
        # dòng giờ thì lấy dòng còn lại dài nhất (research R3).
        if header:
            fields["name"] = (" ".join(nfc(h.text) for h in header), _mean_conf(header))
        else:
            leftovers = [
                (line, text)
                for line, text in zip(body, body_texts, strict=True)
                if not parse_room(text) and not parse_lecturer(text) and not is_time_line(text)
            ]
            if leftovers:
                line, text = max(leftovers, key=lambda item: len(item[1]))
                fields["name"] = (text, line.conf)
    if shift := next((m for t in texts if (m := _SHIFT_RE.search(t))), None):
        fields["shift_number"] = (int(shift.group(1)), 1.0)
    if any(is_e_learning(t) for t in texts):
        fields["e_learning"] = (True, 1.0)
        fields.setdefault("room", ("E-Learning", 1.0))
    return fields
