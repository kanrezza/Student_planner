"""Buổi thi (FR-055 đến FR-058, FR-063, FR-064).

Hàm thuần ở đầu file; hàm ghi dữ liệu gọi `bump_revision`.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.text import ci_key
from app.lib.timeutil import combine, iso
from app.models import ClassSession, Exam, ExamTag, Tag
from app.services.revision import bump_revision
from app.services.tag_links import replace_tag_links

EXAM_TAG_KEY = "exam"
_DURATION_RE = re.compile(r"(\d{1,3})\s*(?:p\b|phút|phut|min)", re.IGNORECASE)


# ---- Hàm thuần ------------------------------------------------------------------------------


def duration_from_format(exam_format: str | None) -> int | None:
    """Thời lượng (phút) trong hình thức thi: "… 60p" → 60; "Bài tập lớn" → None."""
    if not exam_format:
        return None
    match = _DURATION_RE.search(exam_format)
    return int(match.group(1)) if match else None


def resolve_offsets(reminder_offsets: list[int] | None, is_important: bool, settings) -> list[int]:
    """Phút báo trước của buổi thi (FR-063, FR-069); giảm dần, không trùng.

    `None` = theo mặc định: quan trọng → mốc quan trọng ∪ mốc thêm cho buổi thi; thường → 1 mốc.
    `[]` = tắt nhắc; danh sách riêng được dùng nguyên văn.
    """
    if reminder_offsets is not None:
        return sorted(set(reminder_offsets), reverse=True)
    if is_important:
        merged = set(settings.important_reminder_offsets) | set(
            settings.exam_extra_reminder_offsets
        )
        return sorted(merged, reverse=True)
    return [settings.exam_reminder_minutes]


@dataclass(frozen=True)
class Interval:
    kind: str  # "session" | "exam"
    id: int
    title: str
    start_at: datetime
    end_at: datetime


def find_conflicts(start_at: datetime, end_at: datetime, others: list[Interval]) -> list[Interval]:
    """Các khoảng thời gian giao với [start_at, end_at); chạm mép không tính (FR-058)."""
    return [o for o in others if o.start_at < end_at and start_at < o.end_at]


def is_past(end_at: datetime, now: datetime) -> bool:
    return end_at < now


@dataclass(frozen=True)
class ExamKey:
    code: str | None
    name: str
    date: date
    start: time
    attempt: int


def duplicate_key(
    course_code: str | None, course_name: str, day: date, start: time, attempt: int = 1
) -> ExamKey:
    return ExamKey(
        ci_key(course_code) if course_code and course_code.strip() else None,
        ci_key(course_name),
        day,
        start,
        attempt,
    )


def is_duplicate(a: ExamKey, b: ExamKey) -> bool:
    """Cùng ngày, giờ bắt đầu, lần thi và cùng mã (nếu cả hai có mã) hoặc cùng tên (FR-062)."""
    if (a.date, a.start, a.attempt) != (b.date, b.start, b.attempt):
        return False
    if a.code and b.code:
        return a.code == b.code
    return a.name == b.name


def exam_key(exam: Exam) -> ExamKey:
    from app.lib.timeutil import TZ

    return duplicate_key(
        exam.course_code,
        exam.course_name,
        exam.date,
        exam.start_at.astimezone(TZ).time(),
        exam.attempt,
    )


# ---- Truy vấn -------------------------------------------------------------------------------


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", {field: message})


def get_exam(exam_id: int) -> Exam:
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        raise not_found("Không tìm thấy buổi thi")
    return exam


def list_exams(start: date | None, end: date | None, include_past: bool, now: datetime):
    query = select(Exam)
    if start is not None:
        query = query.where(Exam.date >= start)
    if end is not None:
        query = query.where(Exam.date <= end)
    if not include_past:
        query = query.where(Exam.end_at >= now)
    return list(db.session.scalars(query.order_by(Exam.start_at, Exam.id)))


def exams_in_range(start: date, end: date, tag_ids: list[int]) -> list[Exam]:
    query = select(Exam).where(Exam.date.between(start, end))
    if tag_ids:
        query = query.where(Exam.id.in_(select(ExamTag.exam_id).where(ExamTag.tag_id.in_(tag_ids))))
    return list(db.session.scalars(query.order_by(Exam.start_at)))


def conflicts_for(exams: list[Exam]) -> dict[int, list[dict]]:
    """Trùng giờ của từng buổi thi với buổi học chưa huỷ và buổi thi khác (FR-058)."""
    if not exams:
        return {}
    days = {e.date for e in exams}
    candidates = [
        Interval("session", s.id, s.subject.name, s.start_at, s.end_at)
        for s in db.session.scalars(
            select(ClassSession).where(
                ClassSession.is_cancelled.is_(False), ClassSession.date.in_(days)
            )
        )
    ]
    candidates += [
        Interval("exam", e.id, e.course_name, e.start_at, e.end_at)
        for e in db.session.scalars(select(Exam).where(Exam.date.in_(days)))
    ]
    result = {}
    for exam in exams:
        others = [c for c in candidates if not (c.kind == "exam" and c.id == exam.id)]
        found = find_conflicts(exam.start_at, exam.end_at, others)
        result[exam.id] = [
            {"kind": c.kind, "id": c.id, "title": c.title, "start_at": iso(c.start_at)}
            for c in sorted(found, key=lambda c: c.start_at)
        ]
    return result


def find_duplicate_exam(key: ExamKey) -> int | None:
    """Id buổi thi đã có trong lịch giống `key` (FR-062), hoặc None."""
    from app.lib.timeutil import TZ

    for exam in db.session.scalars(select(Exam).where(Exam.date == key.date)):
        if exam.start_at.astimezone(TZ).time() == key.start and is_duplicate(key, exam_key(exam)):
            return exam.id
    return None


# ---- Ghi dữ liệu ----------------------------------------------------------------------------


def exam_tag() -> Tag:
    return db.session.scalars(select(Tag).where(Tag.system_key == EXAM_TAG_KEY)).one()


def _with_exam_tag_first(tag_ids: list[int]) -> list[int]:
    exam_id = exam_tag().id
    return [exam_id, *[t for t in dict.fromkeys(tag_ids) if t != exam_id]]


def _conflict_warnings(exam: Exam) -> tuple[list[dict], list[dict]]:
    conflicts = conflicts_for([exam])[exam.id]
    warnings = []
    if conflicts:
        names = ", ".join(f"“{c['title']}”" for c in conflicts[:3])
        warnings.append(
            {
                "code": "time_conflict",
                "message": f"Buổi thi “{exam.course_name}” trùng giờ với {names}",
            }
        )
    return conflicts, warnings


def build_exam(data: dict) -> Exam:
    """Tạo đối tượng Exam (chưa commit) từ dữ liệu đã kiểm tra; dùng chung với nhập từ ảnh."""
    start, end = data["start_time"], data["end_time"]
    if end <= start:
        raise _invalid("end_time", "Giờ kết thúc phải sau giờ bắt đầu")
    exam = Exam(
        course_code=data.get("course_code"),
        course_name=data["course_name"],
        attempt=data.get("attempt") or 1,
        date=data["date"],
        start_at=combine(data["date"], start),
        end_at=combine(data["date"], end),
        exam_format=data.get("exam_format"),
        room=data.get("room"),
        candidate_number=data.get("candidate_number"),
        reminder_offsets=data.get("reminder_offsets"),
        is_important=data.get("is_important", True),
    )
    db.session.add(exam)
    db.session.flush()
    replace_tag_links(ExamTag, "exam_id", exam.id, _with_exam_tag_first(data.get("tag_ids") or []))
    return exam


def create_exam(data: dict) -> tuple[Exam, list[dict], list[dict]]:
    exam = build_exam(data)
    bump_revision(db.session)
    db.session.commit()
    db.session.refresh(exam)
    conflicts, warnings = _conflict_warnings(exam)
    return exam, conflicts, warnings


def update_exam(exam_id: int, changes: dict) -> tuple[Exam, list[dict], list[dict]]:
    exam = get_exam(exam_id)
    from app.lib.timeutil import TZ

    for field in (
        "course_name",
        "course_code",
        "attempt",
        "exam_format",
        "room",
        "candidate_number",
        "reminder_offsets",
        "is_important",
    ):
        if field not in changes:
            continue
        if changes[field] is None and field in ("course_name", "attempt", "is_important"):
            continue  # cột bắt buộc: bỏ qua giá trị null
        setattr(exam, field, changes[field])
    if {"date", "start_time", "end_time"} & changes.keys():
        day = changes.get("date") or exam.date
        start = changes.get("start_time") or exam.start_at.astimezone(TZ).time()
        end = changes.get("end_time") or exam.end_at.astimezone(TZ).time()
        if end <= start:
            raise _invalid("end_time", "Giờ kết thúc phải sau giờ bắt đầu")
        exam.date = day
        exam.start_at = combine(day, start)
        exam.end_at = combine(day, end)
    bump_revision(db.session)
    db.session.commit()
    conflicts, warnings = _conflict_warnings(exam)
    return exam, conflicts, warnings


def delete_exam(exam_id: int) -> None:
    exam = get_exam(exam_id)
    db.session.delete(exam)
    bump_revision(db.session)
    db.session.commit()


def set_exam_tags(exam_id: int, tag_ids: list[int]) -> Exam:
    """Nhãn "Thi" luôn được giữ ở vị trí đầu (data-model "tags")."""
    exam = get_exam(exam_id)
    replace_tag_links(ExamTag, "exam_id", exam.id, _with_exam_tag_first(tag_ids))
    bump_revision(db.session)
    db.session.commit()
    db.session.expire(exam, ["tag_links"])
    return exam
