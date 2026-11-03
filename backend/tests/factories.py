"""Tạo dữ liệu nhanh cho test, ghi thẳng qua model (không đi qua service)."""

from datetime import date, time

from sqlalchemy import select

from app.models import Semester, Subject, Tag, Task, TaskList


def study_list(session) -> TaskList:
    return session.scalars(select(TaskList).where(TaskList.is_default_study)).one()


def make_semester(
    session,
    name: str = "HK1 2026–2027",
    start: date = date(2026, 9, 7),
    end: date = date(2026, 12, 20),
) -> Semester:
    semester = Semester(name=name, start_date=start, end_date=end)
    session.add(semester)
    session.flush()
    return semester


def make_subject(session, semester: Semester | None = None, **fields) -> Subject:
    semester = semester or make_semester(session)
    values = {
        "name": "Giải tích 1",
        "color": "c01",
        "weekdays": [1],
        "start_time": time(6, 45),
        "end_time": time(9, 25),
        "start_date": semester.start_date,
        "end_date": semester.end_date,
    }
    values.update(fields)
    subject = Subject(semester_id=semester.id, **values)
    session.add(subject)
    session.flush()
    return subject


def make_task(session, title: str = "Nộp bài tập Toán", **fields) -> Task:
    values = {"list_id": study_list(session).id, "priority": 2}
    values.update(fields)
    task = Task(title=title, **values)
    session.add(task)
    session.flush()
    return task


def make_tag(session, name: str = "Gấp", color: str = "c07") -> Tag:
    tag = Tag(name=name, color=color)
    session.add(tag)
    session.flush()
    return tag
