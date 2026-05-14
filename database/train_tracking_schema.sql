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
    cargo_tons REAL,
    day_number INTEGER NOT NULL DEFAULT 1,
    leg_status VARCHAR(20) NOT NULL DEFAULT 'planned'
        CHECK (leg_status IN ('planned', 'in_transit', 'arrived', 'cancelled')),
    departed_at TIMESTAMPTZ,
    expected_arrival_at TIMESTAMPTZ,
    arrived_at TIMESTAMPTZ,
    expected_duration_seconds INTEGER NOT NULL DEFAULT 86400,
    paused_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_train_trip_legs_schedule ON train_trip_legs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_train_trip_legs_status ON train_trip_legs(leg_status);
CREATE INDEX IF NOT EXISTS idx_train_trip_legs_arrival ON train_trip_legs(expected_arrival_at);

-- Idempotent for databases created before pause support:
ALTER TABLE train_trip_legs ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;
