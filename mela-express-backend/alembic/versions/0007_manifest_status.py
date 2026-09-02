"""Align manifest_status_enum with application ManifestStatus values.

Revision ID: 0007_manifest_status
Revises: 0006_classification_and_scan
"""
from alembic import op

revision = "0007_manifest_status"
down_revision = "0006_classification_and_scan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # init.sql may have created open/dispatched/received — add app values safely.
    for value in ("draft", "in_transit", "cancelled"):
        op.execute(
            f"""
            DO $$ BEGIN
                ALTER TYPE manifest_status_enum ADD VALUE IF NOT EXISTS '{value}';
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
            """
        )


def downgrade() -> None:
    pass
