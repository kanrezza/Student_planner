"""Tìm kiếm trên 1.000 task + một học kỳ đầy đủ phải dưới 0,3 giây mỗi truy vấn (SC-008)."""

import time
from datetime import date, timedelta

import pytest

from app.models import Task
from tests.factories import make_semester, study_list
from tests.integration.helpers import create_subject

QUERIES = [
    "nop bai", "bai tap", "do an", "toan", "ly thuyet", "quan tri", "giai tich", "tuan 12",
    "nop qtda", "on thi", "viet bao cao", "hoc nhom", "qtda", "xyz khong co", "5", "a",
    "tieu luan", "thay hung", "phong b2", "ghi chu",
]  # fmt: skip


@pytest.mark.slow
def test_20_truy_van_moi_truy_van_duoi_300ms(client, db_session):
    base = date(2026, 11, 1)
    list_ = study_list(db_session)
    for n in range(1000):
        db_session.add(
            Task(
                title=f"Nộp bài tập số {n} môn {['Toán', 'Lý thuyết', 'Đồ án'][n % 3]} tuần {n % 15}",
                notes="Ghi chú dài cho bài " + str(n) + " gửi thầy Hùng phòng B2 " * 3,
                list_id=list_.id,
                due_date=base + timedelta(days=n % 90),
            )
        )
    semester = make_semester(db_session)
    db_session.commit()
    for name in [
        "Quản trị dự án",
        "Giải tích 1",
        "Giải tích 2",
        "Lý thuyết đồ thị",
        "Vật lý 1",
        "Anh văn",
    ]:
        create_subject(
            client, semester.id, name=name, weekdays=[1, 3, 5], class_code=name[:3].upper()
        )

    slowest = 0.0
    for q in QUERIES:
        start = time.perf_counter()
        assert client.get("/api/search", query_string={"q": q}).status_code == 200
        slowest = max(slowest, time.perf_counter() - start)
    assert slowest < 0.3, f"truy vấn chậm nhất {slowest:.3f}s"
