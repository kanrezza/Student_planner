"""Nhập lịch học và lịch thi từ ảnh (FR-028 đến FR-035, FR-059 đến FR-062).

`recognize` không ghi gì vào database; `commit` lưu tất cả trong một transaction duy nhất.
"""

from datetime import date, time

from sqlalchemy import select

from app.api.errors import ApiError
from app.config import MAX_IMAGE_BYTES
from app.extensions import db
from app.lib import timeutil
from app.lib.text import ci_key
from app.lib.timeutil import TZ, combine
from app.models import ClassSession, Exam, Semester, Shift, Subject
from app.ocr import preprocess, reader
from app.ocr.preview import ExistingSession, PreviewContext, build_preview
from app.schemas.common import _parse_hhmm
from app.schemas.imports import CommitIn, FieldIn
from app.services import canonical_names
from app.services import exams as exam_service
from app.services import subjects as subject_service
from app.services.exams import duplicate_key, exam_key, is_duplicate
from app.services.revision import bump_revision

KINDS = ("week_schedule", "exam_table")


# ---- Nhận diện ----------------------------------------------------------------------------------


def build_context() -> PreviewContext:
    sessions = db.session.execute(
        select(ClassSession, Subject).join(Subject, ClassSession.subject_id == Subject.id)
    ).all()
    return PreviewContext(
        now=timeutil.now(),
        shifts=list(db.session.scalars(select(Shift).order_by(Shift.position))),
        semesters=list(db.session.scalars(select(Semester).order_by(Semester.start_date))),
        canonical_names=canonical_names.names(),
        subject_names=sorted(
            {s.name for _, s in sessions} | set(db.session.scalars(select(Subject.name)))
        ),
        sessions=[
            ExistingSession(c.id, s.name, s.class_code, c.date, c.start_at.astimezone(TZ).time())
            for c, s in sessions
        ],
        exams=[(exam_key(e), e.id) for e in db.session.scalars(select(Exam))],
    )


def recognize(data: bytes, kind: str | None) -> dict:
    """Ảnh → `ImportPreview`; ảnh chỉ nằm trong bộ nhớ, không ghi đĩa hay database (FR-035)."""
    if len(data) > MAX_IMAGE_BYTES:
        raise ApiError(413, "image_too_large", "Ảnh vượt quá 20 MB")
    if kind is not None and kind not in KINDS:
        raise ApiError(
            400,
            "validation_error",
            "Tham số không hợp lệ",
            {"kind": "Phải là week_schedule hoặc exam_table"},
        )
    image = preprocess.load_image(data)
    boxes = reader.read_boxes(image)
    return build_preview(boxes, image.size, build_context(), kind)


# ---- Lưu ----------------------------------------------------------------------------------------


def _value(fields: dict[str, FieldIn], name: str):
    return fields[name].value if name in fields else None


def _text(fields: dict[str, FieldIn], name: str) -> str | None:
    value = _value(fields, name)
    value = str(value).strip() if value not in (None, "") else None
    return value or None


def _required(fields, name, row_label, errors, parse=lambda v: v):
    """Giá trị bắt buộc và phải chắc chắn (FR-032); ghi lỗi `row_label.name` nếu thiếu/sai."""
    key = f"{row_label}.{name}"
    field = fields.get(name)
    if field is None or field.value in (None, ""):
        errors[key] = "Trường này là bắt buộc"
        return None
    if not field.certain:
        errors[key] = "Hãy kiểm tra và xác nhận giá trị này"
        return None
    try:
        return parse(field.value)
    except (ValueError, TypeError):
        errors[key] = "Giá trị không hợp lệ"
        return None


def _date(value) -> date:
    return date.fromisoformat(str(value))


def _fail(errors: dict[str, str]):
    raise ApiError(400, "validation_error", "Dữ liệu chưa hợp lệ", fields=errors)


def _session_exists(name: str, class_code: str | None, day: date, start: time) -> bool:
    """Đã có buổi học cùng tên (hoặc mã lớp), cùng ngày, cùng giờ bắt đầu (FR-034)."""
    start_at = combine(day, start)
    for session in db.session.scalars(
        select(ClassSession).where(ClassSession.date == day, ClassSession.start_at == start_at)
    ):
        subject = session.subject
        if ci_key(subject.name) == ci_key(name) or (
            class_code and subject.class_code and ci_key(subject.class_code) == ci_key(class_code)
        ):
            return True
    return False


def commit(payload: CommitIn) -> dict:
    if payload.kind == "exam_table":
        return _commit_exams(_prepare_exams(payload))
    # Ảnh tuần có thể kèm ô "Lịch thi: …" (buổi thi): kiểm tra hợp lệ trước khi ghi bất cứ thứ gì.
    exams = _prepare_exams(payload)
    result = _commit_week(payload)
    if exams:
        exam_result = _commit_exams(exams)
        result["created_exams"] = exam_result["created_exams"]
        result["skipped_duplicates"] += exam_result["skipped_duplicates"]
        result["warnings"] = result["warnings"] + exam_result["warnings"]
    return result


def _commit_week(payload: CommitIn) -> dict:
    errors: dict[str, str] = {}
    prepared = []  # (chỉ số dòng, dữ liệu môn, khoá trùng)
    for i, row in enumerate(payload.rows):
        if not row.selected:
            continue
        label = f"rows[{i}]"
        f = row.fields
        name = _required(f, "name", label, errors, lambda v: str(v).strip() or None)
        day = _required(f, "date", label, errors, _date)
        start = _required(f, "start_time", label, errors, _parse_hhmm)
        end = _required(f, "end_time", label, errors, _parse_hhmm)
        if row.semester_id is None:
            errors[f"{label}.semester_id"] = "Hãy chọn hoặc tạo học kỳ cho buổi này"
        if None in (name, day, start, end) or row.semester_id is None:
            continue
        rule = {"weekdays": [day.isoweekday()], "room": _text(f, "room"), "start_date": day}
        if row.shift is not None:
            rule["shift"] = row.shift.model_dump()
        else:
            rule["start_time"], rule["end_time"] = start, end
        weekly = row.repeat.mode == "weekly"
        rule["end_date"] = (row.repeat.until or day) if weekly else day
        item = {
            "name": name,
            "class_code": _text(f, "class_code"),
            "lecturer": _text(f, "lecturer"),
            "semester_id": row.semester_id,
            "schedules": [rule],
            "tag_ids": row.tag_ids,
        }
        if rule["end_date"] < day:
            errors[f"{label}.repeat"] = "Ngày kết thúc phải sau hoặc bằng ngày của buổi"
            continue
        prepared.append((i, item, (ci_key(name), day, start), row))
    if errors:
        _fail(errors)

    skipped = 0
    kept: list[dict] = []
    seen: set[tuple] = set()
    merged: dict[str, dict] = {}
    for _i, item, key, row in prepared:
        if key in seen or _session_exists(item["name"], item["class_code"], key[1], key[2]):
            skipped += 1
            continue
        seen.add(key)
        if row.merge_group and row.merge_accepted:
            group = merged.get(row.merge_group)
            if group is None:
                merged[row.merge_group] = item
                kept.append(item)
            else:  # gộp: một môn lặp hàng tuần từ ngày sớm nhất tới `until` xa nhất
                rule, other = group["schedules"][0], item["schedules"][0]
                rule["start_date"] = min(rule["start_date"], other["start_date"])
                rule["end_date"] = max(rule["end_date"], other["end_date"])
            continue
        kept.append(item)
    for item in merged.values():  # gộp luôn là lặp hàng tuần theo thứ của ngày sớm nhất
        rule = item["schedules"][0]
        rule["weekdays"] = [rule["start_date"].isoweekday()]

    subjects, warnings = subject_service.create_many(kept) if kept else ([], [])
    return {
        "created_subjects": len(subjects),
        "created_sessions": sum(len(s.sessions) for s in subjects),
        "skipped_duplicates": skipped,
        "warnings": warnings,
    }


def _prepare_exams(payload: CommitIn) -> list[dict]:
    """Kiểm tra và chuẩn hoá các dòng thi được chọn; sai thì báo lỗi 400 (chưa ghi gì)."""
    errors: dict[str, str] = {}
    prepared = []
    for i, row in enumerate(payload.exam_rows):
        if not row.selected:
            continue
        label = f"exam_rows[{i}]"
        f = row.fields
        name = _required(f, "course_name", label, errors, lambda v: str(v).strip() or None)
        day = _required(f, "date", label, errors, _date)
        start = _required(f, "start_time", label, errors, _parse_hhmm)
        end = _required(f, "end_time", label, errors, _parse_hhmm)
        if None in (name, day, start, end):
            continue
        if end <= start:
            errors[f"{label}.end_time"] = "Giờ kết thúc phải sau giờ bắt đầu"
            continue
        attempt = _value(f, "attempt")
        prepared.append(
            {
                "course_name": name,
                "course_code": _text(f, "course_code"),
                "attempt": int(attempt) if attempt not in (None, "") else 1,
                "date": day,
                "start_time": start,
                "end_time": end,
                "exam_format": _text(f, "exam_format"),
                "room": _text(f, "room"),
                "candidate_number": _text(f, "candidate_number"),
                "tag_ids": row.tag_ids,
            }
        )
    if errors:
        _fail(errors)
    return prepared


def _commit_exams(prepared: list[dict]) -> dict:
    skipped, created, keys = 0, [], []
    for data in prepared:
        key = duplicate_key(
            data["course_code"],
            data["course_name"],
            data["date"],
            data["start_time"],
            data["attempt"],
        )
        if any(is_duplicate(key, k) for k in keys) or exam_service.find_duplicate_exam(key):
            skipped += 1
            continue
        keys.append(key)
        created.append(exam_service.build_exam(data))
    bump_revision(db.session)
    db.session.commit()
    warnings = []
    for exam in created:
        warnings += exam_service._conflict_warnings(exam)[1]
    return {"created_exams": len(created), "skipped_duplicates": skipped, "warnings": warnings}
