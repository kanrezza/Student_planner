"""Lệnh quản trị: `flask seed-demo` tạo dữ liệu mẫu để đo hiệu năng và thử giao diện (T140)."""

import random
from datetime import date, time, timedelta

import click
from sqlalchemy import select

from app.extensions import db
from app.models import Semester, Tag, TaskList
from app.services import semesters, subjects, tags, tasks

DEMO_SEMESTER = "Học kỳ mẫu"
TASK_COUNT = 200
# (tên, thứ, ca/giờ, nhãn E-Learning)
DEMO_SUBJECTS = [
    ("Giải tích 1", [1, 4], {"start_time": time(6, 45), "end_time": time(9, 25)}, False),
    (
        "Lập trình hướng đối tượng",
        [2],
        {"start_time": time(13, 0), "end_time": time(15, 40)},
        False,
    ),
    ("Triết học Mác - Lênin", [3], {"start_time": time(20, 0), "end_time": time(21, 30)}, True),
    ("Cơ sở dữ liệu", [5], {"start_time": time(9, 35), "end_time": time(12, 10)}, False),
    ("Tiếng Anh 2", [2, 5], {"start_time": time(15, 45), "end_time": time(18, 25)}, True),
    ("Giáo dục thể chất 2", [3], {"start_time": time(20, 30), "end_time": time(22, 0)}, False),
]


def seed_demo(task_count: int = TASK_COUNT) -> dict:
    """1 học kỳ 15 tuần quanh hôm nay, 6 môn (2 E-Learning, 1 môn 20:30), `task_count` task."""
    if db.session.scalar(select(Semester).where(Semester.name == DEMO_SEMESTER)):
        raise click.ClickException(
            "Dữ liệu mẫu đã có (học kỳ “Học kỳ mẫu”). Xoá học kỳ đó rồi chạy lại."
        )
    today = date.today()
    start = today - timedelta(days=today.weekday() + 7 * 5)  # Thứ Hai, 5 tuần trước
    semester = semesters.create_semester(
        DEMO_SEMESTER, start, start + timedelta(weeks=15) - timedelta(days=1)
    )
    e_learning = db.session.scalars(select(Tag).where(Tag.system_key == "e_learning")).one()
    urgent = tags.create_tag("Gấp", "c07")
    made, _ = subjects.create_bulk(
        {
            "semester_id": semester.id,
            "rows": [
                {"name": n, "weekdays": d, "tag_ids": [e_learning.id] if e else [], **times}
                for n, d, times, e in DEMO_SUBJECTS
            ],
        }
    )
    lists = list(db.session.scalars(select(TaskList)))
    rng = random.Random(2026)  # cố định để mỗi lần chạy ra cùng dữ liệu
    for i in range(task_count):
        due = start + timedelta(days=rng.randrange(0, 105))
        tasks.create_task(
            {
                "title": f"Việc mẫu {i + 1}",
                "list_id": rng.choice(lists).id,
                "priority": rng.choice([1, 2, 3]),
                "due_date": due,
                "due_time": rng.choice([None, time(rng.randrange(7, 22), 0)]),
                "tag_ids": [urgent.id] if i % 10 == 0 else [],
            }
        )
    return {"subjects": len(made), "tasks": task_count}


@click.command("seed-demo")
@click.option("--tasks", "task_count", default=TASK_COUNT, show_default=True, help="Số task mẫu")
def seed_demo_command(task_count: int):
    """Tạo dữ liệu mẫu: học kỳ, 6 môn, 200 task và nhãn."""
    result = seed_demo(task_count)
    click.echo(f"Đã tạo {result['subjects']} môn và {result['tasks']} task mẫu.")


def register(app) -> None:
    app.cli.add_command(seed_demo_command)
