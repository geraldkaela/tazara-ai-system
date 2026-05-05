-- Create Views for TAZARA Dashboard (Corrected)
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
GROUP BY 'DAR_KAPIRI'

UNION ALL

SELECT 
    'DAR_MBEYA' as route_name,
    AVG(total_cargo_delivered) as avg_efficiency,
    SUM(total_cargo_delivered) as total_cargo,
    AVG(trains_used) as avg_utilization,
    COUNT(*) as schedule_count
FROM performance_history 
GROUP BY 'DAR_MBEYA'

UNION ALL

SELECT 
    'KAPIRI_NDOLA' as route_name,
    AVG(total_cargo_delivered) as avg_efficiency,
    SUM(total_cargo_delivered) as total_cargo,
    AVG(trains_used) as avg_utilization,
    COUNT(*) as schedule_count
FROM performance_history 
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
GROUP BY DATE(created_at)
ORDER BY performance_date DESC;

-- Insert sample performance data (using performance_history)
INSERT INTO performance_history (schedule_id, metric_date, total_cargo_delivered, trains_used, efficiency, net_profit_zmw)
SELECT 
    'sample_' || id, 
    CURRENT_DATE, 
    500 + (random() * 100), 
    6, 
    85.0 + (random() * 20), 
    50000 + (random() * 10000)
FROM generate_series(1, 3) AS id;

SELECT 'Views and sample data created successfully!' as status;
