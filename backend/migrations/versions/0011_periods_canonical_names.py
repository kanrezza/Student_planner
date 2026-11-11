"""Bảng tiết và danh sách tên môn chuẩn (feature 004, data-model "Migration 0011").

Revision ID: 0011_periods_canonical_names
Revises: 0010_subject_schedules
Create Date: 2026-11-10

Seed bảng tiết từ các ca hiện có: ca thứ k (k ≤ 4, theo `position`) ứng với tiết 3k−2…3k, mỗi tiết
50 phút, nghỉ 5 phút (ca khác 160 phút thì chia đều, tiết cuối kết thúc đúng giờ ca); tiết 16–18
mặc định 21:05–21:20, 21:20–21:40, 21:40–22:00. Công thức giống
`app.services.periods.default_period_times` (chép lại ở đây để migration không phụ thuộc code ứng
dụng).
"""

from datetime import date, datetime, timedelta

import sqlalchemy as sa
from alembic import op

revision = "0011_periods_canonical_names"
down_revision = "0010_subject_schedules"
branch_labels = None
depends_on = None

PERIODS_PER_SHIFT = 3
BREAK_MINUTES = 5
MIN_PERIOD_MINUTES = 10
EVENING = [(16, "21:05", "21:20"), (17, "21:20", "21:40"), (18, "21:40", "22:00")]


def _shift_periods(start, end):
    total = (datetime.combine(date.min, end) - datetime.combine(date.min, start)) // timedelta(
        minutes=1
    )
    each = (total - (PERIODS_PER_SHIFT - 1) * BREAK_MINUTES) // PERIODS_PER_SHIFT
    if each < MIN_PERIOD_MINUTES:
        return []
    result, cursor = [], datetime.combine(date.min, start)
    for index in range(PERIODS_PER_SHIFT):
        last = index == PERIODS_PER_SHIFT - 1
        finish = datetime.combine(date.min, end) if last else cursor + timedelta(minutes=each)
        result.append((cursor.time(), finish.time()))
        cursor = finish + timedelta(minutes=BREAK_MINUTES)
    return result


def upgrade():
    op.create_table(
        "periods",
        sa.Column("number", sa.SmallInteger(), primary_key=True, autoincrement=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_manual", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("number BETWEEN 1 AND 30", name="ck_periods_number"),
        sa.CheckConstraint("end_time > start_time", name="ck_periods_times"),
    )
    op.create_table(
        "canonical_subject_names",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("course_code", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_canonical_names_length"),
    )
    op.create_index(
        "uq_canonical_names_lower", "canonical_subject_names", [sa.text("lower(name)")], unique=True
    )

    connection = op.get_bind()
    periods = connection.execute(sa.text("SELECT 1 FROM periods LIMIT 1")).first()
    if periods is None:
        shifts = connection.execute(
            sa.text("SELECT start_time, end_time FROM shifts ORDER BY position LIMIT 4")
        ).all()
        rows = []
        for index, (start, end) in enumerate(shifts):
            for offset, (first, last) in enumerate(_shift_periods(start, end)):
                rows.append((index * PERIODS_PER_SHIFT + offset + 1, first, last))
        for number, start_text, end_text in EVENING:
            rows.append((number, start_text, end_text))
        for number, first, last in rows:
            connection.execute(
                sa.text("INSERT INTO periods (number, start_time, end_time) VALUES (:n, :s, :e)"),
                {"n": number, "s": first, "e": last},
            )


def downgrade():
    op.drop_index("uq_canonical_names_lower", table_name="canonical_subject_names")
    op.drop_table("canonical_subject_names")
    op.drop_table("periods")
