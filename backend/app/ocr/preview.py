"""Ghép kết quả OCR thành `ImportPreview` (data-model "ImportPreview", research R3 bước 6–9).

`build_preview` là hàm thuần: mọi dữ liệu cần từ database (ca học, học kỳ, buổi đã có…) được truyền
vào qua `PreviewContext`, nên test được bằng `TextBox` dựng tay.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, time

from rapidfuzz import fuzz

from app.lib.text import ci_key, fold_key
from app.lib.timeutil import combine
from app.ocr.exam_table import ExamRowData, format_duration, parse_exam_table
from app.ocr.fields import extract_exam_fields, extract_fields, is_exam_cell
from app.ocr.layout import (
    WeekdayHeader,
    detect_layout,
    filter_chrome,
    find_week_headers,
    group_cells,
    split_menu_bar,
)
from app.ocr.month_year import MonthYear, infer_month_year
from app.ocr.reader import TextBox
from app.services.exams import ExamKey, duplicate_key, is_duplicate
from app.services.shifts import match_shift_range

MIN_CONFIDENCE = 0.6  # dưới mức này → ô tô vàng "chưa chắc chắn"
NAME_FIX_RATIO = 90  # tên gần giống môn đã có (rapidfuzz ≥ 90) → sửa theo tên đã có
# Tên đọc kém (độ tin cậy thấp): so không dấu, ngưỡng thấp hơn nhưng phải hơn hẳn ứng viên thứ hai.
WEAK_NAME_FIX_RATIO = 70
WEAK_NAME_MARGIN = 15
KIND_BY_LAYOUT = {"week_grid": "week_schedule", "list": "week_schedule", "exam_table": "exam_table"}


@dataclass(frozen=True)
class ExistingSession:
    id: int
    name: str
    class_code: str | None
    date: date
    start_time: time


@dataclass
class PreviewContext:
    now: datetime
    shifts: list = field(default_factory=list)  # Shift (id, position, start_time, end_time)
    semesters: list = field(default_factory=list)  # Semester (id, start_date, end_date)
    subject_names: list[str] = field(default_factory=list)
    canonical_names: list[str] = field(default_factory=list)  # tên môn chuẩn từ PDF (feature 004)
    sessions: list[ExistingSession] = field(default_factory=list)
    exams: list[tuple[ExamKey, int]] = field(default_factory=list)


# ---- Hàm thuần nhỏ -----------------------------------------------------------------------------


def _hhmm(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def _field(
    value, conf: float = 1.0, reason: str | None = None, certain: bool | None = None
) -> dict:
    """Một trường xem trước: {value, certain, reason?}. Giá trị rỗng/None luôn là chưa chắc chắn
    nếu là trường bắt buộc (do người gọi quyết định qua `certain`)."""
    ok = conf >= MIN_CONFIDENCE if certain is None else certain
    result = {"value": value, "certain": ok}
    if not ok and reason is None and value is not None:
        reason = "Độ tin cậy nhận diện thấp, hãy kiểm tra lại"
    if reason:
        result["reason"] = reason
    return result


def _month_shift(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _make_date(year: int, month: int, day: int) -> date | None:
    if 1 <= day <= calendar.monthrange(year, month)[1]:
        return date(year, month, day)
    return None


def week_dates(
    days: list[int | None], weekdays: list[int], center: tuple[int, int]
) -> tuple[list[date | None], bool]:
    """Ngày đầy đủ của từng cột từ số ngày in trên tiêu đề ("28 29 30 01 02 03 04") và tháng/năm.

    Tuần vắt qua hai tháng (số ngày giảm giữa chừng) và tháng gợi ý có thể sai, nên thử vài cách gán
    tháng rồi chọn cách cho thứ khớp tiêu đề cột nhiều nhất. Trả (ngày, chắc chắn): chắc chắn khi
    cách đầu tiên (đúng tháng gợi ý) khớp toàn bộ.
    """
    drops = [
        i
        for i in range(1, len(days))
        if None not in (days[i - 1], days[i]) and days[i] < days[i - 1]
    ]
    split = drops[0] if drops else None
    options: list[
        tuple[int, int, int | None]
    ] = []  # (tháng gốc, độ lệch tháng cho nửa trước, split)
    for delta in (0, -1, 1):
        base = _month_shift(*center, delta)
        if split is None:
            options.append((*base, None))
        else:
            options.append((*base, split))  # nửa trước ở tháng gốc, nửa sau ở tháng kế
            options.append((*_month_shift(*base, -1), split))  # nửa sau ở tháng gốc

    def build(year: int, month: int, cut: int | None) -> list[date | None]:
        dates = []
        for i, day in enumerate(days):
            y, m = (year, month) if cut is None or i < cut else _month_shift(year, month, 1)
            dates.append(_make_date(y, m, day) if day is not None else None)
        return dates

    def matches(dates: list[date | None]) -> int:
        return sum(1 for d, w in zip(dates, weekdays, strict=True) if d and d.isoweekday() == w)

    results = [build(*opt) for opt in options]
    scores = [matches(dates) for dates in results]
    best = max(range(len(options)), key=lambda i: (scores[i], -i))
    known = sum(1 for d in days if d is not None)
    full = [i for i, score in enumerate(scores) if known and score == known]
    hinted = {0} if split is None else {0, 1}  # các cách dùng đúng tháng gợi ý của ảnh
    distinct = {tuple(results[i]) for i in full}  # cách gán khác nhau cho cùng kết quả chỉ tính một
    certain = len(distinct) == 1 and best in full and bool(set(full) & hinted)
    return results[best], certain


def shift_from_tiet(tiet: tuple[int, int], shifts: list) -> tuple[int, int] | None:
    """ "Tiết a-b" của cổng ↔ dãy ca (mỗi ca 3 tiết: Tiết 1-3 = Ca 1…); None nếu không khớp."""
    first, last = tiet
    ordered = sorted(shifts, key=lambda s: s.position)
    if (first - 1) % 3 or last % 3 or first > last:
        return None
    i, j = (first - 1) // 3, last // 3 - 1
    return (ordered[i].id, ordered[j].id) if 0 <= i <= j < len(ordered) else None


def _shift_times(ids: tuple[int, int], shifts: list) -> tuple[time, time]:
    by_id = {s.id: s for s in shifts}
    return by_id[ids[0]].start_time, by_id[ids[1]].end_time


def semester_of(day: date | None, semesters: list):
    if day is None:
        return None
    return next((s for s in semesters if s.start_date <= day <= s.end_date), None)


def _fix_name(name: str, known: list[str]) -> tuple[str, bool]:
    """Sửa tên môn theo tên đã có nếu gần giống (rapidfuzz ≥ 90). Trả (tên, đã sửa)."""
    key = ci_key(name)
    best, score = None, 0.0
    for candidate in known:
        ratio = fuzz.ratio(key, ci_key(candidate))
        if ratio > score:
            best, score = candidate, ratio
    if best is not None and score >= NAME_FIX_RATIO and ci_key(best) != key:
        return best, True
    return name, False


def _fix_weak_name(name: str, known: list[str]) -> tuple[str, bool]:
    """Tên đọc kém ("Tal uuhóa", "TIch hop va phan Uch dữ…") → tên đã biết giống nhất (không dấu).

    Chỉ sửa khi giống ≥ 70% và hơn ứng viên thứ hai ≥ 15 điểm, để không đoán bừa; kết quả vẫn bị
    tô "chưa chắc chắn" nên người dùng xem lại ở bảng xem trước.
    """
    key = fold_key(name)
    scored = sorted(((fuzz.ratio(key, fold_key(c)), c) for c in set(known)), reverse=True)
    if not scored or scored[0][0] < WEAK_NAME_FIX_RATIO:
        return name, False
    if len(scored) > 1 and scored[0][0] - scored[1][0] < WEAK_NAME_MARGIN:
        return name, False
    return scored[0][1], scored[0][1] != name


# ---- Lịch học -----------------------------------------------------------------------------------


CANONICAL_REASON = "Đã sửa theo thời khoá biểu"
TRUNCATED_REASON = "Ô bị cắt ở mép dưới ảnh, chỉ đọc được dòng tiêu đề — hãy kiểm tra lại"


def _is_truncated(fields: dict) -> bool:
    """Ô bị cắt ở mép dưới: có dòng giờ nhưng không có phần thân (nhóm lớp, phòng, giảng viên)."""
    has_time = "start_time" in fields or "tiet" in fields
    return has_time and not ({"class_code", "room", "lecturer"} & fields.keys())


def _week_dates_for(
    month_year: MonthYear, headers: list[WeekdayHeader]
) -> tuple[dict[int, date | None], bool]:
    weekdays = [h.weekday for h in headers]
    if all(h.full_date for h in headers):
        dates, dates_certain = [h.full_date for h in headers], True
    else:
        center = tuple(int(p) for p in month_year.value.split("-")) if month_year.value else None
        if center is None:
            dates, dates_certain = [None] * len(headers), False
        else:
            dates, dates_certain = week_dates([h.day for h in headers], weekdays, center)
    return dict(zip(weekdays, dates, strict=True)), dates_certain


def _week_rows(
    content: list[TextBox], headers: list[WeekdayHeader], month_year: MonthYear, ctx: PreviewContext
) -> tuple[list[dict], list[dict]]:
    """(buổi học, buổi thi). Ô "Lịch thi: …" trong lưới tuần là buổi thi, không phải môn."""
    date_of, dates_certain = _week_dates_for(month_year, headers)

    parsed = []
    for cell in group_cells(content, headers):
        if is_exam_cell(cell.lines):
            parsed.append((cell, extract_exam_fields(cell.lines), True))
            continue
        fields = extract_fields(cell.lines)
        if not ({"start_time", "tiet", "class_code"} & fields.keys()):
            continue  # ô không có dấu hiệu của buổi học (chữ rác)
        parsed.append((cell, fields, False))

    # Tên đọc rõ ở các ô khác trong ảnh (có hậu tố nhóm lớp) giúp sửa tên của ô bị cắt/đọc kém.
    in_image = [
        str(f["name"][0]) for _, f, exam in parsed if not exam and "name" in f and "class_code" in f
    ]
    known = ctx.subject_names + in_image

    rows, exam_rows = [], []
    for cell, fields, exam in parsed:
        day = date_of.get(cell.weekday)
        if exam:
            exam_rows.append(_exam_cell_row(fields, day, dates_certain, known, ctx))
        else:
            rows.append(_week_row(cell.weekday, day, dates_certain, month_year, fields, ctx, known))
    _mark_exam_duplicates_in_image(exam_rows)
    return _mark_duplicates_and_merges(rows, ctx), exam_rows


def _exam_cell_row(
    fields: dict, day: date | None, dates_certain: bool, known: list[str], ctx: PreviewContext
) -> dict:
    """Buổi thi từ ô "Lịch thi: …" của lưới tuần (cùng dạng với dòng của bảng lịch thi)."""
    name, name_conf = fields.get("name", (None, 0.0))
    if name:
        name = str(name)
        fixed, changed = _fix_weak_name(name, ctx.canonical_names)
        if not changed:
            fixed, changed = _fix_name(name, known)
        if not changed:
            fixed, changed = _fix_weak_name(name, known)
        name = fixed
        if changed:
            name_conf = 0.0  # đã đoán theo tên có sẵn → luôn để người dùng xem lại
    start, start_conf = fields.get("start_time", (None, 0.0))
    end, end_conf = fields.get("end_time", (None, 0.0))
    fmt, fmt_conf = fields.get("exam_format", (None, 1.0))
    room, room_conf = fields.get("room", (None, 1.0))
    end_source = "image" if end else None
    if start and not end and (minutes := format_duration(fmt)):
        total = start.hour * 60 + start.minute + minutes
        if total < 24 * 60:
            end, end_source = time(total // 60, total % 60), "format_duration"
    data = ExamRowData(
        course_code=(None, 1.0),
        course_name=(name, name_conf),
        attempt=(1, 1.0, True),
        date=(day, 1.0 if dates_certain else 0.0),
        start_time=(start, start_conf),
        end_time=(end, end_conf),
        end_time_source=end_source,
        exam_format=(fmt, fmt_conf),
        room=(room, room_conf),
        candidate_number=(None, 1.0),
    )
    row = _exam_row(data, ctx)
    if not dates_certain and day is not None:
        row["fields"]["date"]["reason"] = "Ngày suy ra từ tháng/năm trong ảnh, hãy kiểm tra lại"
    return row


def _week_row(weekday, day, dates_certain, month_year, fields, ctx, known=None) -> dict:
    known = ctx.subject_names if known is None else known
    truncated = _is_truncated(fields)

    def get(key):
        return fields.get(key, (None, 1.0))

    name, name_conf = get("name")
    reason, weak = None, False
    if name:
        # Tên chuẩn từ PDF thời khoá biểu là nguồn đúng: sửa cả khi OCR tự tin (R11).
        name, fixed = _fix_weak_name(str(name), ctx.canonical_names)
        if fixed:
            reason = CANONICAL_REASON
        else:
            name, fixed = _fix_name(str(name), known)
            reason = "Đã sửa theo tên môn có sẵn" if fixed else None
        if not fixed and (name_conf < MIN_CONFIDENCE or truncated):
            name, fixed = _fix_weak_name(str(name), known)
            if fixed:
                name_conf, weak = 0.0, True
                reason = "Tên đọc kém, đã đoán theo tên môn khác — hãy kiểm tra lại"
    name_field = (
        _field(name, name_conf, reason, certain=(not weak) if reason else None)
        if name
        else _field(None, certain=False, reason="Không đọc được tên môn")
    )

    start, start_conf = get("start_time")
    end, end_conf = get("end_time")
    tiet, _ = get("tiet")
    shift_ids = None
    time_reason = None
    tiet_ids = shift_from_tiet(tiet, ctx.shifts) if tiet else None
    if start and end:
        shift_ids = match_shift_range(start, end, ctx.shifts)
        if shift_ids:
            start, end = _shift_times(shift_ids, ctx.shifts)
        elif tiet_ids:
            shift_ids = tiet_ids
            start, end = _shift_times(tiet_ids, ctx.shifts)
            time_reason, start_conf, end_conf = "Giờ đọc lệch, đã lấy theo tiết", 0.0, 0.0
    elif tiet_ids:
        shift_ids = tiet_ids
        start, end = _shift_times(tiet_ids, ctx.shifts)
        time_reason, start_conf, end_conf = "Giờ lấy theo tiết, hãy kiểm tra lại", 0.0, 0.0
    start_field = (
        _field(_hhmm(start), start_conf, time_reason)
        if start
        else _field(None, certain=False, reason="Không đọc được giờ bắt đầu")
    )
    end_field = (
        _field(_hhmm(end), end_conf, time_reason)
        if end
        else _field(None, certain=False, reason="Không đọc được giờ kết thúc")
    )

    if day is None:
        date_field = _field(
            None, certain=False, reason="Không xác định được ngày (thiếu tháng/năm)"
        )
    else:
        date_field = _field(
            day.isoformat(),
            certain=dates_certain and month_year.certain or dates_certain,
            reason=None
            if dates_certain
            else "Ngày suy ra từ tháng/năm trong ảnh, hãy kiểm tra lại",
        )
    weekday_ok = day is not None and day.isoweekday() == weekday
    weekday_field = _field(
        weekday,
        certain=weekday_ok,
        reason=None if weekday_ok else "Ngày không khớp với thứ trong ảnh",
    )

    room, room_conf = get("room")
    lecturer, lecturer_conf = get("lecturer")
    code, code_conf = get("class_code")
    semester = semester_of(day, ctx.semesters)
    until = semester.end_date if semester else day
    if truncated:
        for field_ in (name_field, start_field, end_field):
            field_["certain"] = False
            field_["reason"] = TRUNCATED_REASON
    return {
        "fields": {
            "name": name_field,
            "class_code": _field(code, code_conf) if code else _field(None, certain=True),
            "date": date_field,
            "weekday": weekday_field,
            "start_time": start_field,
            "end_time": end_field,
            "room": _field(room, room_conf) if room else _field(None, certain=True),
            "lecturer": _field(lecturer, lecturer_conf) if lecturer else _field(None, certain=True),
        },
        "shift": (
            {"start_shift_id": shift_ids[0], "end_shift_id": shift_ids[1]} if shift_ids else None
        ),
        "shift_note": None if shift_ids or not start else "Giờ tuỳ chỉnh – không khớp ca nào",
        "truncated": truncated,
        "suggested_tags": ["e_learning"] if "e_learning" in fields else [],
        "semester_id": semester.id if semester else None,
        "duplicate_of_session_id": None,
        "repeat": {
            "mode": "weekly" if semester else "once",
            "until": until.isoformat() if until else None,
        },
        "merge_group": None,
        "merge_accepted": False,
        "selected": True,
    }


def _mark_duplicates_and_merges(rows: list[dict], ctx: PreviewContext) -> list[dict]:
    seen: set[tuple] = set()
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        f = row["fields"]
        name, code = f["name"]["value"], f["class_code"]["value"]
        day, start = f["date"]["value"], f["start_time"]["value"]
        if not (name and day and start):
            continue
        for existing in ctx.sessions:
            same_class = ci_key(existing.name) == ci_key(name) or (
                code and existing.class_code and ci_key(existing.class_code) == ci_key(code)
            )
            if (
                same_class
                and existing.date.isoformat() == day
                and _hhmm(existing.start_time) == start
            ):
                row["duplicate_of_session_id"] = existing.id
                row["selected"] = False
                break
        key = (ci_key(name), day, start)
        if key in seen:  # trùng giữa các dòng trong cùng ảnh
            row["selected"] = False
            row["duplicate_in_image"] = True
        seen.add(key)
        groups.setdefault(
            (ci_key(name), f["weekday"]["value"], start, f["end_time"]["value"]), []
        ).append(row)
    for number, members in enumerate((g for g in groups.values() if len(g) > 1), start=1):
        for row in members:
            row["merge_group"] = f"g{number}"
    return rows


# ---- Lịch thi -----------------------------------------------------------------------------------


def _exam_row(data: ExamRowData, ctx: PreviewContext) -> dict:
    name, name_conf = data.course_name
    day, day_conf = data.date
    start, start_conf = data.start_time
    end, end_conf = data.end_time
    code, code_conf = data.course_code
    fmt, fmt_conf = data.exam_format
    room, room_conf = data.room
    sbd, sbd_conf = data.candidate_number
    attempt, attempt_conf, attempt_ok = data.attempt

    if end is None:
        end_field = _field(
            None,
            certain=False,
            reason="Không có giờ kết thúc và không suy ra được từ hình thức thi",
        )
    elif data.end_time_source == "format_duration":
        end_field = _field(_hhmm(end), certain=True, reason=f"Giờ kết thúc tính từ “{fmt}”")
    else:
        end_field = _field(_hhmm(end), end_conf)
    fields = {
        "course_code": _field(code, code_conf) if code else _field(None, certain=True),
        "course_name": _field(name, name_conf)
        if name
        else _field(None, certain=False, reason="Không đọc được tên học phần"),
        "attempt": _field(
            attempt, attempt_conf, certain=attempt_ok and attempt_conf >= MIN_CONFIDENCE
        ),
        "date": _field(day.isoformat(), day_conf)
        if day
        else _field(None, certain=False, reason="Không đọc được ngày thi"),
        "start_time": _field(_hhmm(start), start_conf)
        if start
        else _field(None, certain=False, reason="Không đọc được giờ bắt đầu"),
        "end_time": end_field,
        "exam_format": _field(fmt, fmt_conf) if fmt else _field(None, certain=True),
        "room": _field(room, room_conf) if room else _field(None, certain=True),
        "candidate_number": _field(sbd, sbd_conf) if sbd else _field(None, certain=True),
    }
    is_past = bool(day and end and combine(day, end) < ctx.now)
    duplicate_id = None
    if name and day and start:
        key = duplicate_key(code, name, day, start, attempt)
        duplicate_id = next(
            (eid for existing, eid in ctx.exams if is_duplicate(key, existing)), None
        )
    return {
        "fields": fields,
        "end_time_source": data.end_time_source,
        "is_past": is_past,
        "duplicate_of_exam_id": duplicate_id,
        "selected": not is_past and duplicate_id is None,
    }


def _mark_exam_duplicates_in_image(rows: list[dict]) -> None:
    keys: list[ExamKey] = []
    for row in rows:
        f = row["fields"]
        if not (f["course_name"]["value"] and f["date"]["value"] and f["start_time"]["value"]):
            continue
        key = duplicate_key(
            f["course_code"]["value"],
            f["course_name"]["value"],
            date.fromisoformat(f["date"]["value"]),
            time.fromisoformat(f["start_time"]["value"]),
            f["attempt"]["value"],
        )
        if any(is_duplicate(key, other) for other in keys):
            row["selected"] = False
            row["duplicate_in_image"] = True
        keys.append(key)


# ---- Điểm vào -----------------------------------------------------------------------------------


def build_preview(
    boxes: list[TextBox],
    image_size: tuple[int, int],
    ctx: PreviewContext,
    kind: str | None = None,
) -> dict:
    """`ImportPreview` dạng dict (JSON). `kind` ép loại ảnh khi lần trước trả "unknown" (FR-059)."""
    menu, _ = split_menu_bar(boxes, image_size)
    content = filter_chrome(boxes, image_size)
    resolved = kind or KIND_BY_LAYOUT.get(detect_layout(content), "unknown")

    if resolved == "exam_table":
        rows = [_exam_row(r, ctx) for r in parse_exam_table(content)]
        _mark_exam_duplicates_in_image(rows)
        return {"kind": "exam_table", "exam_rows": rows}
    if resolved == "week_schedule":
        headers = find_week_headers(content)
        month_year = infer_month_year(content, headers, menu, ctx.now.date())
        rows, exam_rows = _week_rows(content, headers, month_year, ctx) if headers else ([], [])
        return {
            "kind": "week_schedule",
            "month_year": month_year.as_dict(),
            "rows": rows,
            "exam_rows": exam_rows,
        }
    return {"kind": "unknown"}
