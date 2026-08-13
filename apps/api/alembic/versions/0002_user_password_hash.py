"""Add password_hash to users for local registration auth."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_user_password_hash"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
