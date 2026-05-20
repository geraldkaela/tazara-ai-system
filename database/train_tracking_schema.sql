-- Train movement tracking: legs tied to priority/auto schedules (schedules + daily_assignments)
-- Run after create_schedule_tables.py (requires schedules + daily_assignments).

ALTER TABLE daily_assignments
    ADD COLUMN IF NOT EXISTS departure_date TIMESTAMP;

CREATE TABLE IF NOT EXISTS train_trip_legs (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(50) NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
    train_id VARCHAR(40) NOT NULL,
    route_display VARCHAR(300) NOT NULL,
    origin_station VARCHAR(160),
    destination_station VARCHAR(160),
    final_destination VARCHAR(160),
    cargo_tons REAL,
    day_number INTEGER NOT NULL DEFAULT 1,
    assignment_id INTEGER,
    leg_index INTEGER NOT NULL DEFAULT 0,
    leg_count INTEGER NOT NULL DEFAULT 1,
    leg_status VARCHAR(20) NOT NULL DEFAULT 'planned'
        CHECK (leg_status IN ('planned', 'in_transit', 'dwell_time', 'arrived', 'cancelled')),
    departed_at TIMESTAMPTZ,
    expected_arrival_at TIMESTAMPTZ,
    arrived_at TIMESTAMPTZ,
    expected_duration_seconds INTEGER NOT NULL DEFAULT 86400,
    estimated_route_km REAL,
    planned_dwell_seconds INTEGER NOT NULL DEFAULT 0,
    dwell_started_at TIMESTAMPTZ,
    dwell_until TIMESTAMPTZ,
    paused_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_train_trip_legs_schedule ON train_trip_legs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_train_trip_legs_status ON train_trip_legs(leg_status);
CREATE INDEX IF NOT EXISTS idx_train_trip_legs_arrival ON train_trip_legs(expected_arrival_at);

-- Idempotent for databases created before multi-station tracking support:
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS assignment_id INTEGER;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS leg_index INTEGER NOT NULL DEFAULT 0;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS leg_count INTEGER NOT NULL DEFAULT 1;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS final_destination VARCHAR(160);
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS estimated_route_km REAL;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS planned_dwell_seconds INTEGER NOT NULL DEFAULT 0;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS dwell_started_at TIMESTAMPTZ;
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS dwell_until TIMESTAMPTZ;
ALTER TABLE train_trip_legs DROP CONSTRAINT IF EXISTS train_trip_legs_leg_status_check;
ALTER TABLE train_trip_legs
    ADD CONSTRAINT train_trip_legs_leg_status_check
    CHECK (leg_status IN ('planned', 'in_transit', 'dwell_time', 'arrived', 'cancelled'));
CREATE INDEX IF NOT EXISTS idx_train_trip_legs_assignment ON train_trip_legs(assignment_id, leg_index);
