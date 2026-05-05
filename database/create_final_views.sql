-- Create Views for TAZARA Dashboard (Final Version)
-- Uses actual table names that exist

-- Route Performance Summary View (using performance_history)
CREATE OR REPLACE VIEW route_performance_summary AS
SELECT 
    'DAR_KAPIRI' as route_name,
    AVG(total_cargo_delivered) as avg_efficiency,
    SUM(total_cargo_delivered) as total_cargo,
    AVG(trains_used) as avg_utilization,
    COUNT(*) as schedule_count
FROM performance_history 
WHERE schedule_id IS NOT NULL
GROUP BY 'DAR_KAPIRI'

UNION ALL

SELECT 
    'DAR_MBEYA' as route_name,
    AVG(total_cargo_delivered) as avg_efficiency,
    SUM(total_cargo_delivered) as total_cargo,
    AVG(trains_used) as avg_utilization,
    COUNT(*) as schedule_count
FROM performance_history 
WHERE schedule_id IS NOT NULL
GROUP BY 'DAR_MBEYA'

UNION ALL

SELECT 
    'KAPIRI_NDOLA' as route_name,
    AVG(total_cargo_delivered) as avg_efficiency,
    SUM(total_cargo_delivered) as total_cargo,
    AVG(trains_used) as avg_utilization,
    COUNT(*) as schedule_count
FROM performance_history 
WHERE schedule_id IS NOT NULL
GROUP BY 'KAPIRI_NDOLA'

ORDER BY avg_efficiency DESC;

-- Daily Performance Trends View (using performance_history)
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

SELECT 'Views created successfully!' as status;
