"""Tìm kiếm không phân biệt dấu và hoa thường (feature 003 US5, FR-036 đến FR-043, research R15).

Một truy vấn cho mỗi nhóm; mọi từ khoá phải xuất hiện (ở bất kỳ vị trí nào) trong các trường được
tìm của cùng một mục. So khớp dùng hàm SQL `vn_fold` nên "nop bai" tìm được "Nộp bài".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import ColumnElement, Select, and_, case, func, select

from app.api.errors import ApiError
from app.extensions import db
from app.lib import timeutil
from app.lib.text import fold_key, fold_with_map
from app.lib.timeutil import iso
from app.models import Attachment, ClassSession, Exam, Subject, Tag, Task, TaskList, TaskTag
from app.schemas.tasks import serialize_task
from app.services.tasks import active_tasks

GROUPS = ("tasks", "lists", "tags", "subjects", "sessions", "exams", "files")
DEFAULT_LIMIT = 20
MAX_LIMIT = 200
SNIPPET_BEFORE, SNIPPET_AFTER = 30, 50


def _words(query: str) -> list[str]:
    return fold_key(query).split()


def _like(words: list[str], *columns) -> ColumnElement[bool]:
    """Mọi từ đều có trong chuỗi ghép của các cột (`%` và `_` trong từ khoá là ký tự thường)."""
    haystack = func.vn_fold(func.concat_ws(" ", *columns))
    clauses = []
    for word in words:
        escaped = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses.append(haystack.like(f"%{escaped}%", escape="\\"))
    return and_(*clauses)


@dataclass
class Page:
    total: int
    items: list


def _page(query: Select, limit: int) -> Page:
    total = db.session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    return Page(total or 0, list(db.session.execute(query.limit(limit))))


def _snippet(notes: str, words: list[str]) -> str:
    """Đoạn ghi chú quanh chỗ khớp đầu tiên (~80 ký tự), có dấu … ở phía bị cắt."""
    folded, positions = fold_with_map(notes)
    hits = [i for w in words if (i := folded.find(w)) >= 0]
    centre = positions[min(hits)] if hits else 0
    start = max(0, centre - SNIPPET_BEFORE)
    end = min(len(notes), centre + SNIPPET_AFTER)
    text = " ".join(notes[start:end].split())
    return ("…" if start > 0 else "") + text + ("…" if end < len(notes) else "")


def _tasks(words: list[str], include_done: bool, today: date, limit: int, now: datetime):
    query = active_tasks().where(_like(words, Task.title, Task.notes))
    if not include_done:
        query = query.where(Task.completed_at.is_(None))
    upcoming = case((Task.due_date >= today, Task.due_date))
    past = case((Task.due_date < today, Task.due_date))
    query = query.order_by(
        upcoming.asc().nulls_last(), past.desc().nulls_last(), Task.due_time, Task.id
    )
    page = _page(query, limit)
    items = []
    for (task,) in page.items:
        in_title = all(w in fold_key(task.title) for w in words)
        notes = task.notes or ""
        items.append(
            {
                **serialize_task(task, now),
                "matched_field": "title" if in_title else "notes",
                "snippet": None if in_title or not notes else _snippet(notes, words),
            }
        )
    return Page(page.total, items)


def _open_task_count(link_clause) -> ColumnElement:
    return (
        select(func.count())
        .select_from(Task)
        .where(link_clause, Task.deleted_at.is_(None), Task.completed_at.is_(None))
        .scalar_subquery()
    )


def _lists(words: list[str], limit: int) -> Page:
    count = _open_task_count(Task.list_id == TaskList.id)
    query = select(TaskList, count).where(_like(words, TaskList.name)).order_by(TaskList.name)
    page = _page(query, limit)
    items = [
        {"id": l.id, "name": l.name, "emoji": l.emoji, "color": l.color, "open_count": n}
        for l, n in page.items  # noqa: E741
    ]
    return Page(page.total, items)


def _tags(words: list[str], limit: int) -> Page:
    count = _open_task_count(Task.id.in_(select(TaskTag.task_id).where(TaskTag.tag_id == Tag.id)))
    query = select(Tag, count).where(_like(words, Tag.name)).order_by(Tag.name)
    page = _page(query, limit)
    items = [{"id": t.id, "name": t.name, "color": t.color, "open_count": n} for t, n in page.items]
    return Page(page.total, items)


def _subjects(words: list[str], limit: int) -> Page:
    query = (
        select(Subject)
        .where(_like(words, Subject.name, Subject.class_code, Subject.lecturer))
        .order_by(Subject.name, Subject.id)
    )
    page = _page(query, limit)
    items = [
        {
            "id": s.id,
            "name": s.name,
            "class_code": s.class_code,
            "lecturer": s.lecturer,
            "color": s.color,
            "semester_id": s.semester_id,
        }
        for (s,) in page.items
    ]
    return Page(page.total, items)


def _upcoming_first(start_column, now: datetime):
    """Buổi sắp tới (gần nhất trước), rồi buổi đã qua (gần nhất trước)."""
    return (
        case((start_column >= now, start_column)).asc().nulls_last(),
        case((start_column < now, start_column)).desc().nulls_last(),
    )


def _sessions(words: list[str], limit: int, now: datetime) -> Page:
    query = (
        select(ClassSession)
        .join(Subject, ClassSession.subject_id == Subject.id)
        .where(_like(words, Subject.name, Subject.class_code, ClassSession.room))
        .order_by(*_upcoming_first(ClassSession.start_at, now), ClassSession.id)
    )
    page = _page(query, limit)
    items = [
        {
            "id": s.id,
            "subject": {"id": s.subject_id, "name": s.subject.name, "color": s.subject.color},
            "date": s.date.isoformat(),
            "start_at": iso(s.start_at),
            "end_at": iso(s.end_at),
            "room": s.room,
            "is_cancelled": s.is_cancelled,
        }
        for (s,) in page.items
    ]
    return Page(page.total, items)


def _exams(words: list[str], limit: int, now: datetime) -> Page:
    query = (
        select(Exam)
        .where(_like(words, Exam.course_name, Exam.course_code, Exam.room))
        .order_by(*_upcoming_first(Exam.start_at, now), Exam.id)
    )
    page = _page(query, limit)
    items = [
        {
            "id": e.id,
            "course_name": e.course_name,
            "course_code": e.course_code,
            "date": e.date.isoformat(),
            "start_at": iso(e.start_at),
            "end_at": iso(e.end_at),
            "room": e.room,
        }
        for (e,) in page.items
    ]
    return Page(page.total, items)


def _semester_of(attachment) -> int | None:
    """Học kỳ của môn/buổi học chứa file (để mở đúng trang Môn học)."""
    if attachment.subject_id is not None:
        return db.session.get(Subject, attachment.subject_id).semester_id
    if attachment.session_id is not None:
        return db.session.get(ClassSession, attachment.session_id).subject.semester_id
    return None


def _files(words: list[str], limit: int) -> Page:
    """Tên file đính kèm (không đọc nội dung file, FR-029); bỏ file của task trong Thùng rác."""
    from app.services import attachments as attachment_service  # import muộn

    query = (
        attachment_service.visible_query()
        .where(_like(words, Attachment.display_name))
        .order_by(Attachment.id.desc())
    )
    page = _page(query, limit)
    items = [
        {
            "id": a.id,
            "attachment_id": a.id,
            "name": a.display_name,
            "owner": {
                "type": attachment_service.owner_of(a)[0],
                "id": attachment_service.owner_of(a)[1],
                "title": attachment_service.owner_title(a),
                **({"semester_id": semester_id} if (semester_id := _semester_of(a)) else {}),
            },
        }
        for (a,) in page.items
    ]
    return Page(page.total, items)


def search(query: str, include_done: bool, group: str | None, limit: int) -> dict:
    if group is not None and group not in GROUPS:
        raise ApiError(
            400, "validation_error", "Tham số không hợp lệ", {"group": "Nhóm không hợp lệ"}
        )
    limit = max(1, min(limit, MAX_LIMIT))
    words = _words(query)
    now = timeutil.now()
    wanted = (group,) if group else GROUPS
    runners = {
        "tasks": lambda: _tasks(words, include_done, now.date(), limit, now),
        "lists": lambda: _lists(words, limit),
        "tags": lambda: _tags(words, limit),
        "subjects": lambda: _subjects(words, limit),
        "sessions": lambda: _sessions(words, limit, now),
        "exams": lambda: _exams(words, limit, now),
        "files": lambda: _files(words, limit),
    }
    groups = {}
    for name in GROUPS:
        page = runners[name]() if words and name in wanted else Page(0, [])
        groups[name] = {"total": page.total, "items": page.items}
    return {"query": " ".join(words), "groups": groups}
