"""Air-cargo journey scans, flight legs, pickup reminders.

Revision ID: 0005_journey_tracking
Revises: 0004_customer_language
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_journey_tracking"
down_revision = "0004_customer_language"
branch_labels = None
depends_on = None

NEW_STATUSES = [
    "processed_at_origin",
    "dispatched_from_origin",
    "arrived_origin_airport",
    "checked_in_flight",
    "departed",
    "arrived_destination_airport",
    "released_from_airport",
    "distributed_to_branch",
]


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for value in NEW_STATUSES:
            op.execute(
                sa.text(f"ALTER TYPE parcel_status_enum ADD VALUE IF NOT EXISTS '{value}'")
            )

    op.add_column("branches", sa.Column("airport_iata", sa.String(length=4), nullable=True))
    op.add_column("branches", sa.Column("latitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("branches", sa.Column("longitude", sa.Numeric(9, 6), nullable=True))

    op.add_column("parcels", sa.Column("origin_airport_iata", sa.String(length=4), nullable=True))
    op.add_column("parcels", sa.Column("dest_airport_iata", sa.String(length=4), nullable=True))
    op.add_column("parcels", sa.Column("promised_delivery_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parcels", sa.Column("current_eta_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parcels", sa.Column("pickup_ready_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "parcels",
        sa.Column("pickup_reminders_sent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("parcels", sa.Column("last_pickup_reminder_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "parcel_journey_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parcel_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("to_status", postgresql.ENUM(name="parcel_status_enum", create_type=False), nullable=True),
        sa.Column("location_name", sa.String(length=160), nullable=True),
        sa.Column("facility_type", sa.String(length=40), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("flight_number", sa.String(length=12), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="staff"),
        sa.Column("actor_staff_id", sa.UUID(), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_staff_id"], ["staff_users.id"]),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parcel_journey_events_parcel_id", "parcel_journey_events", ["parcel_id"])

    op.create_table(
        "parcel_flight_legs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parcel_id", sa.UUID(), nullable=False),
        sa.Column("flight_number", sa.String(length=12), nullable=False),
        sa.Column("airline_iata", sa.String(length=4), nullable=True),
        sa.Column("airline_name", sa.String(length=80), nullable=True),
        sa.Column("origin_iata", sa.String(length=4), nullable=True),
        sa.Column("dest_iata", sa.String(length=4), nullable=True),
        sa.Column("airway_bill", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_departure", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_arrival", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_departure", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_arrival", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delay_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("altitude_m", sa.Numeric(8, 1), nullable=True),
        sa.Column("heading", sa.Numeric(6, 1), nullable=True),
        sa.Column("velocity_ms", sa.Numeric(8, 2), nullable=True),
        sa.Column("on_ground", sa.Boolean(), nullable=True),
        sa.Column("last_position_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parcel_flight_legs_parcel_id", "parcel_flight_legs", ["parcel_id"])
    op.create_index("ix_parcel_flight_legs_flight_number", "parcel_flight_legs", ["flight_number"])

    op.create_table(
        "pickup_reminder_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parcel_id", sa.UUID(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("recipient_role", sa.String(length=20), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="sent"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pickup_reminder_logs_parcel_id", "pickup_reminder_logs", ["parcel_id"])


def downgrade() -> None:
    op.drop_index("ix_pickup_reminder_logs_parcel_id", table_name="pickup_reminder_logs")
    op.drop_table("pickup_reminder_logs")
    op.drop_index("ix_parcel_flight_legs_flight_number", table_name="parcel_flight_legs")
    op.drop_index("ix_parcel_flight_legs_parcel_id", table_name="parcel_flight_legs")
    op.drop_table("parcel_flight_legs")
    op.drop_index("ix_parcel_journey_events_parcel_id", table_name="parcel_journey_events")
    op.drop_table("parcel_journey_events")
    op.drop_column("parcels", "last_pickup_reminder_at")
    op.drop_column("parcels", "pickup_reminders_sent")
    op.drop_column("parcels", "pickup_ready_at")
    op.drop_column("parcels", "current_eta_at")
    op.drop_column("parcels", "promised_delivery_at")
    op.drop_column("parcels", "dest_airport_iata")
    op.drop_column("parcels", "origin_airport_iata")
    op.drop_column("branches", "longitude")
    op.drop_column("branches", "latitude")
    op.drop_column("branches", "airport_iata")
    # Enum values cannot be removed safely on PostgreSQL.
