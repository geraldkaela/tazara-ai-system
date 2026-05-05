-- TAZARA Multi-Route Table Creation
-- Run this AFTER connecting to tazara_multi_route database

-- 5. Create tables
CREATE TABLE IF NOT EXISTS multi_route_schedules (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    num_trains INTEGER NOT NULL,
    total_days INTEGER NOT NULL,
    cargo_requirements JSONB NOT NULL,
    daily_actions JSONB NOT NULL,
    train_assignments JSONB NOT NULL,
    performance_metrics JSONB NOT NULL,
    cost_breakdown_zmw JSONB NOT NULL,
    efficiency_analysis JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS performance_history (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) REFERENCES multi_route_schedules(schedule_id),
    metric_date DATE NOT NULL,
    total_cargo_delivered DECIMAL(10,2) NOT NULL,
    trains_used INTEGER NOT NULL,
    efficiency DECIMAL(10,2) NOT NULL,
    net_profit_zmw DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) REFERENCES multi_route_schedules(schedule_id),
    action_type VARCHAR(50) NOT NULL,
    action_details JSONB,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'INFO'
);

-- 6. Insert default configuration
INSERT INTO system_configuration (config_key, config_value, description) VALUES
('max_trains', '12', 'Maximum number of trains supported'),
('default_planning_horizon', '14', 'Default planning horizon in days'),
('coordination_bonus_enabled', 'true', 'Enable coordination bonus'),
('performance_threshold', '85', 'Performance threshold percentage')
ON CONFLICT (config_key) DO NOTHING;

-- 7. Grant privileges to tazara user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tazara;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tazara;

-- 8. Show created tables
\dt

SELECT 'Database tables created successfully!' as status;
