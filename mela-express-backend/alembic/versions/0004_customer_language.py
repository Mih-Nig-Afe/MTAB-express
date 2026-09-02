"""add customers.language (preferred message language)

Revision ID: 0004_customer_language
Revises: 0003
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_customer_language"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("language", sa.String(length=5), nullable=True, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("customers", "language")
