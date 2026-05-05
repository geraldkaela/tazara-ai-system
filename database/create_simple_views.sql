-- Create Simple Views for TAZARA Dashboard
-- Basic views without complex string literals

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

SELECT 'Simple views created successfully!' as status;
