"""Môn học và buổi học (FR-007 đến FR-015, FR-039).

Mọi kiểm tra trả lỗi theo tên trường; với nhập nhiều môn, tên trường có tiền tố `rows[i].`
để giao diện chỉ đúng ô lỗi (FR-010).
"""

import dataclasses
from dataclasses import dataclass
from datetime import date, time

from sqlalchemy import select

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.lib.timeutil import combine
from app.models import ClassSession, Shift, Subject, SubjectSchedule, SubjectTag
from app.services import auto_deadlines
from app.services import semesters as semester_service
from app.services.colors import is_palette_color, next_color
from app.services.recurrence import ExistingSession, desired_sessions, plan_sessions
from app.services.revision import bump_revision
from app.services.shifts import resolve_range
from app.services.tag_links import replace_tag_links

MAX_CONFLICTS_LISTED = 3
MAX_PERIOD = 30  # tiết lớn nhất (khớp CHECK của subject_schedules)


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
    """Giá trị đã kiểm tra, sẵn sàng ghi vào bảng `subjects` và `subject_schedules`."""

    values: dict
    schedules: list[dict]
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


def _schedule_items(data: dict, prefix: str) -> list[tuple[dict, str]]:
    """Các quy tắc thô của một môn kèm tiền tố tên trường lỗi.

    Có `schedules` thì mỗi phần tử là một quy tắc (lỗi `schedules[i].trường`); không có thì các
    trường lịch phẳng của môn (`weekdays`, `shift`, `start_time`…) là dạng rút gọn cho một quy tắc
    duy nhất.
    """
    if data.get("schedules") is not None:
        return [(item, f"{prefix}schedules[{i}].") for i, item in enumerate(data["schedules"])]
    return [(data, prefix)]


def resolve_schedule(item: dict, semester, default_dates: tuple[date | None, date | None], prefix):
    """Một quy tắc đã kiểm tra: thứ, khoảng ngày, giờ/ca, khoảng tiết, phòng."""
    errors: dict[str, str] = {}
    weekdays = item.get("weekdays")
    if not weekdays:
        errors[f"{prefix}weekdays"] = "Chọn ít nhất một thứ trong tuần"
    try:
        start_time, end_time, start_shift_id, end_shift_id = resolve_times(item, prefix)
    except FieldErrors as e:
        errors.update(e.fields)
    try:
        start_date, end_date = resolve_dates(
            semester,
            item.get("start_date") or default_dates[0],
            item.get("end_date") or default_dates[1],
            prefix,
        )
    except FieldErrors as e:
        errors.update(e.fields)
    first, last = item.get("period_from"), item.get("period_to")
    if (first is None) != (last is None) or (
        first is not None and not 1 <= first <= last <= MAX_PERIOD
    ):
        errors[f"{prefix}period_from"] = (
            f"Khoảng tiết phải từ 1 đến {MAX_PERIOD}, tiết đầu ≤ tiết cuối"
        )
    if errors:
        raise FieldErrors(errors)
    return {
        "id": item.get("id"),
        "weekdays": sorted(weekdays),
        "start_date": start_date,
        "end_date": end_date,
        "start_shift_id": start_shift_id,
        "end_shift_id": end_shift_id,
        "start_time": start_time,
        "end_time": end_time,
        "period_from": first,
        "period_to": last,
        "room": item.get("room"),
    }


def resolve_subject(
    data: dict,
    semester,
    default_dates: tuple[date | None, date | None],
    used_colors: list[str],
    prefix="",
) -> Resolved:
    errors: dict[str, str] = {}
    schedules = []
    items = _schedule_items(data, prefix)
    if not items:
        errors[f"{prefix}schedules"] = "Môn học cần có ít nhất một lịch học"
    for item, item_prefix in items:
        try:
            schedules.append(resolve_schedule(item, semester, default_dates, item_prefix))
        except FieldErrors as e:
            errors.update(e.fields)
    color = data.get("color") or next_color(used_colors)
    if not is_palette_color(color):
        errors[f"{prefix}color"] = "Màu không hợp lệ"
    if errors:
        raise FieldErrors(errors)
    values = {
        "semester_id": semester.id,
        "name": data["name"],
        "class_code": data.get("class_code"),
        "course_code": data.get("course_code"),
        "credits": data.get("credits"),
        "lecturer": data.get("lecturer"),
        "color": color,
        "reminder_minutes": data.get("reminder_minutes"),
        "is_important": bool(data.get("is_important")),
    }
    return Resolved(values, schedules, data.get("tag_ids") or [])


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
            original_date=s.original_date,
            schedule_id=s.schedule_id,
        )
        for s in subject.sessions
    ]


def regenerate_sessions(
    subject: Subject,
    force: bool = False,
    keep_before: date | None = None,
    keep_conflicts: bool = False,
) -> list[ClassSession]:
    """Đưa buổi học về khớp với các quy tắc lặp của môn.

    Buổi có ngoại lệ nằm ngoài lịch mới → 409, trừ khi `force` (khi đó các buổi này bị xoá) hoặc
    `keep_conflicts` (nhập PDF: giữ lại, tách khỏi quy tắc, người gọi lấy danh sách qua
    `subject.kept_exception_sessions`). `keep_before`: buổi trước ngày này không bị tạo/sửa/xoá.
    """
    desired, _ = desired_sessions(subject.schedules)
    plan = plan_sessions(_existing(subject), desired, keep_before)
    by_id = {s.id: s for s in subject.sessions}
    kept: list[ClassSession] = []
    if plan.exception_conflicts and keep_conflicts:
        kept = [by_id[i] for i in plan.exception_conflicts]
        for session in kept:
            session.schedule_id = None
        plan.exception_conflicts = []
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
        if update.set_schedule:
            session.schedule_id = update.schedule_id
    created = []
    for d in plan.to_create:
        want = desired[d]
        session = ClassSession(
            subject=subject,
            date=d,
            start_at=combine(d, want.start_time),
            end_at=combine(d, want.end_time),
            room=want.room,
            schedule_id=want.schedule_id,
        )
        db.session.add(session)
        created.append(session)
    db.session.flush()
    subject.kept_exception_sessions = kept  # type: ignore[attr-defined]
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
    warnings: list[dict] = []
    if not subject.sessions:
        warnings.append(
            {
                "code": "no_sessions",
                "message": f"“{subject.name}”: khoảng ngày đã chọn không có thứ nào "
                "trùng lịch học, chưa có buổi học nào được tạo",
            }
        )
    else:
        warnings.extend(find_time_conflicts(subject))
    _, overlaps = desired_sessions(subject.schedules)
    if overlaps:
        listed = ", ".join(_fmt(d) for d in overlaps[:MAX_CONFLICTS_LISTED])
        more = len(overlaps) - MAX_CONFLICTS_LISTED
        suffix = f" và {more} ngày khác" if more > 0 else ""
        warnings.append(
            {
                "code": "schedule_overlap",
                "message": f"“{subject.name}”: nhiều lịch học cùng rơi vào ngày {listed}{suffix}; "
                "chỉ lịch đứng trước được tạo buổi",
            }
        )
    return warnings


# ---- Ghi dữ liệu ------------------------------------------------------------------------------


def apply_schedules(subject: Subject, resolved: list[dict]) -> None:
    """Đồng bộ danh sách quy tắc: có `id` thì cập nhật, không có thì tạo, vắng mặt thì xoá."""
    by_id = {rule.id: rule for rule in subject.schedules}
    keep_ids = {item["id"] for item in resolved if item.get("id") in by_id}
    removed = [rule for rule in subject.schedules if rule.id not in keep_ids]
    for rule in removed:
        for session in subject.sessions:
            if session.schedule_id == rule.id:
                session.schedule_id = None
        subject.schedules.remove(rule)
    db.session.flush()
    # Hai bước để không đụng ràng buộc duy nhất (subject_id, position) khi đổi thứ tự.
    for index, rule in enumerate(subject.schedules):
        rule.position = 1000 + index
    db.session.flush()
    ordered: list[SubjectSchedule] = []
    for item in resolved:
        fields = {k: v for k, v in item.items() if k != "id"}
        rule = by_id.get(item.get("id"))
        if rule is None:
            rule = SubjectSchedule(**fields)
            subject.schedules.append(rule)
        else:
            for key, value in fields.items():
                setattr(rule, key, value)
        ordered.append(rule)
    for position, rule in enumerate(ordered):
        rule.position = position
    db.session.flush()


def _insert(resolved: Resolved) -> Subject:
    subject = Subject(**resolved.values)
    db.session.add(subject)
    db.session.flush()
    apply_schedules(subject, resolved.schedules)
    replace_tag_links(SubjectTag, "subject_id", subject.id, resolved.tag_ids)
    regenerate_sessions(subject)
    db.session.refresh(subject)
    return subject


def create_subject(data: dict) -> tuple[Subject, list[dict]]:
    semester = resolve_semester(data.get("semester_id"))
    try:
        resolved = resolve_subject(
            data,
            semester,
            (data.get("start_date"), data.get("end_date")),
            _used_colors(),
        )
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
        default_dates = resolve_dates(semester, data.get("start_date"), data.get("end_date"))
    except FieldErrors as e:
        _raise_fields(e.fields)

    errors: dict[str, str] = {}
    resolved_rows: list[Resolved] = []
    used = _used_colors()
    for i, row in enumerate(data["rows"]):
        try:
            resolved = resolve_subject(row, semester, default_dates, used, prefix=f"rows[{i}].")
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


LEGACY_SCHEDULE_FIELDS = ("weekdays", "shift", "start_time", "end_time", "start_date", "end_date")


def _schedule_as_input(rule: SubjectSchedule) -> dict:
    """Quy tắc đang lưu dưới dạng đầu vào (để PATCH dạng rút gọn chỉ ghi đè phần được gửi)."""
    item: dict = {
        "id": rule.id,
        "weekdays": list(rule.weekdays),
        "start_date": rule.start_date,
        "end_date": rule.end_date,
        "period_from": rule.period_from,
        "period_to": rule.period_to,
        "room": rule.room,
    }
    if rule.start_shift_id:
        item["shift"] = {
            "start_shift_id": rule.start_shift_id,
            "end_shift_id": rule.end_shift_id,
        }
    else:
        item["start_time"], item["end_time"] = rule.start_time, rule.end_time
    return item


def _patched_schedules(subject: Subject, changes: dict) -> list[dict]:
    """Danh sách quy tắc sau PATCH: `schedules` thay toàn bộ; các trường phẳng sửa quy tắc duy
    nhất."""
    if changes.get("schedules") is not None:
        return changes["schedules"]
    flat = {k: changes[k] for k in (*LEGACY_SCHEDULE_FIELDS, "room") if k in changes}
    current = [_schedule_as_input(rule) for rule in subject.schedules]
    if not flat:
        return current
    if len(current) != 1:
        _raise_fields({"schedules": "Môn có nhiều lịch học, hãy gửi danh sách schedules"})
    item = current[0]
    # Gửi giờ tuỳ chỉnh thì bỏ ca cũ, và ngược lại.
    if "start_time" in flat or "end_time" in flat:
        item.pop("shift", None)
        item.setdefault("start_time", subject.schedules[0].start_time)
        item.setdefault("end_time", subject.schedules[0].end_time)
    if flat.get("shift"):
        item.pop("start_time", None)
        item.pop("end_time", None)
    item.update(flat)
    if flat.get("shift") is None and "shift" in flat:
        item.pop("shift", None)
    if "period_from" not in flat and ("shift" in flat or "start_time" in flat):
        item["period_from"] = item["period_to"] = None  # giờ đổi tay thì khoảng tiết cũ hết đúng
    return [item]


def update_subject(subject_id: int, changes: dict, confirm: bool) -> tuple[Subject, list[dict]]:
    """Sửa thông tin chung và các quy tắc lặp; buổi đã huỷ/sửa riêng được giữ nguyên (FR-013)."""
    subject = get_subject(subject_id)
    current = {
        "name": subject.name,
        "class_code": subject.class_code,
        "course_code": subject.course_code,
        "credits": subject.credits,
        "lecturer": subject.lecturer,
        "color": subject.color,
        "reminder_minutes": subject.reminder_minutes,
        "is_important": subject.is_important,
        "tag_ids": [t.id for t in subject.tags],
    }
    merged = {**current, **{k: v for k, v in changes.items() if k in current}}
    if merged.get("name") is None:
        _raise_fields({"name": "Trường này là bắt buộc"})
    merged["schedules"] = _patched_schedules(subject, changes)
    try:
        resolved = resolve_subject(merged, subject.semester, (None, None), _used_colors())
    except FieldErrors as e:
        _raise_fields(e.fields)

    for field, value in resolved.values.items():
        setattr(subject, field, value)
    apply_schedules(subject, resolved.schedules)
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


def create_many(
    items: list[dict], row_name: str = "rows", index_map: list[int] | None = None
) -> tuple[list[Subject], list[dict]]:
    """Tạo nhiều môn trong MỘT transaction, mỗi môn có học kỳ và khoảng ngày riêng (nhập từ ảnh).

    Dòng nào lỗi thì không lưu môn nào; lỗi báo theo `rows[i].<trường>` (contracts/rest-api.md).
    """
    errors: dict[str, str] = {}
    resolved_rows: list[Resolved] = []
    used = _used_colors()
    for i, item in enumerate(items):
        prefix = f"{row_name}[{index_map[i] if index_map else i}]."
        try:
            semester = resolve_semester(item.get("semester_id"))
            resolved = resolve_subject(
                item,
                semester,
                (item.get("start_date"), item.get("end_date")),
                used,
                prefix=prefix,
            )
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


@dataclass
class ImportUpdate:
    """Kết quả cập nhật một môn đã có từ nhập PDF (chưa commit)."""

    subject: Subject
    created: int = 0
    updated: int = 0
    skipped: int = 0
    kept: list[ClassSession] = dataclasses.field(default_factory=list)


def update_from_import(
    subject: Subject, item: dict, keep_before: date, prefix: str = ""
) -> ImportUpdate:
    """Nhập lại PDF: thay toàn bộ quy tắc của môn đã có bằng quy tắc từ file (feature 004, R9).

    Buổi trước `keep_before` không bị sửa/xoá; buổi đã huỷ/sửa riêng giữ như cũ, buổi có ngoại lệ
    nằm ngoài lịch mới được giữ lại (tách khỏi quy tắc) thay vì hỏi xác nhận. Không commit.
    """
    tag_ids = list(dict.fromkeys([t.id for t in subject.tags] + list(item.get("tag_ids") or [])))
    merged = {
        "name": item["name"],
        "class_code": subject.class_code or item.get("class_code"),
        "course_code": item.get("course_code") or subject.course_code,
        "credits": item.get("credits") if item.get("credits") is not None else subject.credits,
        "lecturer": subject.lecturer,
        "color": subject.color,
        "reminder_minutes": subject.reminder_minutes,
        "is_important": subject.is_important,
        "tag_ids": tag_ids,
        "schedules": [{**rule, "id": None} for rule in item["schedules"]],
    }
    try:
        resolved = resolve_subject(merged, subject.semester, (None, None), _used_colors(), prefix)
    except FieldErrors as e:
        _raise_fields(e.fields)
    before = {s.id: (s.start_at, s.end_at, s.room) for s in subject.sessions}
    for key, value in resolved.values.items():
        setattr(subject, key, value)
    apply_schedules(subject, resolved.schedules)
    replace_tag_links(SubjectTag, "subject_id", subject.id, resolved.tag_ids)
    db.session.flush()
    created = regenerate_sessions(subject, keep_before=keep_before, keep_conflicts=True)
    result = ImportUpdate(subject, created=len(created), kept=subject.kept_exception_sessions)  # type: ignore[attr-defined]
    for session in subject.sessions:
        if session.id in before:
            same = before[session.id] == (session.start_at, session.end_at, session.room)
            result.skipped += same
            result.updated += not same
    return result
