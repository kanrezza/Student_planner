"""Tìm kiếm không dấu: extension unaccent và hàm vn_fold (feature 003 US5, research R15).

`vn_fold(text)` gập chữ về không dấu, chữ thường (kể cả đ/Đ → d) và là IMMUTABLE nên dùng được trong
biểu thức truy vấn; kết quả khớp `foldVi` ở frontend.

Revision ID: 0007_search
Revises: 0006_backup
Create Date: 2026-11-06
"""

from alembic import op

revision = "0007_search"
down_revision = "0006_backup"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION vn_fold(text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
        $$ SELECT lower(public.unaccent('public.unaccent', coalesce($1, ''))) $$
        """
    )


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS vn_fold(text)")  # giữ lại extension (có thể nơi khác dùng)
