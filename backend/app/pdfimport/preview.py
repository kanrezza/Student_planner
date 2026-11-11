"""Bản xem trước từ các hàng đã đọc: gộp môn, đổi tiết sang giờ, chọn học kỳ (hàm thuần, R9).

Không đụng CSDL: ngữ cảnh (ca, bảng tiết, học kỳ, môn đã có) do tầng dịch vụ nạp rồi truyền vào.
Kết quả là dict JSON-được, đúng `TimetablePdfPreview` trong data-model.md; không chứa thông tin
cá nhân vì phần đầu trang đã bị bỏ ở tầng bố cục (R6).
"""

from dataclasses import dataclass, field
from datetime import date

from app.lib.text import ci_key, fold_key
from app.ocr.fields import is_e_learning
from app.pdfimport.cells import (
    join_cell_lines,
    parse_class_label,
    parse_credits,
    parse_dates,
    parse_day_cell,
    parse_semester_name,
)
from app.pdfimport.layout import DAY_KEYS, RawRow, fold
from app.pdfimport.reader import PdfImportError
from app.services.periods import periods_to_time
from app.services.recurrence import generate_dates

DEFAULT_SEMESTER_NAME = "Học kỳ mới"


@dataclass
class PreviewContext:
    shifts: list  # ca học (id, position, start_time, end_time)
    periods: dict  # {số tiết: (giờ bắt đầu, giờ kết thúc)}
    semesters: list  # (id, name, start_date, end_date)
    existing_subjects: list = field(
        default_factory=list
    )  # môn đã có (kèm quy tắc) để nhận ra khi nhập lại


def _hhmm(value) -> str:
    return value.strftime("%H:%M")


def _problem(field_name: str, level: str, message: str) -> dict:
    return {"field": field_name, "level": level, "message": message}


def build_schedule(weekday: int, cell_text: str, dates: list[date], ctx: PreviewContext) -> dict:
    problems: list[dict] = []
    start = end = None
    if len(dates) >= 2:
        start, end = dates[0], dates[1]
    if len(dates) < 2:
        problems.append(_problem("start_date", "error", "Thiếu ngày bắt đầu hoặc ngày kết thúc"))
    elif end < start:
        problems.append(_problem("end_date", "error", "Ngày kết thúc trước ngày bắt đầu"))
    cell = parse_day_cell(cell_text)
    schedule = {
        "weekday": weekday,
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "period_from": None,
        "period_to": None,
        "shift": None,
        "start_time": None,
        "end_time": None,
        "room": None,
        "session_count": 0,
        "problems": problems,
        "selected": True,
    }
    if cell is None:
        problems.append(
            _problem("period_from", "error", "Không đọc được tiết, hãy chọn ca hoặc giờ")
        )
    else:
        schedule["period_from"], schedule["period_to"] = cell.period_from, cell.period_to
        schedule["room"] = cell.room
        resolved = periods_to_time(cell.period_from, cell.period_to, ctx.periods, ctx.shifts)
        if resolved.error:
            problems.append(_problem("start_time", "error", resolved.error))
        else:
            schedule["start_time"] = _hhmm(resolved.start_time)
            schedule["end_time"] = _hhmm(resolved.end_time)
            if resolved.shift:
                schedule["shift"] = {
                    "start_shift_id": resolved.shift[0],
                    "end_shift_id": resolved.shift[1],
                }
        if cell.room is None:
            problems.append(_problem("room", "warning", "Chưa có phòng học"))
    if start and end and end >= start:
        schedule["session_count"] = len(generate_dates([weekday], start, end))
        if schedule["session_count"] == 0:
            problems.append(
                _problem("start_date", "warning", "Không có buổi nào trong khoảng ngày này")
            )
            schedule["selected"] = False
    return schedule


def _duplicate_warnings(schedules: list[dict]) -> None:
    """Hai quy tắc cùng thứ, trùng ngày và trùng giờ trong một môn → cảnh báo ở quy tắc sau."""
    for i, later in enumerate(schedules):
        for earlier in schedules[:i]:
            same_day = later["weekday"] == earlier["weekday"]
            if (
                same_day
                and later["start_date"]
                and earlier["start_date"]
                and later["start_date"] <= (earlier["end_date"] or "")
                and earlier["start_date"] <= (later["end_date"] or "")
                and later["start_time"] == earlier["start_time"]
            ):
                later["problems"].append(
                    _problem("start_date", "warning", "Trùng ngày và giờ với một lịch khác của môn")
                )
                break


def is_e_learning_room(room: str | None) -> bool:
    """Phòng học trực tuyến ("ONLINE-Elearning", "E-Learning", "online") → gợi ý nhãn E-Learning."""
    if not room:
        return False
    compact = fold(room).replace("-", "").replace(" ", "")
    return "elearning" in compact or "online" in compact or is_e_learning(room)


def match_existing(subject: dict, existing_subjects: list):
    """Môn đã có khớp với môn trong PDF (R9, FR-021): cùng mã lớp (không phân biệt hoa thường)
    VÀ (cùng mã học phần HOẶC cùng tên không phân biệt dấu). Không khớp → None."""
    class_key = ci_key(subject["class_code"] or "")
    for existing in existing_subjects:
        if ci_key(existing.class_code or "") != class_key:
            continue
        same_code = bool(
            subject["course_code"]
            and existing.course_code
            and ci_key(existing.course_code) == ci_key(subject["course_code"])
        )
        if same_code or fold_key(existing.name) == fold_key(subject["name"]):
            return existing
    return None


def _existing_rules(existing) -> list[tuple]:
    rules = []
    for rule in existing.schedules:
        for weekday in rule.weekdays:
            rules.append(
                (
                    weekday,
                    rule.start_date.isoformat(),
                    rule.end_date.isoformat(),
                    _hhmm(rule.start_time),
                    _hhmm(rule.end_time),
                    rule.room or None,
                )
            )
    return rules


def _preview_rules(subject: dict) -> list[tuple]:
    return [
        (r["weekday"], r["start_date"], r["end_date"], r["start_time"], r["end_time"], r["room"])
        for r in subject["schedules"]
    ]


def _rule_text(rule: tuple) -> str:
    weekday, start, end, begin, finish, room = rule
    days = {7: "CN"}.get(weekday, f"T{weekday + 1}")
    parts = [days, f"{begin}–{finish}"] + ([room] if room else [])
    return f"{' · '.join(parts)} ({start[8:]}/{start[5:7]}–{end[8:]}/{end[5:7]})"


def diff_subject(existing, subject: dict) -> list[dict]:
    """Khác biệt giữa môn đã có và môn trong PDF; rỗng nghĩa là giống hệt (`unchanged`)."""
    diff: list[dict] = []
    for label, before, after in (
        ("Tên", existing.name, subject["name"]),
        ("Mã học phần", existing.course_code, subject["course_code"]),
        ("Số tín chỉ", existing.credits, subject["credits"]),
    ):
        if after is not None and before != after:
            diff.append(
                {
                    "field": label,
                    "before": None if before is None else str(before),
                    "after": str(after),
                }
            )
    old, new = _existing_rules(existing), _preview_rules(subject)
    only_old = [r for r in old if r not in new]
    only_new = [r for r in new if r not in old]
    # Cùng thứ, ngày, giờ mà khác phòng → một dòng "Phòng: a → b".
    for rule in list(only_new):
        twin = next((o for o in only_old if o[:5] == rule[:5]), None)
        if twin is not None:
            diff.append({"field": "Phòng", "before": twin[5], "after": rule[5]})
            only_old.remove(twin)
            only_new.remove(rule)
    diff += [{"field": "Lịch", "before": _rule_text(r), "after": None} for r in only_old]
    diff += [{"field": "Lịch", "before": None, "after": _rule_text(r)} for r in only_new]
    return diff


def apply_existing(subjects: list[dict], existing_subjects: list) -> None:
    """Gắn `status`, `existing_subject_id`, `diff` cho từng môn (môn giống hệt mặc định bỏ chọn)."""
    for subject in subjects:
        existing = match_existing(subject, existing_subjects)
        if existing is None:
            continue
        subject["existing_subject_id"] = existing.id
        subject["diff"] = diff_subject(existing, subject)
        subject["status"] = "changed" if subject["diff"] else "unchanged"
        if subject["status"] == "unchanged":
            subject["selected"] = False
            for rule in subject["schedules"]:
                rule["selected"] = False


def group_subjects(rows: list[RawRow], ctx: PreviewContext) -> list[dict]:
    """Gộp các hàng cùng (mã HP, mã lớp) thành một môn, mỗi ô thứ có nội dung = 1 quy tắc."""
    subjects: dict[tuple[str, str], dict] = {}
    for row in rows:
        course_code = join_cell_lines(row.cells["course"], "course_code")
        name, class_code = parse_class_label(join_cell_lines(row.cells["class"], "class_label"))
        key = (course_code, class_code or name)
        subject = subjects.get(key)
        if subject is None:
            subject = subjects[key] = {
                "course_code": course_code or None,
                "name": name,
                "class_code": class_code,
                "credits": parse_credits(" ".join(row.cells["credits"])),
                "status": "new",
                "existing_subject_id": None,
                "diff": [],
                "suggested_tags": [],
                "selected": True,
                "schedules": [],
            }
        dates = parse_dates(join_cell_lines(row.cells["dates"], "dates"))
        for index, day_key in enumerate(DAY_KEYS):
            lines = row.cells[day_key]
            if not lines:
                continue
            text = join_cell_lines(lines, "day_cell")
            subject["schedules"].append(build_schedule(index + 1, text, dates, ctx))
    result = list(subjects.values())
    for subject in result:
        _duplicate_warnings(subject["schedules"])
        if any(is_e_learning_room(r["room"]) for r in subject["schedules"]):
            subject["suggested_tags"] = ["e_learning"]
        subject["selected"] = any(s["selected"] for s in subject["schedules"])
    return result


def choose_semester(start: date, end: date, semesters: list, suggested_name: str | None) -> dict:
    """Đề xuất học kỳ cho khoảng [start, end] của mọi quy tắc (FR-018)."""
    base = {
        "suggested_name": suggested_name or DEFAULT_SEMESTER_NAME,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    containing = [s for s in semesters if s.start_date <= start and end <= s.end_date]
    if containing:
        best = min(containing, key=lambda s: (s.end_date - s.start_date, s.start_date))
        return {
            **base,
            "choice": "use",
            "semester_id": best.id,
            "name": best.name,
            "start_date": best.start_date.isoformat(),
            "end_date": best.end_date.isoformat(),
        }
    overlapping = [s for s in semesters if s.start_date <= end and start <= s.end_date]
    if not overlapping:
        return {**base, "choice": "create"}
    if len(overlapping) == 1:
        only = overlapping[0]
        return {
            **base,
            "choice": "extend",
            "semester_id": only.id,
            "name": only.name,
            "start_date": min(start, only.start_date).isoformat(),
            "end_date": max(end, only.end_date).isoformat(),
        }
    return {
        **base,
        "choice": "conflict",
        "conflicts": [
            {
                "id": s.id,
                "name": s.name,
                "start_date": s.start_date.isoformat(),
                "end_date": s.end_date.isoformat(),
            }
            for s in overlapping
        ],
    }


def build_timetable_preview(
    rows: list[RawRow], semester_line: str | None, ctx: PreviewContext
) -> dict:
    subjects = group_subjects(rows, ctx)
    warnings: list[dict] = []
    name = parse_semester_name(semester_line)
    if name is None:
        warnings.append(
            {
                "code": "no_semester_line",
                "message": "Không đọc được dòng học kỳ trong file, hãy kiểm tra tên học kỳ.",
            }
        )
    starts = [s["start_date"] for sub in subjects for s in sub["schedules"] if s["start_date"]]
    ends = [s["end_date"] for sub in subjects for s in sub["schedules"] if s["end_date"]]
    if not subjects or not starts or not ends:
        raise PdfImportError(
            422, "pdf_not_timetable", "Không đọc được môn học hoặc ngày học nào trong bảng."
        )
    semester = choose_semester(
        date.fromisoformat(min(starts)), date.fromisoformat(max(ends)), ctx.semesters, name
    )
    if semester["choice"] in ("use", "extend"):
        target = [e for e in ctx.existing_subjects if e.semester_id == semester["semester_id"]]
        apply_existing(subjects, target)
    return {"semester": semester, "subjects": subjects, "warnings": warnings}
