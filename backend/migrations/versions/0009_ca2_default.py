"""Giờ mặc định của Ca 2 là 09:30–12:10 (khớp cổng sinh viên); trước đây là 09:35.

Revision ID: 0009_ca2_default
Revises: 0008_recurring_tasks
Create Date: 2026-11-10

Chỉ đổi khi Ca 2 còn đúng giá trị mặc định cũ (09:35–12:10) và chưa môn nào dùng: ca đang được dùng
phải đổi qua màn hình Cài đặt để các môn, buổi học và deadline tự động cập nhật theo (FR-040).
"""

from alembic import op

revision = "0009_ca2_default"
down_revision = "0008_recurring_tasks"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE shifts SET start_time = '09:30'
        WHERE name = 'Ca 2' AND start_time = '09:35' AND end_time = '12:10'
          AND NOT EXISTS (
              SELECT 1 FROM subjects WHERE start_shift_id = shifts.id OR end_shift_id = shifts.id
          )
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE shifts SET start_time = '09:35'
        WHERE name = 'Ca 2' AND start_time = '09:30' AND end_time = '12:10'
          AND NOT EXISTS (
              SELECT 1 FROM subjects WHERE start_shift_id = shifts.id OR end_shift_id = shifts.id
          )
        """
    )
