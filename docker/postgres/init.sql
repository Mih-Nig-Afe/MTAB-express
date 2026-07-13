-- Run before the first Alembic migration.
-- Alembic creates tables; this file creates the PostgreSQL enum types
-- that those tables reference.

CREATE TYPE parcel_status_enum AS ENUM (
    'created',
    'received_at_origin',
    'in_transit',
    'arrived_at_destination',
    'ready_for_pickup',
    'delivered',
    'returned',
    'cancelled',
    'lost',
    'on_hold'
);

CREATE TYPE payment_mode_enum AS ENUM ('before', 'after');
CREATE TYPE payment_method_enum AS ENUM ('cash', 'chapa');
CREATE TYPE payment_status_enum AS ENUM ('pending', 'paid', 'failed');
CREATE TYPE staff_role_enum AS ENUM ('operator', 'manager', 'driver', 'admin');
CREATE TYPE size_category_enum AS ENUM ('small', 'medium', 'large', 'oversized');
CREATE TYPE manifest_status_enum AS ENUM ('open', 'dispatched', 'received');
