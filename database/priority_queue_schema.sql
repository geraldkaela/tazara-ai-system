-- PRIORITY QUEUE DATABASE SCHEMA
-- For TAZARA AI Priority Auto-Scheduling System

-- Priority Queue Table
CREATE TABLE IF NOT EXISTS priority_queue (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    customer_name VARCHAR(100) NOT NULL,
    customer_tier VARCHAR(20) NOT NULL, -- platinum, gold, silver, bronze
    cargo_type VARCHAR(50) NOT NULL,
    cargo_weight FLOAT NOT NULL,
    cargo_value DECIMAL(12,2),
    route VARCHAR(50) NOT NULL,
    priority_score FLOAT NOT NULL, -- 0-100 score
    urgency_level VARCHAR(20) NOT NULL, -- emergency, urgent, normal
    delivery_deadline TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending', -- pending, queued, scheduled, completed
    scheduled_at TIMESTAMP,
    schedule_id VARCHAR(50),
    priority_factors JSONB, -- Store detailed priority factors
    metadata JSONB -- Additional order metadata
);

-- Priority Queue Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_priority_queue_score ON priority_queue (priority_score DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_priority_queue_status ON priority_queue (status, priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_priority_queue_deadline ON priority_queue (delivery_deadline, priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_priority_queue_order ON priority_queue (order_id);

-- Priority Scheduling History
CREATE TABLE IF NOT EXISTS priority_scheduling_history (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(50) NOT NULL,
    order_ids TEXT[] NOT NULL, -- Array of order IDs in batch
    priority_scores FLOAT[] NOT NULL, -- Array of priority scores
    total_cargo_weight FLOAT NOT NULL,
    total_trains_used INTEGER NOT NULL,
    scheduling_duration_ms INTEGER, -- Time taken to schedule
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'in_progress', -- in_progress, completed, failed
    performance_metrics JSONB,
    cost_breakdown JSONB,
    notification_sent BOOLEAN DEFAULT FALSE
);

-- Priority Queue Configuration
CREATE TABLE IF NOT EXISTS priority_queue_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO priority_queue_config (config_key, config_value) VALUES
('priority_threshold', '75.0'),
('check_interval_seconds', '300'),
('max_queue_size', '50'),
('auto_scheduling_enabled', 'true'),
('notification_enabled', 'true'),
('max_trains_per_batch', '12')
ON CONFLICT (config_key) DO NOTHING;

-- Priority Queue Statistics View
CREATE OR REPLACE VIEW priority_queue_stats AS
SELECT 
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
    COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued_orders,
    COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_orders,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
    AVG(priority_score) as avg_priority_score,
    MAX(priority_score) as max_priority_score,
    MIN(priority_score) as min_priority_score,
    COUNT(CASE WHEN urgency_level = 'emergency' THEN 1 END) as emergency_orders,
    COUNT(CASE WHEN urgency_level = 'urgent' THEN 1 END) as urgent_orders,
    COUNT(CASE WHEN customer_tier = 'platinum' THEN 1 END) as platinum_orders,
    COUNT(CASE WHEN delivery_deadline < CURRENT_TIMESTAMP + INTERVAL '24 hours' THEN 1 END) as urgent_deadline_orders
FROM priority_queue
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';

-- Function to add order to priority queue
CREATE OR REPLACE FUNCTION add_to_priority_queue(
    p_order_id VARCHAR(50),
    p_customer_name VARCHAR(100),
    p_customer_tier VARCHAR(20),
    p_cargo_type VARCHAR(50),
    p_cargo_weight FLOAT,
    p_cargo_value DECIMAL(12,2),
    p_route VARCHAR(50),
    p_priority_score FLOAT,
    p_urgency_level VARCHAR(20),
    p_delivery_deadline TIMESTAMP,
    p_priority_factors JSONB,
    p_metadata JSONB DEFAULT '{}'
) RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO priority_queue (
        order_id, customer_name, customer_tier, cargo_type, cargo_weight,
        cargo_value, route, priority_score, urgency_level, delivery_deadline,
        priority_factors, metadata
    ) VALUES (
        p_order_id, p_customer_name, p_customer_tier, p_cargo_type, p_cargo_weight,
        p_cargo_value, p_route, p_priority_score, p_urgency_level, p_delivery_deadline,
        p_priority_factors, p_metadata
    ) ON CONFLICT (order_id) DO UPDATE SET
        priority_score = p_priority_score,
        status = 'pending',
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error adding order to priority queue: %', SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to get next batch of high-priority orders
CREATE OR REPLACE FUNCTION get_priority_batch(
    p_max_trains INTEGER DEFAULT 12,
    p_max_cargo FLOAT DEFAULT 12000
) RETURNS TABLE (
    order_ids TEXT[],
    priority_scores FLOAT[],
    total_cargo_weight FLOAT,
    route_requirements JSONB,
    deadline_earliest TIMESTAMP,
    deadline_latest TIMESTAMP
) AS $$
DECLARE
    batch_orders RECORD;
    remaining_trains INTEGER;
    total_weight FLOAT;
    order_list TEXT[];
    score_list FLOAT[];
    cargo_by_route JSONB;
BEGIN
    -- Initialize
    remaining_trains := p_max_trains;
    total_weight := 0;
    order_list := '{}';
    score_list := '{}';
    cargo_by_route := '{}';
    
    -- Get orders that can be handled with available trains
    FOR batch_orders IN 
        SELECT order_id, priority_score, cargo_weight, route, delivery_deadline
        FROM priority_queue
        WHERE status = 'pending'
        AND priority_score >= (SELECT CAST(config_value AS FLOAT) FROM priority_queue_config WHERE config_key = 'priority_threshold')
        ORDER BY priority_score DESC, delivery_deadline ASC
        LIMIT p_max_trains
    LOOP
        -- Check if we can handle this order
        IF remaining_trains > 0 AND total_weight + batch_orders.cargo_weight <= p_max_cargo THEN
            order_list := array_append(order_list, batch_orders.order_id);
            score_list := array_append(score_list, batch_orders.priority_score);
            total_weight := total_weight + batch_orders.cargo_weight;
            remaining_trains := remaining_trains - 1;
            
            -- Aggregate cargo by route
            cargo_by_route := cargo_by_route || 
                COALESCE(jsonb_build_object(batch_orders.route, batch_orders.cargo_weight), '{}'::jsonb);
        END IF;
    END LOOP;
    
    -- Update status of selected orders
    UPDATE priority_queue 
    SET status = 'queued', scheduled_at = CURRENT_TIMESTAMP
    WHERE order_id = ANY(order_list);
    
    -- Return results
    RETURN QUERY SELECT 
        order_list, score_list, total_weight, cargo_by_route,
        MIN(delivery_deadline) FILTER (WHERE order_id = ANY(order_list)),
        MAX(delivery_deadline) FILTER (WHERE order_id = ANY(order_list))
    FROM priority_queue
    WHERE order_id = ANY(order_list);
END;
$$ LANGUAGE plpgsql;
