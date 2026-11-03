"""Môn học và buổi học (FR-007 đến FR-015, FR-039).

Mọi kiểm tra trả lỗi theo tên trường; với nhập nhiều môn, tên trường có tiền tố `rows[i].`
để giao diện chỉ đúng ô lỗi (FR-010).
"""

from dataclasses import dataclass
from datetime import date, time

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.timeutil import combine
from app.models import ClassSession, Shift, Subject, SubjectTag
from app.services import auto_deadlines
from app.services import semesters as semester_service
from app.services.colors import is_palette_color, next_color
from app.services.recurrence import ExistingSession, generate_dates, plan_regeneration
from app.services.revision import bump_revision
from app.services.shifts import resolve_range
from app.services.tag_links import replace_tag_links

MAX_CONFLICTS_LISTED = 3


class FieldErrors(Exception):
    """Gom nhiều lỗi trường (để báo cùng lúc mọi dòng lỗi khi nhập nhiều môn)."""

    def __init__(self, fields: dict[str, str]):
        super().__init__("field errors")
        self.fields = fields


def _raise_fields(fields: dict[str, str]):
    raise ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", fields)


def _fmt(d: date) -> str:
    return d.strftime("%d/%m/%Y")


@dataclass
class Resolved:
    """Giá trị đã kiểm tra, sẵn sàng ghi vào bảng `subjects`."""

    values: dict
    tag_ids: list[int]


# ---- Kiểm tra và chuẩn hoá đầu vào ------------------------------------------------------------


def resolve_semester(semester_id: int | None):
    if semester_id is not None:
        semester = semester_service.get_semester(semester_id)
    else:
        semester = semester_service.current_semester()
    if semester is None:
        _raise_fields({"semester_id": "Chưa có học kỳ nào. Hãy tạo học kỳ trước khi thêm môn."})
    return semester


def resolve_times(data: dict, prefix: str = "") -> tuple[time, time, int | None, int | None]:
    """Giờ học từ ca (`shift`) hoặc giờ tuỳ chỉnh.

    Trả (giờ bắt đầu, giờ kết thúc, start_shift_id, end_shift_id).
    """
    shift = data.get("shift")
    start, end = data.get("start_time"), data.get("end_time")
    if shift and (start or end):
        raise FieldErrors(
            {f"{prefix}start_time": "Chọn ca học hoặc nhập giờ tuỳ chỉnh, không cả hai"}
        )
    if shift:
        first = db.session.get(Shift, shift["start_shift_id"])
        last = db.session.get(Shift, shift["end_shift_id"])
        if first is None or last is None:
            raise FieldErrors({f"{prefix}shift": "Ca học không tồn tại"})
        if last.position < first.position:
            raise FieldErrors({f"{prefix}shift": "Ca kết thúc phải sau hoặc trùng ca bắt đầu"})
        start_time, end_time = resolve_range(first, last)
        return start_time, end_time, first.id, last.id
    if start is None or end is None:
        raise FieldErrors(
            {f"{prefix}start_time": "Cần chọn ca học hoặc nhập giờ bắt đầu và kết thúc"}
        )
    if end <= start:
        raise FieldErrors({f"{prefix}end_time": "Giờ kết thúc phải sau giờ bắt đầu"})
    return start, end, None, None


def resolve_dates(
    semester, start: date | None, end: date | None, prefix: str = ""
) -> tuple[date, date]:
    start = start or semester.start_date
    end = end or semester.end_date
    inside = f"Phải nằm trong học kỳ ({_fmt(semester.start_date)} – {_fmt(semester.end_date)})"
    errors = {}
    if not semester.start_date <= start <= semester.end_date:
        errors[f"{prefix}start_date"] = inside
    if not semester.start_date <= end <= semester.end_date:
        errors[f"{prefix}end_date"] = inside
    elif end < start:
        errors[f"{prefix}end_date"] = "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu"
    if errors:
        raise FieldErrors(errors)
    return start, end


def resolve_subject(
    data: dict, semester, start, end, used_colors: list[str], prefix=""
) -> Resolved:
    start_time, end_time, start_shift_id, end_shift_id = resolve_times(data, prefix)
    color = data.get("color") or next_color(used_colors)
    if not is_palette_color(color):
        raise FieldErrors({f"{prefix}color": "Màu không hợp lệ"})
    values = {
        "semester_id": semester.id,
        "name": data["name"],
        "class_code": data.get("class_code"),
        "lecturer": data.get("lecturer"),
        "room": data.get("room"),
        "color": color,
        "weekdays": data["weekdays"],
        "start_shift_id": start_shift_id,
        "end_shift_id": end_shift_id,
        "start_time": start_time,
        "end_time": end_time,
        "start_date": start,
        "end_date": end,
        "reminder_minutes": data.get("reminder_minutes"),
    }
    return Resolved(values, data.get("tag_ids") or [])


def _used_colors() -> list[str]:
    return list(db.session.scalars(select(Subject.color)))


# ---- Buổi học ---------------------------------------------------------------------------------


def _existing(subject: Subject) -> list[ExistingSession]:
    return [
        ExistingSession(
            id=s.id,
            date=s.date,
            start_at=s.start_at,
            end_at=s.end_at,
            room=s.room,
            is_cancelled=s.is_cancelled,
            time_overridden=s.time_overridden,
            room_overridden=s.room_overridden,
        )
        for s in subject.sessions
    ]


def regenerate_sessions(subject: Subject, force: bool = False) -> list[ClassSession]:
    """Đưa buổi học về khớp với môn.

    Buổi có ngoại lệ nằm ngoài khoảng mới → 409, trừ khi `force` (khi đó các buổi này bị xoá).
    """
    plan = plan_regeneration(
        _existing(subject),
        generate_dates(subject.weekdays, subject.start_date, subject.end_date),
        subject.start_time,
        subject.end_time,
        subject.room,
    )
    by_id = {s.id: s for s in subject.sessions}
    if plan.exception_conflicts and not force:
        conflicts = sorted((by_id[i] for i in plan.exception_conflicts), key=lambda s: s.date)
        raise ApiError(
            409,
            "conflict",
            "Một số buổi đã huỷ hoặc đã sửa riêng sẽ bị xoá vì nằm ngoài lịch mới",
            details={"sessions": [{"id": s.id, "date": s.date.isoformat()} for s in conflicts]},
        )

    removed = plan.to_delete + (plan.exception_conflicts if force else [])
    auto_deadlines.drop_for_sessions(removed)
    for session_id in removed:
        db.session.delete(by_id[session_id])
    for update in plan.to_update:
        session = by_id[update.id]
        if update.start_at is not None:
            session.start_at, session.end_at = update.start_at, update.end_at
        if update.room is not None or update.clear_room:
            session.room = update.room
    created = []
    for d in plan.to_create:
        session = ClassSession(
            subject=subject,
            date=d,
            start_at=combine(d, subject.start_time),
            end_at=combine(d, subject.end_time),
            room=subject.room,
        )
        db.session.add(session)
        created.append(session)
    db.session.flush()
    return created


def find_time_conflicts(subject: Subject) -> list[dict]:
    """Cảnh báo (không chặn) khi buổi của môn trùng giờ với buổi học khác (FR-015)."""
    mine = [s for s in subject.sessions if not s.is_cancelled]
    if not mine:
        return []
    others = db.session.scalars(
        select(ClassSession).where(
            ClassSession.subject_id != subject.id,
            ClassSession.is_cancelled.is_(False),
            ClassSession.date.in_({s.date for s in mine}),
        )
    ).all()
    clashes = []
    for s in mine:
        for o in others:
            if o.date == s.date and o.start_at < s.end_at and s.start_at < o.end_at:
                clashes.append((s.date, o.subject.name))
    if not clashes:
        return []
    clashes.sort()
    listed = ", ".join(f"“{name}” ngày {_fmt(d)}" for d, name in clashes[:MAX_CONFLICTS_LISTED])
    more = len(clashes) - MAX_CONFLICTS_LISTED
    suffix = f" và {more} buổi khác" if more > 0 else ""
    return [
        {"code": "time_conflict", "message": f"“{subject.name}” trùng giờ với {listed}{suffix}"}
    ]


def _warnings(subject: Subject) -> list[dict]:
    if not subject.sessions:
        return [
            {
                "code": "no_sessions",
                "message": f"“{subject.name}”: khoảng ngày đã chọn không có thứ nào "
                "trùng lịch học, chưa có buổi học nào được tạo",
            }
        ]
    return find_time_conflicts(subject)


# ---- Ghi dữ liệu ------------------------------------------------------------------------------


def _insert(resolved: Resolved) -> Subject:
    subject = Subject(**resolved.values)
    db.session.add(subject)
    db.session.flush()
    replace_tag_links(SubjectTag, "subject_id", subject.id, resolved.tag_ids)
    regenerate_sessions(subject)
    db.session.refresh(subject)
    return subject


def create_subject(data: dict) -> tuple[Subject, list[dict]]:
    semester = resolve_semester(data.get("semester_id"))
    try:
        start, end = resolve_dates(semester, data.get("start_date"), data.get("end_date"))
        resolved = resolve_subject(data, semester, start, end, _used_colors())
    except FieldErrors as e:
        _raise_fields(e.fields)
    subject = _insert(resolved)
    auto_deadlines.reconcile(subject_ids=[subject.id])
    warnings = _warnings(subject)
    bump_revision(db.session)
    db.session.commit()
    return subject, warnings


def create_bulk(data: dict) -> tuple[list[Subject], list[dict]]:
    """Nhập nhiều môn trong một transaction: dòng nào lỗi thì không lưu môn nào (FR-009, FR-010)."""
    semester = resolve_semester(data.get("semester_id"))
    try:
        start, end = resolve_dates(semester, data.get("start_date"), data.get("end_date"))
    except FieldErrors as e:
        _raise_fields(e.fields)

    errors: dict[str, str] = {}
    resolved_rows: list[Resolved] = []
    used = _used_colors()
    for i, row in enumerate(data["rows"]):
        try:
            resolved = resolve_subject(row, semester, start, end, used, prefix=f"rows[{i}].")
        except FieldErrors as e:
            errors.update(e.fields)
            continue
        used.append(resolved.values["color"])
        resolved_rows.append(resolved)
    if errors:
        _raise_fields(errors)

    subjects = [_insert(r) for r in resolved_rows]
    auto_deadlines.reconcile(subject_ids=[s.id for s in subjects])
    warnings = [w for s in subjects for w in _warnings(s)]
    bump_revision(db.session)
    db.session.commit()
    return subjects, warnings


def get_subject(subject_id: int) -> Subject:
    subject = db.session.get(Subject, subject_id)
    if subject is None:
        raise not_found("Không tìm thấy môn học")
    return subject


def list_subjects(semester_id: int | None) -> list[Subject]:
    query = select(Subject).order_by(Subject.name)
    if semester_id is not None:
        query = query.where(Subject.semester_id == semester_id)
    return list(db.session.scalars(query))


def update_subject(subject_id: int, changes: dict, confirm: bool) -> tuple[Subject, list[dict]]:
    """Sửa thông tin chung; buổi đã huỷ/sửa riêng được giữ nguyên (FR-013)."""
    subject = get_subject(subject_id)
    current = {
        "name": subject.name,
        "class_code": subject.class_code,
        "lecturer": subject.lecturer,
        "room": subject.room,
        "weekdays": list(subject.weekdays),
        "color": subject.color,
        "reminder_minutes": subject.reminder_minutes,
        "tag_ids": [t.id for t in subject.tags],
        "start_date": subject.start_date,
        "end_date": subject.end_date,
    }
    if subject.start_shift_id:
        current["shift"] = {
            "start_shift_id": subject.start_shift_id,
            "end_shift_id": subject.end_shift_id,
        }
    else:
        current["start_time"], current["end_time"] = subject.start_time, subject.end_time
    # Gửi giờ tuỳ chỉnh thì bỏ ca cũ, và ngược lại.
    if "start_time" in changes or "end_time" in changes:
        current.pop("shift", None)
        current.setdefault("start_time", subject.start_time)
        current.setdefault("end_time", subject.end_time)
    if changes.get("shift"):
        current.pop("start_time", None)
        current.pop("end_time", None)
    merged = {**current, **changes}

    for field in ("name", "weekdays"):
        if merged.get(field) is None:
            _raise_fields({field: "Trường này là bắt buộc"})
    try:
        start, end = resolve_dates(subject.semester, merged["start_date"], merged["end_date"])
        resolved = resolve_subject(merged, subject.semester, start, end, _used_colors())
    except FieldErrors as e:
        _raise_fields(e.fields)

    for field, value in resolved.values.items():
        setattr(subject, field, value)
    if "tag_ids" in changes:
        replace_tag_links(SubjectTag, "subject_id", subject.id, resolved.tag_ids)
    db.session.flush()
    regenerate_sessions(subject, force=confirm)
    auto_deadlines.reconcile(subject_ids=[subject.id])
    warnings = _warnings(subject)
    bump_revision(db.session)
    db.session.commit()
    return subject, warnings


def delete_subject(subject_id: int) -> None:
    auto_deadlines.drop_for_subjects([subject_id])
    db.session.delete(get_subject(subject_id))
    bump_revision(db.session)
    db.session.commit()
