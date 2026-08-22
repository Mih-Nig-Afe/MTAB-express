"""Add OTP columns to parcels and create manifest_checkpoints table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-22 14:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add OTP columns to parcels
    op.add_column('parcels', sa.Column('pickup_otp', sa.String(length=10), nullable=True))
    op.add_column('parcels', sa.Column('otp_expires_at', sa.DateTime(timezone=True), nullable=True))

    # Create manifest_checkpoints table
    op.create_table(
        'manifest_checkpoints',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('manifest_id', sa.UUID(), nullable=False),
        sa.Column('location_name', sa.String(length=120), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['manifest_id'], ['transfer_manifests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('manifest_checkpoints')
    op.drop_column('parcels', 'otp_expires_at')
    op.drop_column('parcels', 'pickup_otp')
