"""Mốc nhắc tối hôm trước hạn cho task tự tạo (FR-071, task T160).

Revision ID: 0003_auto_deadline_reminder
Revises: 0002_important_digest
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_auto_deadline_reminder"
down_revision = "0002_important_digest"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "settings",
        sa.Column(
            "auto_deadline_eve_reminder_time",
            sa.Time(),
            nullable=True,
            server_default=sa.text("'20:00'"),
        ),
    )


def downgrade():
    op.drop_column("settings", "auto_deadline_eve_reminder_time")
