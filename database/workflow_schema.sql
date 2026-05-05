-- TAZARA Workflow Enhancement Schema
-- Adds approval workflow, customer orders, and schedule modification support

-- ========================================
-- CUSTOMER ORDERS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS customer_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    cargo_type VARCHAR(50) NOT NULL,
    cargo_weight DECIMAL(10,2) NOT NULL,
    origin_station VARCHAR(50) NOT NULL,
    destination_station VARCHAR(50) NOT NULL,
    priority_level INTEGER DEFAULT 3,  -- 1=High, 2=Medium, 3=Low
    requested_departure_date DATE,
    requested_arrival_date DATE,
    special_requirements JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',  -- pending, assigned, cancelled, completed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_schedule_id VARCHAR(100) REFERENCES multi_route_schedules(schedule_id),
    assigned_train_id INTEGER,
    notes TEXT
);

-- ========================================
-- SCHEDULE APPROVAL WORKFLOW
-- ========================================
CREATE TABLE IF NOT EXISTS schedule_approvals (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) UNIQUE NOT NULL REFERENCES multi_route_schedules(schedule_id),
    approval_status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, needs_revision
    approver_id VARCHAR(50),
    approver_name VARCHAR(100),
    approval_date TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    revision_notes TEXT,
    approval_level INTEGER DEFAULT 1,  -- 1=Manager, 2=Director, 3=Executive
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- SCHEDULE MODIFICATIONS HISTORY
-- ========================================
CREATE TABLE IF NOT EXISTS schedule_modifications (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) NOT NULL REFERENCES multi_route_schedules(schedule_id),
    modification_type VARCHAR(50) NOT NULL,  -- train_add, train_remove, time_adjust, priority_change
    modification_details JSONB NOT NULL,
    previous_values JSONB,
    new_values JSONB,
    modified_by VARCHAR(50) NOT NULL,
    modification_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    impact_analysis JSONB,
    approval_required BOOLEAN DEFAULT TRUE,
    approval_status VARCHAR(20) DEFAULT 'pending'
);

-- ========================================
-- TRAIN CANCELLATIONS
-- ========================================
CREATE TABLE IF NOT EXISTS train_cancellations (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(100) NOT NULL REFERENCES multi_route_schedules(schedule_id),
    train_id INTEGER NOT NULL,
    cancellation_reason VARCHAR(200) NOT NULL,
    cancelled_by VARCHAR(50) NOT NULL,
    cancellation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    impact_analysis JSONB,
    alternative_arrangements JSONB,
    status VARCHAR(20) DEFAULT 'cancelled',  -- cancelled, rescheduled, partial_refund
    refund_amount DECIMAL(10,2),
    customer_notified BOOLEAN DEFAULT FALSE
);

-- ========================================
-- SCHEDULING PRIORITIES CONFIGURATION
-- ========================================
CREATE TABLE IF NOT EXISTS scheduling_priorities (
    id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) UNIQUE NOT NULL,
    weight_speed DECIMAL(3,2) DEFAULT 0.33,  -- 0.0 to 1.0
    weight_fuel DECIMAL(3,2) DEFAULT 0.33,   -- 0.0 to 1.0
    weight_cost DECIMAL(3,2) DEFAULT 0.34,   -- 0.0 to 1.0
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- SCHEDULING RULES AND CONSTRAINTS
-- ========================================
CREATE TABLE IF NOT EXISTS scheduling_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- time_window, capacity, maintenance, safety, custom
    rule_conditions JSONB NOT NULL,
    rule_actions JSONB NOT NULL,
    priority_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- INDEXES
-- ========================================
CREATE INDEX IF NOT EXISTS idx_customer_orders_status ON customer_orders(status);
CREATE INDEX IF NOT EXISTS idx_customer_orders_priority ON customer_orders(priority_level);
CREATE INDEX IF NOT EXISTS idx_customer_orders_dates ON customer_orders(requested_departure_date, requested_arrival_date);
CREATE INDEX IF NOT EXISTS idx_schedule_approvals_status ON schedule_approvals(approval_status);
CREATE INDEX IF NOT EXISTS idx_schedule_modifications_schedule ON schedule_modifications(schedule_id);
CREATE INDEX IF NOT EXISTS idx_train_cancellations_schedule ON train_cancellations(schedule_id);
CREATE INDEX IF NOT EXISTS idx_scheduling_priorities_active ON scheduling_priorities(is_active);
CREATE INDEX IF NOT EXISTS idx_scheduling_rules_active ON scheduling_rules(is_active);

-- ========================================
-- INSERT DEFAULT DATA
-- ========================================
INSERT INTO scheduling_priorities (priority_name, weight_speed, weight_fuel, weight_cost) VALUES
('Balanced', 0.33, 0.33, 0.34),
('Speed Priority', 0.60, 0.20, 0.20),
('Fuel Efficiency', 0.20, 0.60, 0.20),
('Cost Optimization', 0.20, 0.20, 0.60)
ON CONFLICT (priority_name) DO NOTHING;

INSERT INTO scheduling_rules (rule_name, rule_type, rule_conditions, rule_actions, priority_level) VALUES
('Max Daily Operating Hours', 'time_window', '{"max_hours": 16, "min_rest_hours": 8}', '{"action": "reject", "message": "Exceeds maximum daily operating hours"}', 1),
('Minimum Cargo Load', 'capacity', '{"min_cargo_tons": 100}', '{"action": "warn", "message": "Below minimum cargo threshold"}', 2),
('Maintenance Window', 'maintenance', '{"maintenance_hours": "02:00-06:00"}', '{"action": "restrict", "message": "Maintenance window active"}', 1),
('Safety Check Required', 'safety', '{"routes": ["DAR_KAPIRI"], "check_required": true}', '{"action": "require_approval", "message": "Safety check required for this route"}', 1)
ON CONFLICT DO NOTHING;
