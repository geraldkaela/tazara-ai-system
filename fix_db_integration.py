#!/usr/bin/env python3
"""
Fix Database Integration Issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath('.')))

from database.db_manager import DatabaseManager

def test_sql_fix():
    db = DatabaseManager()
    
    # Test the SQL query directly
    try:
        # Test with a simple INSERT first
        query = '''
            INSERT INTO labor_costs (
                schedule_id, driver_id, train_id, route_name, work_date,
                regular_hours, overtime_hours, premium_overtime_hours, total_hours,
                base_hourly_rate, regular_cost_zmw, overtime_cost_zmw,
                premium_overtime_cost_zmw, total_labor_cost_zmw,
                skill_level, shift_type, is_weekend, route_complexity_factor,
                efficiency_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        '''
        
        params = (
            'test_schedule_001',  # 1. schedule_id
            'driver_001',        # 2. driver_id
            1,                   # 3. train_id
            'DAR_KAPIRI',        # 4. route_name
            '2026-02-09',        # 5. work_date
            8.0,                 # 6. regular_hours
            2.5,                 # 7. overtime_hours
            0.0,                 # 8. premium_overtime_hours
            10.5,                # 9. total_hours
            70.0,                # 10. base_hourly_rate
            560.0,               # 11. regular_cost_zmw
            262.5,               # 12. overtime_cost_zmw
            0.0,                 # 13. premium_overtime_cost_zmw
            822.5,               # 14. total_labor_cost_zmw
            'advanced',            # 15. skill_level
            'day',                # 16. shift_type
            False                 # 17. is_weekend
        )
        
        print(f" SQL Query has {query.count('%s')} placeholders")
        print(f" Parameters has {len(params)} items")
        
        # Execute with context manager
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                if result:
                    print(f' SQL Query Fixed: Labor cost record saved (ID: {result[0]})')
                    print(f' SQL Query Fixed: Labor cost record saved (ID: {result[0]})')
                    return True
        
        return False
        
    except Exception as e:
        print(f' SQL Query Error: {e}')
        return False

if __name__ == "__main__":
    test_sql_fix()
