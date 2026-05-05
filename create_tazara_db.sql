-- TAZARA Multi-Route Database Setup - pgAdmin Compatible
-- Copy and paste this entire script into pgAdmin Query Tool

-- Drop existing database and user (clean start)
DROP DATABASE IF EXISTS tazara_multi_route;
DROP USER IF EXISTS tazara;

-- Create fresh user
CREATE USER tazara WITH PASSWORD 'tazara123';

-- Create fresh database
CREATE DATABASE tazara_multi_route OWNER tazara;

-- Note: In pgAdmin, you need to manually connect to tazara_multi_route database
-- Then run the table creation commands below

-- TAZARA Multi-Route Tables Only
CREATE TABLE multi_route_schedules (
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

CREATE TABLE performance_history (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) REFERENCES multi_route_schedules(schedule_id),
    metric_date DATE NOT NULL,
    total_cargo_delivered DECIMAL(10,2) NOT NULL,
    trains_used INTEGER NOT NULL,
    efficiency DECIMAL(10,2) NOT NULL,
    net_profit_zmw DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE system_configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) REFERENCES multi_route_schedules(schedule_id),
    action_type VARCHAR(50) NOT NULL,
    action_details JSONB,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'INFO'
);

-- Insert default configuration
INSERT INTO system_configuration (config_key, config_value, description) VALUES
('max_trains', '12', 'Maximum number of trains supported'),
('default_planning_horizon', '14', 'Default planning horizon in days'),
('coordination_bonus_enabled', 'true', 'Enable coordination bonus'),
('performance_threshold', '85', 'Performance threshold percentage');

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tazara;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tazara;

-- View tables (SQL version for pgAdmin)
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

SELECT 'Database setup completed successfully!' as status;
