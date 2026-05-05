#!/usr/bin/env python3
"""
Test database save functionality
"""

import psycopg2
import json

def test_db_save():
    """Test saving a schedule to database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        # Test data
        schedule_data = {
            'schedule_id': 'test_schedule_123',
            'num_trains': 5,
            'total_days': 7,
            'cargo_requirements': {'DAR_KAPIRI': 500, 'DAR_MBEYA': 300, 'KAPIRI_NDOLA': 200},
            'daily_actions': [[1, 2, 3, 0, 1], [2, 1, 0, 3, 2]],
            'train_assignments': [{'train_id': 'T-1', 'route': 'DAR_KAPIRI'}],
            'performance_metrics': {
                'total_cargo_delivered': 800,
                'total_profit': 1500000,
                'efficiency': 160
            },
            'cost_breakdown_zmw': {'total_cost': 1000000, 'net_profit': 500000},
            'efficiency_analysis': {
                'cargo_per_train': 160,
                'profit_per_train': 300000
            }
        }
        
        # Insert schedule
        insert_query = """
        INSERT INTO multi_route_schedules (
            schedule_id, num_trains, total_days, cargo_requirements,
            daily_actions, train_assignments, performance_metrics,
            cost_breakdown_zmw, efficiency_analysis
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (schedule_id) DO UPDATE SET
            timestamp = NOW(),
            cargo_requirements = EXCLUDED.cargo_requirements,
            daily_actions = EXCLUDED.daily_actions,
            train_assignments = EXCLUDED.train_assignments,
            performance_metrics = EXCLUDED.performance_metrics,
            cost_breakdown_zmw = EXCLUDED.cost_breakdown_zmw,
            efficiency_analysis = EXCLUDED.efficiency_analysis
        """
        
        cursor.execute(insert_query, (
            schedule_data['schedule_id'],
            schedule_data['num_trains'],
            schedule_data['total_days'],
            json.dumps(schedule_data['cargo_requirements']),
            json.dumps(schedule_data['daily_actions']),
            json.dumps(schedule_data['train_assignments']),
            json.dumps(schedule_data['performance_metrics']),
            json.dumps(schedule_data['cost_breakdown_zmw']),
            json.dumps(schedule_data['efficiency_analysis'])
        ))
        
        conn.commit()
        
        # Verify it was saved
        cursor.execute("SELECT * FROM multi_route_schedules WHERE schedule_id = %s", (schedule_data['schedule_id'],))
        result = cursor.fetchone()
        
        if result:
            print(f"SUCCESS: Schedule {schedule_data['schedule_id']} saved and retrieved from database")
            print(f"Cargo delivered: {result[8]['total_cargo_delivered']}")
        else:
            print("ERROR: Schedule not found in database after save")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_save()
