-- Check table structure for performance_history
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'performance_history' 
AND table_schema = 'public'
ORDER BY ordinal_position;
