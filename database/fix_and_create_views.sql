-- Fix performance_history table and create proper views

-- Step 1: Add route_name column to performance_history
ALTER TABLE performance_history ADD COLUMN IF NOT EXISTS route_name VARCHAR(50);

-- Step 2: Update existing records with default route
UPDATE performance_history 
SET route_name = 'DAR_KAPIRI' 
WHERE route_name IS NULL;

-- Step 3: Create proper views using route_name

-- Route Performance Summary View
CREATE OR REPLACE VIEW route_performance_summary AS
SELECT 
    route_name,
    AVG(total_cargo_delivered) as avg_efficiency,
    SUM(total_cargo_delivered) as total_cargo,
    AVG(trains_used) as avg_utilization,
    COUNT(*) as schedule_count
FROM performance_history 
WHERE schedule_id IS NOT NULL
GROUP BY route_name
ORDER BY avg_efficiency DESC;

-- Daily Performance Trends View
CREATE OR REPLACE VIEW daily_performance_trends AS
SELECT 
    DATE(created_at) as performance_date,
    AVG(total_cargo_delivered) as avg_cargo,
    AVG(trains_used) as avg_trains,
    AVG(efficiency) as avg_efficiency,
    SUM(net_profit_zmw) as total_profit
FROM performance_history 
WHERE schedule_id IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY performance_date DESC;

SELECT 'Table fixed and views created successfully!' as status;
