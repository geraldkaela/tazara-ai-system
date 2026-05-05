-- TAZARA Multi-Route System - Labor Cost Tracking Schema
-- Phase 1: Enhanced Labor Cost Optimization

-- Labor cost tracking table
CREATE TABLE IF NOT EXISTS labor_costs (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) NOT NULL,
    driver_id VARCHAR(50) NOT NULL,
    train_id INTEGER,
    route_name VARCHAR(50),
    work_date DATE NOT NULL,
    
    -- Hours tracking
    regular_hours DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    overtime_hours DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    premium_overtime_hours DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    total_hours DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    
    -- Cost breakdown
    base_hourly_rate DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    regular_cost_zmw DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    overtime_cost_zmw DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    premium_overtime_cost_zmw DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_labor_cost_zmw DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    
    -- Driver attributes
    skill_level VARCHAR(20) DEFAULT 'beginner',
    shift_type VARCHAR(20) DEFAULT 'day',
    is_weekend BOOLEAN DEFAULT FALSE,
    
    -- Route and efficiency factors
    route_complexity_factor DECIMAL(3,2) DEFAULT 1.00,
    efficiency_score DECIMAL(5,2) DEFAULT 0.00,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (schedule_id) REFERENCES multi_route_schedules(schedule_id) ON DELETE CASCADE
);

-- Optimization events tracking
CREATE TABLE IF NOT EXISTS optimization_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    schedule_id VARCHAR(100),
    event_description TEXT,
    
    -- Before/after states
    old_assignment JSONB,
    new_assignment JSONB,
    
    -- Performance metrics
    cost_savings_zmw DECIMAL(12,2) DEFAULT 0.00,
    efficiency_improvement DECIMAL(5,2) DEFAULT 0.00,
    overtime_reduction_hours DECIMAL(5,2) DEFAULT 0.00,
    
    -- Processing metrics
    processing_time_ms INTEGER,
    algorithm_version VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (schedule_id) REFERENCES multi_route_schedules(schedule_id) ON DELETE CASCADE
);

-- Driver skills and certifications
CREATE TABLE IF NOT EXISTS driver_skills (
    id SERIAL PRIMARY KEY,
    driver_id VARCHAR(50) NOT NULL UNIQUE,
    
    -- Skill levels
    current_skill_level VARCHAR(20) DEFAULT 'beginner',
    years_experience INTEGER DEFAULT 0,
    training_hours INTEGER DEFAULT 0,
    
    -- Certifications
    certifications JSONB DEFAULT '[]',
    
    -- Performance metrics
    average_efficiency_score DECIMAL(5,2) DEFAULT 0.00,
    total_hours_worked DECIMAL(8,2) DEFAULT 0.00,
    accident_free_days INTEGER DEFAULT 0,
    
    -- Cost factors
    skill_premium_multiplier DECIMAL(3,2) DEFAULT 1.00,
    reliability_score DECIMAL(3,2) DEFAULT 1.00,
    
    -- Metadata
    last_skill_assessment DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shift assignments and preferences
CREATE TABLE IF NOT EXISTS shift_assignments (
    id SERIAL PRIMARY KEY,
    driver_id VARCHAR(50) NOT NULL,
    schedule_id VARCHAR(100),
    
    -- Shift details
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) NOT NULL, -- day, evening, night, weekend
    start_time TIME,
    end_time TIME,
    
    -- Preferences and constraints
    preferred_shift VARCHAR(20),
    max_hours_per_shift DECIMAL(5,2) DEFAULT 8.00,
    max_overtime_hours DECIMAL(5,2) DEFAULT 4.00,
    
    -- Performance
    actual_hours_worked DECIMAL(5,2) DEFAULT 0.00,
    shift_efficiency DECIMAL(5,2) DEFAULT 0.00,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (driver_id) REFERENCES driver_skills(driver_id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES multi_route_schedules(schedule_id) ON DELETE CASCADE
);

-- Labor cost optimization recommendations
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100),
    recommendation_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    
    -- Recommendation details
    description TEXT NOT NULL,
    potential_savings_zmw DECIMAL(12,2) DEFAULT 0.00,
    potential_savings_percentage DECIMAL(5,2) DEFAULT 0.00,
    implementation_effort VARCHAR(20) DEFAULT 'medium',
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, rejected
    implementation_date DATE,
    actual_savings_zmw DECIMAL(12,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (schedule_id) REFERENCES multi_route_schedules(schedule_id) ON DELETE CASCADE
);

-- Labor performance trends
CREATE TABLE IF NOT EXISTS labor_performance_trends (
    id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    route_name VARCHAR(50),
    
    -- Aggregated metrics
    total_drivers_worked INTEGER DEFAULT 0,
    total_hours_worked DECIMAL(8,2) DEFAULT 0.00,
    total_overtime_hours DECIMAL(8,2) DEFAULT 0.00,
    total_labor_cost_zmw DECIMAL(12,2) DEFAULT 0.00,
    
    -- Performance indicators
    average_efficiency_score DECIMAL(5,2) DEFAULT 0.00,
    average_cost_per_hour DECIMAL(8,2) DEFAULT 0.00,
    overtime_percentage DECIMAL(5,2) DEFAULT 0.00,
    
    -- Trend analysis
    cost_trend_percentage DECIMAL(5,2) DEFAULT 0.00,
    efficiency_trend_percentage DECIMAL(5,2) DEFAULT 0.00,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (metric_date, route_name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_labor_costs_schedule_id ON labor_costs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_labor_costs_driver_id ON labor_costs(driver_id);
CREATE INDEX IF NOT EXISTS idx_labor_costs_work_date ON labor_costs(work_date);
CREATE INDEX IF NOT EXISTS idx_optimization_events_schedule_id ON optimization_events(schedule_id);
CREATE INDEX IF NOT EXISTS idx_optimization_events_type ON optimization_events(event_type);
CREATE INDEX IF NOT EXISTS idx_driver_skills_driver_id ON driver_skills(driver_id);
CREATE INDEX IF NOT EXISTS idx_shift_assignments_driver_id ON shift_assignments(driver_id);
CREATE INDEX IF NOT EXISTS idx_shift_assignments_date ON shift_assignments(shift_date);
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_schedule_id ON optimization_recommendations(schedule_id);
CREATE INDEX IF NOT EXISTS idx_labor_performance_trends_date ON labor_performance_trends(metric_date);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_labor_costs_updated_at BEFORE UPDATE ON labor_costs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_driver_skills_updated_at BEFORE UPDATE ON driver_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shift_assignments_updated_at BEFORE UPDATE ON shift_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_optimization_recommendations_updated_at BEFORE UPDATE ON optimization_recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample driver skills data
INSERT INTO driver_skills (driver_id, current_skill_level, years_experience, skill_premium_multiplier) VALUES
('driver_001', 'advanced', 5, 1.4),
('driver_002', 'intermediate', 3, 1.2),
('driver_003', 'beginner', 1, 1.0),
('driver_004', 'advanced', 7, 1.4),
('driver_005', 'intermediate', 4, 1.2),
('driver_006', 'beginner', 2, 1.0)
ON CONFLICT (driver_id) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE labor_costs IS 'Tracks detailed labor costs for each driver assignment including overtime, premiums, and efficiency metrics';
COMMENT ON TABLE optimization_events IS 'Logs optimization events and their impact on cost and efficiency';
COMMENT ON TABLE driver_skills IS 'Maintains driver skill levels, certifications, and performance history';
COMMENT ON TABLE shift_assignments IS 'Tracks driver shift assignments, preferences, and performance';
COMMENT ON TABLE optimization_recommendations IS 'Stores optimization recommendations and their implementation status';
COMMENT ON TABLE labor_performance_trends IS 'Aggregated labor performance metrics for trend analysis';
