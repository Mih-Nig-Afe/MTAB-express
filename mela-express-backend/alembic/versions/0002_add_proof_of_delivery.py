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
    op.create_table(
        'parcel_proof_of_delivery',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parcel_id', sa.UUID(), nullable=False),
        sa.Column('photo_url', sa.String(length=500), nullable=False),
        sa.Column('signature_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('parcel_proof_of_delivery')
