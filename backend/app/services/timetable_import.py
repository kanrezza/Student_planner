"""Nhập học kỳ từ PDF thời khoá biểu: xem trước (không ghi gì) và lưu (một transaction).

Chỉ đọc trong bộ nhớ, không file tạm, không log nội dung file (R6, SC-006).
"""

from sqlalchemy import func, select

from app.api.errors import ApiError
from app.extensions import db
from app.models import ClassSession, Semester, Shift
from app.pdfimport.layout import parse_table
from app.pdfimport.preview import PreviewContext, build_timetable_preview
from app.pdfimport.reader import PdfImportError, read_pdf
from app.schemas.timetable_import import TimetableCommitIn
from app.services import periods as periods_service
from app.services import semesters as semester_service
from app.services import subjects as subject_service


def _context() -> PreviewContext:
    shifts = list(db.session.scalars(select(Shift).order_by(Shift.position)))
    return PreviewContext(
        shifts=shifts,
        periods=periods_service.load_periods(),
        semesters=semester_service.all_semesters(),
    )


def preview(data: bytes) -> dict:
    """Đọc PDF và trả bản xem trước; lỗi đọc đổi thành `ApiError` đúng mã của contract."""
    try:
        table = parse_table(read_pdf(data))
        return build_timetable_preview(table.rows, table.semester_line, _context())
    except PdfImportError as err:
        raise ApiError(err.status, err.code, err.message) from None


def _apply_semester(choice) -> Semester:
    """Dùng, mở rộng hoặc tạo học kỳ — chưa commit (cùng transaction với việc tạo môn)."""
    if choice.choice == "use":
        return semester_service.get_semester(choice.semester_id)
    if choice.choice == "extend":
        semester = semester_service.get_semester(choice.semester_id)
        start = min(semester.start_date, choice.start_date)
        end = max(semester.end_date, choice.end_date)
        semester_service._check_overlap(start, end, exclude_id=semester.id)
        semester.start_date, semester.end_date = start, end
        db.session.flush()
        return semester
    semester_service._check_overlap(choice.start_date, choice.end_date)
    semester = Semester(name=choice.name, start_date=choice.start_date, end_date=choice.end_date)
    db.session.add(semester)
    db.session.flush()
    return semester


def commit(payload: TimetableCommitIn) -> dict:
    """Lưu phần đã chọn. Lỗi ở bất kỳ môn/quy tắc nào → không lưu gì (FR-025)."""
    try:
        semester = _apply_semester(payload.semester)
        items = []
        for subject in payload.subjects:
            item = subject.model_dump(exclude={"existing_subject_id"})
            item["semester_id"] = semester.id
            item["schedules"] = [
                {k: v for k, v in rule.items() if k != "save_periods"} for rule in item["schedules"]
            ]
            items.append(item)
        created, warnings = subject_service.create_many(items, row_name="subjects")
        created_sessions = db.session.scalar(
            select(func.count())
            .select_from(ClassSession)
            .where(ClassSession.subject_id.in_([s.id for s in created]))
        )
    except Exception:
        db.session.rollback()
        raise
    return {
        "semester_id": semester.id,
        "created_subjects": len(created),
        "updated_subjects": 0,
        "created_sessions": created_sessions or 0,
        "updated_sessions": 0,
        "skipped_sessions": 0,
        "kept_exception_sessions": 0,
        "warnings": warnings,
    }
