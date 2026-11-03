"""Khởi tạo toàn bộ bảng và dữ liệu mặc định (data-model.md, task T027).

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _id():
    return sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True)


def _timestamps():
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def _single_row_id():
    return sa.Column("id", sa.SmallInteger(), primary_key=True, server_default=sa.text("1"))


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "semesters",
        _id(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 100", name="ck_semesters_name_length"),
        sa.CheckConstraint("end_date >= start_date", name="ck_semesters_dates"),
    )
    # Các học kỳ không được chồng lấn ngày (FR-036).
    op.execute(
        "ALTER TABLE semesters ADD CONSTRAINT ex_semesters_no_overlap "
        "EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)"
    )

    op.create_table(
        "shifts",
        _id(),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False, unique=True),
        *_timestamps(),
        sa.CheckConstraint("end_time > start_time", name="ck_shifts_times"),
    )

    op.create_table(
        "subjects",
        _id(),
        sa.Column(
            "semester_id",
            sa.BigInteger(),
            sa.ForeignKey("semesters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("class_code", sa.Text()),
        sa.Column("lecturer", sa.Text()),
        sa.Column("room", sa.Text()),
        sa.Column("color", sa.Text(), nullable=False),
        sa.Column("weekdays", postgresql.ARRAY(sa.SmallInteger()), nullable=False),
        sa.Column(
            "start_shift_id", sa.BigInteger(), sa.ForeignKey("shifts.id", ondelete="SET NULL")
        ),
        sa.Column("end_shift_id", sa.BigInteger(), sa.ForeignKey("shifts.id", ondelete="SET NULL")),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reminder_minutes", sa.Integer()),
        *_timestamps(),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_subjects_name_length"),
        sa.CheckConstraint(
            "cardinality(weekdays) >= 1 AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]",
            name="ck_subjects_weekdays",
        ),
        sa.CheckConstraint(
            "(start_shift_id IS NULL) = (end_shift_id IS NULL)", name="ck_subjects_shift_pair"
        ),
        sa.CheckConstraint("end_time > start_time", name="ck_subjects_times"),
        sa.CheckConstraint("end_date >= start_date", name="ck_subjects_dates"),
        sa.CheckConstraint(
            "reminder_minutes IS NULL OR reminder_minutes >= -1", name="ck_subjects_reminder"
        ),
    )
    op.create_index("ix_subjects_semester_id", "subjects", ["semester_id"])

    op.create_table(
        "class_sessions",
        _id(),
        sa.Column(
            "subject_id",
            sa.BigInteger(),
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("room", sa.Text()),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("time_overridden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("room_overridden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_task_suppressed", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
        sa.CheckConstraint("end_at > start_at", name="ck_class_sessions_times"),
        sa.UniqueConstraint("subject_id", "date", "start_at", name="uq_class_sessions_slot"),
    )
    op.create_index("ix_class_sessions_subject_id", "class_sessions", ["subject_id"])
    op.create_index("ix_class_sessions_date", "class_sessions", ["date"])
    op.create_index("ix_class_sessions_start_at", "class_sessions", ["start_at"])

    op.create_table(
        "task_lists",
        _id(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("color", sa.Text(), nullable=False),
        sa.Column("is_default_study", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    op.create_index("uq_task_lists_name_ci", "task_lists", [sa.text("lower(name)")], unique=True)
    op.create_index(
        "uq_task_lists_default_study",
        "task_lists",
        ["is_default_study"],
        unique=True,
        postgresql_where=sa.text("is_default_study"),
    )

    op.create_table(
        "tasks",
        _id(),
        sa.Column("list_id", sa.BigInteger(), sa.ForeignKey("task_lists.id"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("due_date", sa.Date()),
        sa.Column("due_time", sa.Time()),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default=sa.text("2")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("reminder_minutes", sa.Integer()),
        sa.Column(
            "source_session_id",
            sa.BigInteger(),
            sa.ForeignKey("class_sessions.id", ondelete="SET NULL"),
            unique=True,
        ),
        sa.Column("is_auto", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("user_modified", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
        sa.CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 300", name="ck_tasks_title_length"
        ),
        sa.CheckConstraint("due_time IS NULL OR due_date IS NOT NULL", name="ck_tasks_due_time"),
        sa.CheckConstraint("priority IN (1, 2, 3)", name="ck_tasks_priority"),
        sa.CheckConstraint(
            "reminder_minutes IS NULL OR reminder_minutes >= -1", name="ck_tasks_reminder"
        ),
    )
    op.create_index("ix_tasks_list_id", "tasks", ["list_id"])
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])

    op.create_table(
        "tags",
        _id(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("color", sa.Text(), nullable=False),
        sa.Column("system_key", sa.Text(), unique=True),
        *_timestamps(),
    )
    op.create_index("uq_tags_name_ci", "tags", [sa.text("lower(name)")], unique=True)

    for table, owner_col, owner_table in [
        ("subject_tags", "subject_id", "subjects"),
        ("session_tags", "session_id", "class_sessions"),
        ("task_tags", "task_id", "tasks"),
    ]:
        op.create_table(
            table,
            sa.Column(
                owner_col,
                sa.BigInteger(),
                sa.ForeignKey(f"{owner_table}.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "tag_id",
                sa.BigInteger(),
                sa.ForeignKey("tags.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("position", sa.SmallInteger(), nullable=False),
        )

    op.create_table(
        "settings",
        _single_row_id(),
        sa.Column(
            "session_reminder_minutes", sa.Integer(), nullable=False, server_default=sa.text("15")
        ),
        sa.Column(
            "task_reminder_minutes", sa.Integer(), nullable=False, server_default=sa.text("60")
        ),
        sa.Column(
            "date_only_task_reminder_time",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'08:00'"),
        ),
        sa.Column("calendar_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "calendar_sync_prompted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "auto_deadline_evening_from",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'20:00'"),
        ),
        sa.Column(
            "auto_deadline_due_time", sa.Time(), nullable=False, server_default=sa.text("'08:00'")
        ),
        sa.Column(
            "auto_deadline_excluded_keywords",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY['Giáo dục thể chất']::text[]"),
        ),
        sa.CheckConstraint("id = 1", name="ck_settings_single_row"),
    )
    op.create_table(
        "sync_state",
        _single_row_id(),
        sa.Column("revision", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.CheckConstraint("id = 1", name="ck_sync_state_single_row"),
    )
    op.create_table(
        "agent_status",
        _single_row_id(),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("permission", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("icloud_source", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column(
            "last_synced_revision", sa.BigInteger(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("last_error", sa.Text()),
        sa.CheckConstraint("id = 1", name="ck_agent_status_single_row"),
    )

    _seed()


def _seed():
    """Dữ liệu mặc định: 4 ca, 3 danh sách, nhãn hệ thống E-Learning, các dòng cài đặt."""
    op.execute(
        """
        INSERT INTO shifts (name, start_time, end_time, position) VALUES
            ('Ca 1', '06:45', '09:25', 1),
            ('Ca 2', '09:35', '12:10', 2),
            ('Ca 3', '13:00', '15:40', 3),
            ('Ca 4', '15:45', '18:25', 4)
        """
    )
    op.execute(
        """
        INSERT INTO task_lists (name, color, is_default_study) VALUES
            ('Học tập', 'c01', true),
            ('Cá nhân', 'c02', false),
            ('Công việc', 'c03', false)
        """
    )
    op.execute(
        "INSERT INTO tags (name, color, system_key) VALUES ('E-Learning', 'c05', 'e_learning')"
    )
    op.execute("INSERT INTO settings (id) VALUES (1)")
    op.execute("INSERT INTO sync_state (id) VALUES (1)")
    op.execute("INSERT INTO agent_status (id) VALUES (1)")


def downgrade():
    for table in [
        "agent_status",
        "sync_state",
        "settings",
        "task_tags",
        "session_tags",
        "subject_tags",
        "tags",
        "tasks",
        "task_lists",
        "class_sessions",
        "subjects",
        "shifts",
        "semesters",
    ]:
        op.drop_table(table)
