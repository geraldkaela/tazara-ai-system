-- UUID extension not required for serial IDs

-- ========================================
-- Core Tables
-- ========================================

-- Drop child tables first due to foreign key constraints
DROP TABLE IF EXISTS multi_route_audit_logs;
DROP TABLE IF EXISTS train_operations;
DROP TABLE IF EXISTS route_performance;
DROP TABLE IF EXISTS daily_performance;
DROP TABLE IF EXISTS performance_history;
DROP TABLE IF EXISTS schedule_comparisons;
DROP TABLE IF EXISTS performance_alerts;
DROP TABLE IF EXISTS model_training;
DROP TABLE IF EXISTS route_efficiency_trends;

-- Multi-Route Schedules Table
CREATE TABLE IF NOT EXISTS multi_route_schedules (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    num_trains INTEGER NOT NULL,
    total_days INTEGER NOT NULL,
    cargo_requirements JSONB NOT NULL,
    daily_actions JSONB NOT NULL,
    train_assignments JSONB NOT NULL,
    performance_metrics JSONB NOT NULL,
    cost_breakdown_zmw JSONB NOT NULL,
    efficiency_analysis JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Train Operations Table
CREATE TABLE IF NOT EXISTS train_operations (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES multi_route_schedules(id),
    train_id INTEGER NOT NULL,
    day INTEGER NOT NULL,
    action INTEGER NOT NULL,
    route_name VARCHAR(50),
    train_state VARCHAR(20),
    time_left INTEGER,
    cargo_carried DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Route Performance Table
CREATE TABLE IF NOT EXISTS route_performance (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES multi_route_schedules(id),
    route_name VARCHAR(50) NOT NULL,
    cargo_delivered DECIMAL(10,2) NOT NULL,
    trains_assigned INTEGER NOT NULL,
    efficiency_score DECIMAL(5,2),
    revenue_zmw DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily Performance Summary Table
CREATE TABLE IF NOT EXISTS daily_performance (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES multi_route_schedules(id),
    day INTEGER NOT NULL,
    total_cargo_delivered DECIMAL(10,2) NOT NULL,
    active_trains INTEGER NOT NULL,
    idle_trains INTEGER NOT NULL,
    daily_reward DECIMAL(15,2),
    daily_cost_zmw DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- Performance Tracking Tables
-- ========================================

-- Performance Metrics History
CREATE TABLE IF NOT EXISTS performance_history (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES multi_route_schedules(id),
    metric_date DATE NOT NULL,
    total_cargo_delivered DECIMAL(10,2) NOT NULL,
    trains_used INTEGER NOT NULL,
    efficiency DECIMAL(10,2) NOT NULL,
    net_profit_zmw DECIMAL(15,2) NOT NULL,
    coordination_bonus_zmw DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Route Efficiency Trends
CREATE TABLE IF NOT EXISTS route_efficiency_trends (
    id SERIAL PRIMARY KEY,
    route_name VARCHAR(50) NOT NULL,
    metric_date DATE NOT NULL,
    average_efficiency DECIMAL(5,2) NOT NULL,
    total_cargo DECIMAL(10,2) NOT NULL,
    train_utilization DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- Configuration and Settings Tables
-- ========================================

-- System Configuration
CREATE TABLE IF NOT EXISTS system_configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model Training Records
CREATE TABLE IF NOT EXISTS model_training (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    training_episodes INTEGER NOT NULL,
    final_reward DECIMAL(15,2) NOT NULL,
    training_metrics JSONB,
    model_path VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- Audit and Logging Tables
-- ========================================

-- Multi-Route Audit Logs
CREATE TABLE IF NOT EXISTS multi_route_audit_logs (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES multi_route_schedules(id),
    action_type VARCHAR(50) NOT NULL,
    action_details JSONB,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'INFO'
);

-- System Events Log
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_details JSONB,
    component VARCHAR(50),
    severity VARCHAR(20) DEFAULT 'INFO',
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- ========================================
-- Comparison and Analytics Tables
-- ========================================

-- Baseline vs Multi-Route Comparisons
CREATE TABLE IF NOT EXISTS schedule_comparisons (
    id SERIAL PRIMARY KEY,
    comparison_id VARCHAR(100) UNIQUE NOT NULL,
    multi_route_schedule_id INTEGER REFERENCES multi_route_schedules(id),
    baseline_metrics JSONB NOT NULL,
    multi_route_metrics JSONB NOT NULL,
    improvement_metrics JSONB NOT NULL,
    cargo_requirements JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance Alerts
CREATE TABLE IF NOT EXISTS performance_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    alert_message TEXT NOT NULL,
    threshold_value DECIMAL(10,2),
    actual_value DECIMAL(10,2),
    severity VARCHAR(20) DEFAULT 'WARNING',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- Indexes for Performance Optimization
-- ========================================

-- Multi-Route Schedules Indexes
CREATE INDEX IF NOT EXISTS idx_multi_route_schedules_timestamp ON multi_route_schedules(timestamp);
CREATE INDEX IF NOT EXISTS idx_multi_route_schedules_status ON multi_route_schedules(status);
CREATE INDEX IF NOT EXISTS idx_multi_route_schedules_num_trains ON multi_route_schedules(num_trains);

-- Train Operations Indexes
CREATE INDEX IF NOT EXISTS idx_train_operations_schedule ON train_operations(schedule_id);
CREATE INDEX IF NOT EXISTS idx_train_operations_day ON train_operations(day);
CREATE INDEX IF NOT EXISTS idx_train_operations_train_id ON train_operations(train_id);

-- Route Performance Indexes
CREATE INDEX IF NOT EXISTS idx_route_performance_schedule ON route_performance(schedule_id);
CREATE INDEX IF NOT EXISTS idx_route_performance_route ON route_performance(route_name);
CREATE INDEX IF NOT EXISTS idx_route_performance_efficiency ON route_performance(efficiency_score);

-- Performance History Indexes
CREATE INDEX IF NOT EXISTS idx_performance_history_date ON performance_history(metric_date);
CREATE INDEX IF NOT EXISTS idx_performance_history_schedule ON performance_history(schedule_id);
CREATE INDEX IF NOT EXISTS idx_performance_history_efficiency ON performance_history(efficiency);

-- Audit Logs Indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON multi_route_audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_schedule ON multi_route_audit_logs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON multi_route_audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON multi_route_audit_logs(severity);

-- ========================================
-- Views for Common Queries
-- ========================================

-- Drop existing views to avoid column name conflicts
DROP VIEW IF EXISTS schedule_summary;
DROP VIEW IF EXISTS route_performance_summary;
DROP VIEW IF EXISTS daily_performance_trends;

-- Schedule Summary View
CREATE OR REPLACE VIEW schedule_summary AS
SELECT 
    s.schedule_id,
    s.timestamp,
    s.num_trains,
    s.total_days,
    (s.performance_metrics->>'total_cargo_delivered')::DECIMAL as total_cargo,
    (s.performance_metrics->>'trains_used')::INTEGER as trains_used,
    (s.performance_metrics->>'efficiency')::DECIMAL as efficiency,
    (s.cost_breakdown_zmw->>'net_profit_zmw')::DECIMAL as net_profit_zmw,
    s.status
FROM multi_route_schedules s
WHERE s.status = 'active';

-- Route Performance Summary View
CREATE OR REPLACE VIEW route_performance_summary AS
SELECT 
    route_name,
    AVG(average_efficiency) as avg_efficiency,
    SUM(total_cargo) as total_cargo,
    AVG(train_utilization) as avg_utilization,
    COUNT(*) as schedule_count
FROM route_efficiency_trends
GROUP BY route_name;

-- Daily Performance Trends View
CREATE OR REPLACE VIEW daily_performance_trends AS
SELECT 
    DATE(created_at) as performance_date,
    AVG(total_cargo_delivered) as avg_cargo,
    AVG(trains_used) as avg_trains_used,
    AVG(efficiency) as avg_efficiency,
    SUM(net_profit_zmw) as total_profit
FROM performance_history
GROUP BY DATE(created_at)
ORDER BY performance_date DESC;

-- ========================================
-- Triggers for Data Integrity
-- ========================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp trigger to relevant tables
CREATE TRIGGER update_multi_route_schedules_timestamp
    BEFORE UPDATE ON multi_route_schedules
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_system_configuration_timestamp
    BEFORE UPDATE ON system_configuration
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ========================================
-- Initial Data Setup
-- ========================================

-- Insert default system configuration
INSERT INTO system_configuration (config_key, config_value, description) VALUES
('max_trains', '12', 'Maximum number of trains supported'),
('default_planning_horizon', '14', 'Default planning horizon in days'),
('coordination_bonus_enabled', 'true', 'Enable coordination bonus for multi-train operations'),
('performance_threshold', '85', 'Performance threshold percentage for alerts'),
('auto_retrain_enabled', 'false', 'Enable automatic model retraining')
ON CONFLICT (config_key) DO NOTHING;

-- Insert initial model training record
INSERT INTO model_training (model_version, training_episodes, final_reward, training_metrics, model_path, is_active) VALUES
('multi_route_v2.0', 500, 7247848.50, '{"avg_reward": 522279.40, "efficiency": 174.2}', 'models/multi_route_agent.pkl', true)
ON CONFLICT DO NOTHING;

-- ========================================
-- Sample Data (for development/testing)
-- ========================================

-- Insert sample multi-route schedule
INSERT INTO multi_route_schedules (
    schedule_id, num_trains, total_days, cargo_requirements,
    daily_actions, train_assignments, performance_metrics,
    cost_breakdown_zmw, efficiency_analysis
) VALUES (
    'multi_route_sample_001',
    6,
    14,
    '{"DAR_KAPIRI": 500, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 500}',
    '[[0, 1, 2, 0, 0, 0], [0, 0, 0, 1, 2, 0]]',
    '[{"train_id": 0, "day": 0, "action": 0, "route_name": "IDLE"}]',
    '{"total_cargo_delivered": 348, "trains_used": 2, "efficiency": 174.2}',
    '{"revenue_zmw": 34848.50, "net_profit_zmw": -158151.50}',
    '{"cargo_per_train": 174, "trains_utilization": 0.33}'
) ON CONFLICT (schedule_id) DO NOTHING;

-- ========================================
-- Schema Comments
-- ========================================

COMMENT ON TABLE multi_route_schedules IS 'Main table for storing multi-route scheduling results';
COMMENT ON TABLE train_operations IS 'Detailed train operations and assignments';
COMMENT ON TABLE route_performance IS 'Route-specific performance metrics';
COMMENT ON TABLE performance_history IS 'Historical performance tracking';
COMMENT ON TABLE multi_route_audit_logs IS 'Audit trail for multi-route operations';
COMMENT ON TABLE schedule_comparisons IS 'Baseline vs multi-route comparisons';

-- ========================================
-- Database Statistics and Maintenance
-- ========================================

-- Create function to update performance trends
CREATE OR REPLACE FUNCTION update_performance_trends()
RETURNS VOID AS $$
BEGIN
    -- Update route efficiency trends
    INSERT INTO route_efficiency_trends (route_name, metric_date, average_efficiency, total_cargo, train_utilization)
    SELECT 
        rp.route_name,
        CURRENT_DATE,
        AVG(rp.efficiency_score),
        SUM(rp.cargo_delivered),
        AVG(rp.efficiency_score / 50) * 100
    FROM route_performance rp
    WHERE rp.created_at >= CURRENT_DATE
    GROUP BY rp.route_name
    ON CONFLICT (route_name, metric_date) DO UPDATE SET
        average_efficiency = EXCLUDED.average_efficiency,
        total_cargo = EXCLUDED.total_cargo,
        train_utilization = EXCLUDED.train_utilization;
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic maintenance
CREATE OR REPLACE FUNCTION schedule_maintenance()
RETURNS VOID AS $$
BEGIN
    -- Update performance trends
    PERFORM update_performance_trends();
    
    -- Clean old audit logs (keep 90 days)
    DELETE FROM multi_route_audit_logs WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Update system statistics
    ANALYZE multi_route_schedules;
    ANALYZE train_operations;
    ANALYZE route_performance;
END;
$$ LANGUAGE plpgsql;
