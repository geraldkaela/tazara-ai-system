-- Create Views for TAZARA Dashboard
-- Run this after tables are created

-- Route Performance Summary View
CREATE OR REPLACE VIEW route_performance_summary AS
SELECT 
    route_name,
    AVG(efficiency_score) as avg_efficiency,
    SUM(cargo_delivered) as total_cargo,
    AVG(train_utilization) as avg_utilization,
    COUNT(*) as schedule_count
FROM route_performance 
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
GROUP BY DATE(created_at)
ORDER BY performance_date DESC;

-- Insert some sample data for testing (optional)
INSERT INTO route_performance (route_name, cargo_delivered, trains_assigned, efficiency_score, revenue_zmw)
SELECT 
    'DAR_KAPIRI', 
    85.5, 
    6, 
    85.5,
    85000
WHERE NOT EXISTS (SELECT 1 FROM route_performance LIMIT 1);

INSERT INTO route_performance (route_name, cargo_delivered, trains_assigned, efficiency_score, revenue_zmw)
SELECT 
    'DAR_MBEYA', 
    75.2, 
    5, 
    75.2,
    75000
WHERE NOT EXISTS (SELECT 1 FROM route_performance WHERE route_name = 'DAR_MBEYA' LIMIT 1);

INSERT INTO route_performance (route_name, cargo_delivered, trains_assigned, efficiency_score, revenue_zmw)
SELECT 
    'KAPIRI_NDOLA', 
    90.1, 
    4, 
    90.1,
    90000
WHERE NOT EXISTS (SELECT 1 FROM route_performance WHERE route_name = 'KAPIRI_NDOLA' LIMIT 1);

SELECT 'Views and sample data created successfully!' as status;
