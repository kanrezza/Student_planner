"""File đính kèm: dòng CSDL (mục đính kèm, nội dung) và dọn dẹp (feature 005).

Phần đĩa nằm ở `attachments_store`; module này giữ logic có CSDL.
"""

import logging

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.api.errors import ApiError, not_found
from app.extensions import db
from app.models import Attachment, AttachmentBlob, ClassSession, Exam, Settings, Subject, Task
from app.services import attachments_store as store
from app.services.revision import bump_revision

log = logging.getLogger(__name__)


def sweep_orphans() -> int:
    """Dọn file/thư mục tạm lạ trong volume; lỗi chỉ ghi log, không chặn việc khác."""
    try:
        known = set(db.session.scalars(select(AttachmentBlob.sha256)))
        return store.sweep(known)
    except Exception as error:  # noqa: BLE001 — dọn dẹp không được làm hỏng tiến trình chính
        log.warning("Bỏ qua dọn file đính kèm: %s", error)
        return 0


# ---- Gắn, đọc, đổi tên, xoá ------------------------------------------------------------

MIB = 1 << 20
OWNER_COLUMNS = {
    "task": "task_id",
    "subject": "subject_id",
    "session": "session_id",
    "exam": "exam_id",
}


def settings() -> Settings:
    return db.session.get(Settings, 1)


def max_bytes() -> int:
    return settings().attachment_max_mb * MIB


def _fail(status: int, code: str, message: str, fields: dict | None = None) -> ApiError:
    return ApiError(status, code, message, fields)


def owner_object(owner_type: str, owner_id: int):
    """Task (không ở Thùng rác), môn, buổi học hoặc buổi thi; không có → 400 `owner_not_found`."""
    model = {"task": Task, "subject": Subject, "session": ClassSession, "exam": Exam}.get(
        owner_type
    )
    if model is None:
        raise _fail(400, "validation_error", "Dữ liệu chưa hợp lệ", {"owner_type": "Không hợp lệ"})
    obj = db.session.get(model, owner_id)
    if obj is None or (owner_type == "task" and obj.deleted_at is not None):
        raise _fail(400, "owner_not_found", "Không tìm thấy nơi để đính kèm")
    return obj


def _owner_filter(owner_type: str, owner_id: int):
    return getattr(Attachment, OWNER_COLUMNS[owner_type]) == owner_id


def _upsert_blob(sha: str, size: int, mime: str, executable: bool) -> bool:
    """Chèn dòng nội dung (nếu chưa có) và khoá nó; trả True khi file còn trong kho.

    Khoá dòng blob để `collect_garbage` chạy chồng phải chờ; nếu file đã bị dọn mất giữa chừng thì
    báo False để người gọi ghi lại nội dung.
    """
    db.session.execute(
        pg_insert(AttachmentBlob)
        .values(sha256=sha, size=size, mime_type=mime, is_executable=executable)
        .on_conflict_do_nothing()
    )
    db.session.execute(
        select(AttachmentBlob.sha256).where(AttachmentBlob.sha256 == sha).with_for_update()
    ).one()
    return store.blob_path(sha).is_file()


def create_from_stream(owner_type: str, owner_id: int, filename: str, stream) -> Attachment:
    """Gắn một file vào một nơi. Mỗi file một transaction; lỗi không để lại file dở."""
    owner_object(owner_type, owner_id)
    name = store.clean_display_name(filename)
    for _attempt in range(2):
        sha, size, head = store.store_stream(stream, max_bytes())
        mime, executable = store.detect_mime(name, head), store.is_executable(name, head)
        if _upsert_blob(sha, size, mime, executable):
            break
        db.session.rollback()  # file vừa bị dọn chạy chồng: ghi lại từ đầu luồng (có thể tua lại)
        if not (hasattr(stream, "seek") and stream.seekable()):
            raise _fail(409, "conflict", "Vui lòng thử gắn lại file")
        stream.seek(0)
    else:
        raise _fail(409, "conflict", "Vui lòng thử gắn lại file")
    taken = db.session.scalars(
        select(Attachment.display_name).where(_owner_filter(owner_type, owner_id))
    ).all()
    attachment = Attachment(
        blob_sha256=sha,
        display_name=store.unique_display_name(name, taken),
        **{OWNER_COLUMNS[owner_type]: owner_id},
    )
    db.session.add(attachment)
    bump_revision(db.session)
    db.session.commit()
    return attachment


def visible_query():
    """Mục đính kèm đang hiển thị: bỏ mục của task trong Thùng rác."""
    return (
        select(Attachment)
        .outerjoin(Task, Attachment.task_id == Task.id)
        .where(Task.deleted_at.is_(None))
    )


def get(attachment_id: int) -> Attachment:
    attachment = db.session.scalar(visible_query().where(Attachment.id == attachment_id))
    if attachment is None:
        raise not_found("Không tìm thấy file đính kèm")
    return attachment


def list_for(owner_type: str, owner_id: int) -> list[Attachment]:
    owner_object(owner_type, owner_id)
    query = visible_query().where(_owner_filter(owner_type, owner_id)).order_by(Attachment.id)
    return list(db.session.scalars(query))


def rename(attachment_id: int, display_name: str) -> Attachment:
    attachment = get(attachment_id)
    name = store.clean_display_name(display_name)
    if not display_name.strip() or not name:
        raise _fail(
            400, "validation_error", "Dữ liệu chưa hợp lệ", {"display_name": "Không được để trống"}
        )
    owner_type, owner_id = owner_of(attachment)
    others = db.session.scalars(
        select(Attachment.display_name).where(
            _owner_filter(owner_type, owner_id), Attachment.id != attachment.id
        )
    ).all()
    attachment.display_name = store.unique_display_name(name, others)
    bump_revision(db.session)
    db.session.commit()
    return attachment


def owner_of(attachment: Attachment) -> tuple[str, int]:
    for owner_type, column in OWNER_COLUMNS.items():
        value = getattr(attachment, column)
        if value is not None:
            return owner_type, value
    raise ValueError("Mục đính kèm không có nơi gắn")


def owner_title(attachment: Attachment) -> str:
    owner_type, owner_id = owner_of(attachment)
    obj = db.session.get(
        {"task": Task, "subject": Subject, "session": ClassSession, "exam": Exam}[owner_type],
        owner_id,
    )
    if owner_type == "task":
        return obj.title
    if owner_type == "subject":
        return obj.name
    if owner_type == "exam":
        return obj.course_name
    return f"{obj.subject.name} · {obj.date:%d/%m/%Y}"


def delete(attachment_id: int) -> None:
    attachment = get(attachment_id)
    sha = attachment.blob_sha256
    db.session.delete(attachment)
    bump_revision(db.session)
    db.session.commit()
    collect_garbage([sha])


def collect_garbage(shas) -> int:
    """Xoá nội dung không còn mục đính kèm nào (kể cả của task trong Thùng rác), cả dòng lẫn file.

    Khoá dòng blob trong lúc kiểm tra để chạy chồng với upload cùng nội dung vẫn nhất quán. Lỗi xoá
    file chỉ ghi log: lượt quét sau sẽ dọn.
    """
    removed = 0
    for sha in set(shas):
        blob = db.session.scalar(
            select(AttachmentBlob).where(AttachmentBlob.sha256 == sha).with_for_update()
        )
        if blob is None:
            continue
        in_use = db.session.scalar(
            select(func.count()).select_from(Attachment).where(Attachment.blob_sha256 == sha)
        )
        if in_use:
            db.session.rollback()
            continue
        try:
            store.delete_blob(sha)
        except OSError as error:
            log.warning("Chưa xoá được file đính kèm %s: %s", sha[:8], error)
        db.session.delete(blob)
        db.session.commit()
        removed += 1
    return removed


def shas_for(model, ids) -> list[str]:
    """Nội dung được dùng bởi các mục đính kèm của những `ids` (lấy TRƯỚC khi xoá chủ)."""
    column = getattr(Attachment, OWNER_COLUMNS[model])
    ids = list(ids)
    if not ids:
        return []
    return list(db.session.scalars(select(Attachment.blob_sha256).where(column.in_(ids))))


def stats() -> dict:
    total = db.session.scalar(select(func.coalesce(func.sum(AttachmentBlob.size), 0)))
    blob_count = db.session.scalar(select(func.count()).select_from(AttachmentBlob))
    visible = visible_query().subquery()
    attachment_count = db.session.scalar(select(func.count()).select_from(visible))
    largest = list(
        db.session.scalars(
            visible_query()
            .join(AttachmentBlob, AttachmentBlob.sha256 == Attachment.blob_sha256)
            .order_by(AttachmentBlob.size.desc(), Attachment.id)
            .limit(10)
        )
    )
    cfg = settings()
    return {
        "total_bytes": int(total),
        "blob_count": blob_count,
        "attachment_count": attachment_count,
        "largest": largest,
        "max_file_mb": cfg.attachment_max_mb,
        "backup_warn_mb": cfg.backup_attachments_warn_mb,
    }


def _subject_scope(subject_ids: list[int]):
    """Mục đính kèm của các môn và của mọi buổi học thuộc các môn đó."""
    session_ids = select(ClassSession.id).where(ClassSession.subject_id.in_(subject_ids))
    return Attachment.subject_id.in_(subject_ids) | Attachment.session_id.in_(session_ids)


def count_for_subjects(subject_ids) -> int:
    """Số file sẽ mất khi xoá các môn này (gồm file của các buổi học của môn)."""
    ids = list(subject_ids)
    if not ids:
        return 0
    return db.session.scalar(
        select(func.count()).select_from(Attachment).where(_subject_scope(ids))
    )


def shas_for_subjects(subject_ids) -> list[str]:
    ids = list(subject_ids)
    if not ids:
        return []
    return list(db.session.scalars(select(Attachment.blob_sha256).where(_subject_scope(ids))))


def count_for_exam(exam_id: int) -> int:
    return db.session.scalar(
        select(func.count()).select_from(Attachment).where(Attachment.exam_id == exam_id)
    )


def move_session_files_to_subject(session_ids, subject_id: int) -> int:
    """Buổi học sắp bị xoá (sửa lịch môn): file của buổi chuyển sang môn học, không mất (FR-024)."""
    ids = list(session_ids)
    if not ids:
        return 0
    moved = db.session.execute(
        update(Attachment)
        .where(Attachment.session_id.in_(ids))
        .values(session_id=None, subject_id=subject_id)
    ).rowcount
    return moved or 0
