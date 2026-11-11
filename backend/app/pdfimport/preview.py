"""Bản xem trước từ các hàng đã đọc: gộp môn, đổi tiết sang giờ, chọn học kỳ (hàm thuần, R9).

Không đụng CSDL: ngữ cảnh (ca, bảng tiết, học kỳ, môn đã có) do tầng dịch vụ nạp rồi truyền vào.
Kết quả là dict JSON-được, đúng `TimetablePdfPreview` trong data-model.md; không chứa thông tin
cá nhân vì phần đầu trang đã bị bỏ ở tầng bố cục (R6).
"""

from dataclasses import dataclass, field
from datetime import date

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
    existing_subjects: list = field(default_factory=list)  # dùng ở US3 (nhập lại)


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
        rooms = " ".join(fold(s["room"] or "") for s in subject["schedules"])
        if "elearning" in rooms.replace("-", "").replace(" ", ""):
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
    return {"semester": semester, "subjects": subjects, "warnings": warnings}
