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
    # Use existing enums created by postgres init.sql
    staff_role_enum = postgresql.ENUM('operator', 'manager', 'driver', 'admin', name='staff_role_enum', create_type=False)
    payment_mode_enum = postgresql.ENUM('before', 'after', name='payment_mode_enum', create_type=False)
    payment_method_enum = postgresql.ENUM('cash', 'chapa', name='payment_method_enum', create_type=False)
    payment_status_enum = postgresql.ENUM('pending', 'paid', 'failed', name='payment_status_enum', create_type=False)
    parcel_status_enum = postgresql.ENUM('created', 'received_at_origin', 'in_transit', 'arrived_at_destination', 'ready_for_pickup', 'delivered', 'returned', 'cancelled', 'lost', 'on_hold', name='parcel_status_enum', create_type=False)
    manifest_status_enum = postgresql.ENUM('open', 'dispatched', 'received', 'draft', 'in_transit', 'cancelled', name='manifest_status_enum', create_type=False)

    op.create_table(
        'branches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    op.create_table(
        'staff_users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', staff_role_enum, nullable=False),
        sa.Column('branch_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('email')
    )

    op.create_table(
        'customers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=False),
        sa.Column('telegram_id', sa.String(length=40), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_phone'), 'customers', ['phone'], unique=True)
    op.create_index(op.f('ix_customers_telegram_id'), 'customers', ['telegram_id'], unique=True)

    op.create_table(
        'parcels',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tracking_code', sa.String(length=30), nullable=False),
        sa.Column('origin_branch_id', sa.UUID(), nullable=False),
        sa.Column('destination_branch_id', sa.UUID(), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=False),
        sa.Column('receiver_name', sa.String(length=120), nullable=False),
        sa.Column('receiver_phone', sa.String(length=30), nullable=False),
        sa.Column('receiver_id', sa.UUID(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight_kg', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('declared_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_mode', payment_mode_enum, nullable=False),
        sa.Column('payment_method', payment_method_enum, nullable=True),
        sa.Column('payment_status', payment_status_enum, nullable=False),
        sa.Column('status', parcel_status_enum, nullable=False),
        sa.Column('waybill_url', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['destination_branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['origin_branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['receiver_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parcels_tracking_code'), 'parcels', ['tracking_code'], unique=True)

    op.create_table(
        'parcel_status_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parcel_id', sa.UUID(), nullable=False),
        sa.Column('from_status', parcel_status_enum, nullable=True),
        sa.Column('to_status', parcel_status_enum, nullable=False),
        sa.Column('changed_by', sa.UUID(), nullable=True),
        sa.Column('branch_id', sa.UUID(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['changed_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parcel_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('method', payment_method_enum, nullable=False),
        sa.Column('chapa_tx_ref', sa.String(length=100), nullable=True),
        sa.Column('status', payment_status_enum, nullable=False),
        sa.Column('collected_by', sa.UUID(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['collected_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_chapa_tx_ref'), 'payments', ['chapa_tx_ref'], unique=True)

    op.create_table(
        'transfer_manifests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('origin_branch_id', sa.UUID(), nullable=False),
        sa.Column('destination_branch_id', sa.UUID(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('driver_name', sa.String(length=120), nullable=True),
        sa.Column('vehicle_plate', sa.String(length=20), nullable=True),
        sa.Column('status', manifest_status_enum, nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['destination_branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['origin_branch_id'], ['branches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'manifest_parcels',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('manifest_id', sa.UUID(), nullable=False),
        sa.Column('parcel_id', sa.UUID(), nullable=False),
        sa.Column('received', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['manifest_id'], ['transfer_manifests.id'], ),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.id'], ),
        sa.ForeignKeyConstraint(['received_by'], ['staff_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'notification_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parcel_id', sa.UUID(), nullable=True),
        sa.Column('customer_id', sa.UUID(), nullable=True),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['parcel_id'], ['parcels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('notification_logs')
    op.drop_table('manifest_parcels')
    op.drop_table('transfer_manifests')
    op.drop_table('payments')
    op.drop_table('parcel_status_history')
    op.drop_table('parcels')
    op.drop_table('customers')
    op.drop_table('staff_users')
    op.drop_table('branches')
