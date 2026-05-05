-- TAZARA Phase 4 Database Schema
-- Intelligent Resource Matching Tables
-- Updated to work with existing Phase 1/2 tables
-- Created: 2026-02-12

-- ============================================
-- PHASE 4: DRIVER SKILLS - ALTER EXISTING TABLE
-- ============================================

-- Add Phase 4 columns to existing driver_skills table
ALTER TABLE driver_skills 
    ADD COLUMN IF NOT EXISTS driver_name VARCHAR(100) DEFAULT 'Unknown',
    ADD COLUMN IF NOT EXISTS skill_category VARCHAR(50) DEFAULT 'locomotive',
    ADD COLUMN IF NOT EXISTS locomotive_types JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS route_expertise JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS safety_score DECIMAL(5,2) DEFAULT 95.0,
    ADD COLUMN IF NOT EXISTS preferred_shifts JSONB DEFAULT '["day"]',
    ADD COLUMN IF NOT EXISTS max_overtime_hours DECIMAL(4,1) DEFAULT 4.0,
    ADD COLUMN IF NOT EXISTS current_status VARCHAR(20) DEFAULT 'available',
    ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Skill-task matching history
CREATE TABLE IF NOT EXISTS skill_task_matching (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,  -- 'schedule', 'maintenance', 'special'
    driver_id VARCHAR(50) NOT NULL REFERENCES driver_skills(driver_id),
    route VARCHAR(50),
    
    -- Matching criteria
    required_skills JSONB NOT NULL,
    matched_skills JSONB NOT NULL,
    skill_match_score DECIMAL(5,2) NOT NULL,  -- 0-100
    
    -- Assignment details
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP,
    task_duration_hours DECIMAL(5,2),
    
    -- Outcome
    success_rating DECIMAL(3,2),  -- 0.0 to 1.0
    feedback_notes TEXT,
    
    -- Performance
    efficiency_achieved DECIMAL(5,2),
    cost_incurred DECIMAL(10,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PHASE 4: GEOGRAPHIC CLUSTERS & OPTIMIZATION
-- ============================================

-- Geographic clusters for route optimization
CREATE TABLE IF NOT EXISTS geographic_clusters (
    id SERIAL PRIMARY KEY,
    cluster_id VARCHAR(50) NOT NULL UNIQUE,
    cluster_name VARCHAR(100) NOT NULL,
    
    -- Geographic center
    center_lat DECIMAL(10, 8) NOT NULL,
    center_lng DECIMAL(11, 8) NOT NULL,
    radius_km DECIMAL(6,2) NOT NULL DEFAULT 50.0,
    
    -- Coverage area
    bounding_box JSONB,  -- {min_lat, max_lat, min_lng, max_lng}
    covered_routes JSONB DEFAULT '[]',  -- ['DAR_KAPIRI', 'DAR_MBEYA']
    covered_stations JSONB DEFAULT '[]',
    
    -- Optimization factors
    fuel_efficiency_factor DECIMAL(4,3) DEFAULT 1.0,  -- multiplier (0.8 = 20% savings)
    avg_travel_time_reduction DECIMAL(5,2) DEFAULT 0.0,  -- minutes saved
    cost_reduction_factor DECIMAL(4,3) DEFAULT 1.0,
    
    -- Traffic patterns
    peak_hours JSONB DEFAULT '[{"start": 7, "end": 9}, {"start": 17, "end": 19}]',
    congestion_factor DECIMAL(3,2) DEFAULT 1.0,
    
    -- Environmental factors
    elevation_profile JSONB,  -- elevation changes affecting fuel
    weather_risk_score DECIMAL(4,2) DEFAULT 0.0,  -- 0-1 risk score
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Route segment optimization
CREATE TABLE IF NOT EXISTS route_segments (
    id SERIAL PRIMARY KEY,
    segment_id VARCHAR(50) NOT NULL UNIQUE,
    start_station VARCHAR(100) NOT NULL,
    end_station VARCHAR(100) NOT NULL,
    route VARCHAR(50) NOT NULL,
    
    -- Distance and time
    distance_km DECIMAL(6,2) NOT NULL,
    base_travel_time_minutes INTEGER NOT NULL,
    
    -- Optimization data
    optimal_speed_kmh DECIMAL(4,1) DEFAULT 40.0,
    fuel_consumption_liters DECIMAL(6,2),
    fuel_cost_zmw DECIMAL(8,2),
    
    -- Conditions
    terrain_type VARCHAR(20) DEFAULT 'flat',  -- 'flat', 'hilly', 'mountainous'
    track_condition VARCHAR(20) DEFAULT 'good',  -- 'excellent', 'good', 'fair', 'poor'
    
    -- Geographic data
    cluster_id VARCHAR(50) REFERENCES geographic_clusters(cluster_id),
    waypoints JSONB,  -- Array of {lat, lng} for the route
    
    -- Historical performance
    avg_actual_time DECIMAL(6,2),
    delay_frequency DECIMAL(4,3) DEFAULT 0.0,  -- 0-1
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analyzed TIMESTAMP
);

-- ============================================
-- PHASE 4: ASSET MANAGEMENT
-- ============================================

-- Asset inventory and assignments
CREATE TABLE IF NOT EXISTS asset_assignments (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(50) NOT NULL,
    asset_type VARCHAR(50) NOT NULL,  -- 'locomotive', 'wagon', 'equipment', 'facility'
    asset_name VARCHAR(100) NOT NULL,
    
    -- Assignment details
    schedule_id VARCHAR(50),
    driver_id VARCHAR(50) REFERENCES driver_skills(driver_id),
    route VARCHAR(50),
    
    -- Time period
    assignment_start TIMESTAMP NOT NULL,
    assignment_end TIMESTAMP,
    
    -- Utilization
    planned_utilization_hours DECIMAL(5,2),
    actual_utilization_hours DECIMAL(5,2),
    utilization_rate DECIMAL(5,2),  -- percentage
    
    -- Performance
    efficiency_rating DECIMAL(4,2),
    maintenance_required BOOLEAN DEFAULT FALSE,
    issues_encountered JSONB DEFAULT '[]',
    
    -- Cost tracking
    operating_cost_zmw DECIMAL(10,2),
    revenue_generated_zmw DECIMAL(10,2),
    profit_margin DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asset utilization tracking
CREATE TABLE IF NOT EXISTS asset_utilization_daily (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(50) NOT NULL,
    asset_type VARCHAR(50) NOT NULL,
    metric_date DATE NOT NULL,
    
    -- Daily metrics
    hours_in_service DECIMAL(4,1) DEFAULT 0.0,
    hours_idle DECIMAL(4,1) DEFAULT 0.0,
    hours_maintenance DECIMAL(4,1) DEFAULT 0.0,
    total_hours_available DECIMAL(4,1) DEFAULT 24.0,
    
    -- Utilization calculation
    utilization_rate DECIMAL(5,2) DEFAULT 0.0,  -- percentage
    
    -- Performance
    cargo_volume_tons DECIMAL(8,2) DEFAULT 0.0,
    trips_completed INTEGER DEFAULT 0,
    delays_incurred INTEGER DEFAULT 0,
    
    -- Costs and revenue
    operating_cost_zmw DECIMAL(10,2) DEFAULT 0.0,
    fuel_consumed_liters DECIMAL(8,2) DEFAULT 0.0,
    
    UNIQUE(asset_id, metric_date)
);

-- ============================================
-- PHASE 4: RESOURCE CONFLICT RESOLUTION
-- ============================================

-- Resource conflicts and resolutions
CREATE TABLE IF NOT EXISTS resource_conflicts (
    id SERIAL PRIMARY KEY,
    conflict_id VARCHAR(50) NOT NULL UNIQUE,
    conflict_type VARCHAR(50) NOT NULL,  -- 'double_booking', 'skill_mismatch', 'asset_shortage'
    
    -- Affected resources
    resource_type VARCHAR(50) NOT NULL,  -- 'driver', 'locomotive', 'wagon'
    resource_id VARCHAR(50) NOT NULL,
    
    -- Conflicting assignments
    primary_assignment_id VARCHAR(50) NOT NULL,
    conflicting_assignment_id VARCHAR(50) NOT NULL,
    
    -- Time overlap
    overlap_start TIMESTAMP NOT NULL,
    overlap_end TIMESTAMP NOT NULL,
    overlap_duration_minutes INTEGER NOT NULL,
    
    -- Detection
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detected_by VARCHAR(50) DEFAULT 'system',  -- 'system', 'manual', 'schedule_change'
    
    -- Resolution
    status VARCHAR(20) DEFAULT 'open',  -- 'open', 'resolved', 'escalated', 'ignored'
    resolution_type VARCHAR(50),  -- 'reassign', 'reschedule', 'add_resource', 'cancel'
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(50),
    resolution_notes TEXT,
    
    -- Impact
    cost_impact_zmw DECIMAL(10,2) DEFAULT 0.0,
    delay_impact_minutes INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PHASE 4: OPTIMIZATION RECOMMENDATIONS - ALTER EXISTING
-- ============================================

-- Add Phase 4 columns to existing optimization_recommendations table
ALTER TABLE optimization_recommendations 
    ADD COLUMN IF NOT EXISTS recommendation_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS target_resource_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS target_resource_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS current_state JSONB,
    ADD COLUMN IF NOT EXISTS recommended_state JSONB,
    ADD COLUMN IF NOT EXISTS expected_improvement JSONB,
    ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(4,3),
    ADD COLUMN IF NOT EXISTS reasoning TEXT,
    ADD COLUMN IF NOT EXISTS factors_considered JSONB,
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Driver skills indexes
CREATE INDEX IF NOT EXISTS idx_driver_skills_category ON driver_skills(skill_category);
CREATE INDEX IF NOT EXISTS idx_driver_skills_status ON driver_skills(current_status);
CREATE INDEX IF NOT EXISTS idx_driver_skills_route ON driver_skills USING GIN(route_expertise);

-- Skill matching indexes
CREATE INDEX IF NOT EXISTS idx_skill_task_driver ON skill_task_matching(driver_id);
CREATE INDEX IF NOT EXISTS idx_skill_task_date ON skill_task_matching(assigned_date);
CREATE INDEX IF NOT EXISTS idx_skill_task_score ON skill_task_matching(skill_match_score);

-- Geographic indexes
CREATE INDEX IF NOT EXISTS idx_geo_clusters_location ON geographic_clusters(center_lat, center_lng);
CREATE INDEX IF NOT EXISTS idx_geo_clusters_routes ON geographic_clusters USING GIN(covered_routes);
CREATE INDEX IF NOT EXISTS idx_route_segments_route ON route_segments(route);

-- Asset indexes
CREATE INDEX IF NOT EXISTS idx_asset_assignments_asset ON asset_assignments(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_assignments_driver ON asset_assignments(driver_id);
CREATE INDEX IF NOT EXISTS idx_asset_assignments_schedule ON asset_assignments(schedule_id);
CREATE INDEX IF NOT EXISTS idx_asset_util_daily ON asset_utilization_daily(asset_id, metric_date);

-- Conflict indexes
CREATE INDEX IF NOT EXISTS idx_conflicts_resource ON resource_conflicts(resource_id, status);
CREATE INDEX IF NOT EXISTS idx_conflicts_status ON resource_conflicts(status);

-- Recommendation indexes
CREATE INDEX IF NOT EXISTS idx_recommendations_type ON optimization_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON optimization_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON optimization_recommendations(priority);

-- ============================================
-- SAMPLE DATA INSERTION (for testing)
-- ============================================

-- Update existing driver skills with Phase 4 data
UPDATE driver_skills SET 
    driver_name = CASE driver_id
        WHEN 'driver_001' THEN 'John Mutale'
        WHEN 'driver_002' THEN 'Grace Banda'
        WHEN 'driver_003' THEN 'Peter Zulu'
        WHEN 'driver_004' THEN 'Mary Chileshe'
        WHEN 'driver_005' THEN 'Charles Bwalya'
        ELSE driver_name
    END,
    skill_category = 'locomotive',
    route_expertise = CASE driver_id
        WHEN 'driver_001' THEN '["DAR_KAPIRI", "DAR_MBEYA"]'::jsonb
        WHEN 'driver_002' THEN '["DAR_KAPIRI", "KAPIRI_NDOLA"]'::jsonb
        WHEN 'driver_003' THEN '["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"]'::jsonb
        WHEN 'driver_004' THEN '["DAR_MBEYA"]'::jsonb
        WHEN 'driver_005' THEN '["KAPIRI_NDOLA"]'::jsonb
        ELSE '["DAR_KAPIRI"]'::jsonb
    END,
    locomotive_types = '["diesel"]'::jsonb,
    preferred_shifts = '["day"]'::jsonb,
    safety_score = 95.0
WHERE driver_name = 'Unknown' OR driver_name IS NULL;

-- Insert sample geographic clusters
INSERT INTO geographic_clusters (
    cluster_id, cluster_name, center_lat, center_lng, radius_km,
    covered_routes, fuel_efficiency_factor, avg_travel_time_reduction
) VALUES
('CLUSTER_DAR', 'Dar es Salaam Hub', -6.7924, 39.2083, 75.0, '["DAR_KAPIRI", "DAR_MBEYA"]', 0.92, 15.5),
('CLUSTER_KAPIRI', 'Kapiri Mposhi Hub', -13.4500, 28.4500, 60.0, '["DAR_KAPIRI", "KAPIRI_NDOLA"]', 0.95, 12.0),
('CLUSTER_MBEYA', 'Mbeya Hub', -8.9000, 33.4500, 50.0, '["DAR_MBEYA", "KAPIRI_NDOLA"]', 0.88, 18.5)
ON CONFLICT (cluster_id) DO NOTHING;

-- Insert sample route segments
INSERT INTO route_segments (
    segment_id, start_station, end_station, route, distance_km, base_travel_time_minutes,
    optimal_speed_kmh, fuel_consumption_liters, terrain_type
) VALUES
('SEG_DAR_KAPIRI_1', 'Dar_es_Salaam_Terminal', 'Makambako_Junction', 'DAR_KAPIRI', 380.0, 480, 47.5, 1200.0, 'hilly'),
('SEG_DAR_KAPIRI_2', 'Makambako_Junction', 'Kapiri_Mposhi_Terminal', 'DAR_KAPIRI', 420.0, 540, 46.7, 1350.0, 'mountainous'),
('SEG_DAR_MBEYA_1', 'Dar_es_Salaam_Terminal', 'Makambako_Junction', 'DAR_MBEYA', 380.0, 480, 47.5, 1200.0, 'hilly'),
('SEG_DAR_MBEYA_2', 'Makambako_Junction', 'Mbeya_Station', 'DAR_MBEYA', 350.0, 450, 46.7, 1100.0, 'mountainous')
ON CONFLICT (segment_id) DO NOTHING;

-- Insert sample asset assignments
INSERT INTO asset_assignments (
    asset_id, asset_type, asset_name, driver_id, route,
    assignment_start, planned_utilization_hours, operating_cost_zmw
) VALUES
('LOC001', 'locomotive', 'TAZARA Diesel Engine 001', 'driver_001', 'DAR_KAPIRI', CURRENT_TIMESTAMP - INTERVAL '2 days', 120.0, 45000.0),
('LOC002', 'locomotive', 'TAZARA Diesel Engine 002', 'driver_002', 'DAR_MBEYA', CURRENT_TIMESTAMP - INTERVAL '1 day', 100.0, 38000.0),
('WAG001', 'wagon', 'Cargo Wagon Set A', NULL, 'DAR_KAPIRI', CURRENT_TIMESTAMP - INTERVAL '3 days', 200.0, 15000.0)
ON CONFLICT DO NOTHING;

COMMIT;
