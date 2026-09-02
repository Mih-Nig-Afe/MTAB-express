"""Parcel classification, branch facility types, scan stations.

Revision ID: 0006_classification_and_scan
Revises: 0005_journey_tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_classification_and_scan"
down_revision = "0005_journey_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE content_category_enum AS ENUM
            ('documents', 'electronics', 'clothing', 'food', 'fragile', 'general');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE facility_type_enum AS ENUM ('branch', 'airport', 'sorting_hub');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.add_column(
        "branches",
        sa.Column(
            "facility_type",
            postgresql.ENUM("branch", "airport", "sorting_hub", name="facility_type_enum", create_type=False),
            nullable=False,
            server_default="branch",
        ),
    )

    op.add_column(
        "parcels",
        sa.Column(
            "size_category",
            postgresql.ENUM("small", "medium", "large", "oversized", name="size_category_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "parcels",
        sa.Column(
            "content_category",
            postgresql.ENUM(
                "documents", "electronics", "clothing", "food", "fragile", "general",
                name="content_category_enum", create_type=False,
            ),
            nullable=True,
            server_default="general",
        ),
    )
    op.add_column("parcels", sa.Column("length_cm", sa.Numeric(6, 1), nullable=True))
    op.add_column("parcels", sa.Column("width_cm", sa.Numeric(6, 1), nullable=True))
    op.add_column("parcels", sa.Column("height_cm", sa.Numeric(6, 1), nullable=True))
    op.add_column("parcels", sa.Column("volumetric_weight_kg", sa.Numeric(6, 2), nullable=True))
    op.add_column("parcels", sa.Column("chargeable_weight_kg", sa.Numeric(6, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("parcels", "chargeable_weight_kg")
    op.drop_column("parcels", "volumetric_weight_kg")
    op.drop_column("parcels", "height_cm")
    op.drop_column("parcels", "width_cm")
    op.drop_column("parcels", "length_cm")
    op.drop_column("parcels", "content_category")
    op.drop_column("parcels", "size_category")
    op.drop_column("branches", "facility_type")
    op.execute("DROP TYPE IF EXISTS facility_type_enum")
    op.execute("DROP TYPE IF EXISTS content_category_enum")
    # size_category_enum existed in init.sql — leave enum in place on downgrade
