"""Initial schema — all core tables and enum types.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TODO: implement initial schema migration (Task 2.2)
    pass


def downgrade() -> None:
    # TODO: implement rollback (Task 2.2)
    pass
