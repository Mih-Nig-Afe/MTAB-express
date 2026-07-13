"""Add proof_of_delivery table.

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-01 01:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TODO: implement proof_of_delivery table creation (Task 2.3)
    pass


def downgrade() -> None:
    # TODO: implement rollback (Task 2.3)
    pass
