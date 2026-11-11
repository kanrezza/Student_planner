"""Môn nhiều quy tắc lặp hằng tuần: bảng subject_schedules (feature 004, data-model "Migration
0010").

Revision ID: 0010_subject_schedules
Revises: 0009_ca2_default
Create Date: 2026-11-10

- Tạo `subject_schedules`; thêm `subjects.course_code`, `subjects.credits`,
`class_sessions.schedule_id`.
- Mỗi môn cũ thành đúng 1 quy tắc (`position = 0`) chép từ các cột lịch của môn; mọi buổi của môn
gắn
  `schedule_id` của quy tắc đó. Ngoại lệ của buổi (huỷ, sửa giờ/phòng, dời ngày) không đổi.
- Xoá các cột lịch và CHECK cũ khỏi `subjects`.

`downgrade` chép ngược từ quy tắc có `position` nhỏ nhất của mỗi môn: các quy tắc còn lại của môn có
nhiều quy tắc bị mất (môn cũ chỉ có một quy tắc).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_subject_schedules"
down_revision = "0009_ca2_default"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "subject_schedules",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "subject_id",
            sa.BigInteger(),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("weekdays", postgresql.ARRAY(sa.SmallInteger()), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "start_shift_id", sa.BigInteger(), sa.ForeignKey("shifts.id", ondelete="SET NULL")
        ),
        sa.Column("end_shift_id", sa.BigInteger(), sa.ForeignKey("shifts.id", ondelete="SET NULL")),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("period_from", sa.SmallInteger()),
        sa.Column("period_to", sa.SmallInteger()),
        sa.Column("room", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("subject_id", "position", name="uq_subject_schedules_position"),
        sa.CheckConstraint("position >= 0", name="ck_subject_schedules_position"),
        sa.CheckConstraint(
            "cardinality(weekdays) >= 1 AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]",
            name="ck_subject_schedules_weekdays",
        ),
        sa.CheckConstraint("end_date >= start_date", name="ck_subject_schedules_dates"),
        sa.CheckConstraint("end_time > start_time", name="ck_subject_schedules_times"),
        sa.CheckConstraint(
            "(start_shift_id IS NULL) = (end_shift_id IS NULL)",
            name="ck_subject_schedules_shift_pair",
        ),
        sa.CheckConstraint(
            "(period_from IS NULL) = (period_to IS NULL) AND "
            "(period_from IS NULL OR (period_from >= 1 AND period_from <= period_to "
            "AND period_to <= 30))",
            name="ck_subject_schedules_periods",
        ),
    )
    op.create_index("ix_subject_schedules_subject_id", "subject_schedules", ["subject_id"])

    op.add_column("subjects", sa.Column("course_code", sa.Text()))
    op.add_column("subjects", sa.Column("credits", sa.SmallInteger()))
    op.create_check_constraint(
        "ck_subjects_credits", "subjects", "credits IS NULL OR credits BETWEEN 0 AND 30"
    )
    op.add_column(
        "class_sessions",
        sa.Column(
            "schedule_id",
            sa.BigInteger(),
            sa.ForeignKey("subject_schedules.id", ondelete="SET NULL"),
        ),
    )
    op.create_index("ix_class_sessions_schedule_id", "class_sessions", ["schedule_id"])

    op.execute(
        """
        INSERT INTO subject_schedules
            (subject_id, position, weekdays, start_date, end_date, start_shift_id, end_shift_id,
             start_time, end_time, room)
        SELECT id, 0, weekdays, start_date, end_date, start_shift_id, end_shift_id,
               start_time, end_time, room
        FROM subjects
        """
    )
    op.execute(
        """
        UPDATE class_sessions cs SET schedule_id = ss.id
        FROM subject_schedules ss
        WHERE ss.subject_id = cs.subject_id AND ss.position = 0
        """
    )

    for name in ("ck_subjects_weekdays", "ck_subjects_shift_pair", "ck_subjects_times"):
        op.drop_constraint(name, "subjects", type_="check")
    op.drop_constraint("ck_subjects_dates", "subjects", type_="check")
    for column in (
        "weekdays",
        "start_shift_id",
        "end_shift_id",
        "start_time",
        "end_time",
        "start_date",
        "end_date",
        "room",
    ):
        op.drop_column("subjects", column)


def downgrade():
    op.add_column("subjects", sa.Column("room", sa.Text()))
    op.add_column("subjects", sa.Column("weekdays", postgresql.ARRAY(sa.SmallInteger())))
    op.add_column(
        "subjects",
        sa.Column(
            "start_shift_id", sa.BigInteger(), sa.ForeignKey("shifts.id", ondelete="SET NULL")
        ),
    )
    op.add_column(
        "subjects",
        sa.Column("end_shift_id", sa.BigInteger(), sa.ForeignKey("shifts.id", ondelete="SET NULL")),
    )
    op.add_column("subjects", sa.Column("start_time", sa.Time()))
    op.add_column("subjects", sa.Column("end_time", sa.Time()))
    op.add_column("subjects", sa.Column("start_date", sa.Date()))
    op.add_column("subjects", sa.Column("end_date", sa.Date()))
    op.execute(
        """
        UPDATE subjects s SET weekdays = ss.weekdays, start_date = ss.start_date,
            end_date = ss.end_date, start_shift_id = ss.start_shift_id,
            end_shift_id = ss.end_shift_id, start_time = ss.start_time, end_time = ss.end_time,
            room = ss.room
        FROM (
            SELECT DISTINCT ON (subject_id) * FROM subject_schedules ORDER BY subject_id, position
        ) ss
        WHERE ss.subject_id = s.id
        """
    )
    for column in ("weekdays", "start_time", "end_time", "start_date", "end_date"):
        op.alter_column("subjects", column, nullable=False)
    op.create_check_constraint(
        "ck_subjects_weekdays",
        "subjects",
        "cardinality(weekdays) >= 1 AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]",
    )
    op.create_check_constraint(
        "ck_subjects_shift_pair", "subjects", "(start_shift_id IS NULL) = (end_shift_id IS NULL)"
    )
    op.create_check_constraint("ck_subjects_times", "subjects", "end_time > start_time")
    op.create_check_constraint("ck_subjects_dates", "subjects", "end_date >= start_date")

    op.drop_index("ix_class_sessions_schedule_id", table_name="class_sessions")
    op.drop_column("class_sessions", "schedule_id")
    op.drop_constraint("ck_subjects_credits", "subjects", type_="check")
    op.drop_column("subjects", "credits")
    op.drop_column("subjects", "course_code")
    op.drop_index("ix_subject_schedules_subject_id", table_name="subject_schedules")
    op.drop_table("subject_schedules")
