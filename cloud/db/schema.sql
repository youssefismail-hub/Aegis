-- AEGIS telemetry database schema.
-- Uses TimescaleDB (a PostgreSQL extension) for time-series performance
-- on the telemetry table, while keeping everything in one database
-- instead of splitting into separate relational + time-series systems.
-- See docs/decisions/ for the ADR on this choice (write it after this step).

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin TEXT UNIQUE,
    make TEXT,
    model TEXT,
    year INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(id),
    device_uid TEXT UNIQUE NOT NULL,
    firmware_version TEXT,
    last_seen TIMESTAMPTZ
);

-- Regular table first, then converted to a TimescaleDB hypertable below.
-- A hypertable automatically partitions data by time under the hood,
-- which is what makes time-range queries ("give me the last hour of RPM")
-- fast even as this table grows into millions of rows.
CREATE TABLE telemetry (
    time TIMESTAMPTZ NOT NULL,
    device_id UUID REFERENCES devices(id),
    pid TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL
);

SELECT create_hypertable('telemetry', 'time');

CREATE TABLE dtc_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id),
    code TEXT NOT NULL,
    description TEXT,
    severity TEXT CHECK (severity IN ('critical', 'warning', 'info')),
    detected_at TIMESTAMPTZ DEFAULT now(),
    cleared_at TIMESTAMPTZ
);