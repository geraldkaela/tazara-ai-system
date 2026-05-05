import psycopg2
import os
import json

def test_save_visibility():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        print(f"Connecting to {db_url}")
        
        # Connection 1: Insert parent
        conn1 = psycopg2.connect(db_url)
        conn1.autocommit = True
        cur1 = conn1.cursor()
        
        schedule_id_str = "visibility_test_" + str(os.getpid())
        print(f"Inserting parent with schedule_id={schedule_id_str}...")
        cur1.execute("""
            INSERT INTO multi_route_schedules (
                schedule_id, num_trains, total_days, cargo_requirements,
                daily_actions, train_assignments, performance_metrics,
                cost_breakdown_zmw, efficiency_analysis
            ) VALUES (%s, 1, 1, '{}', '[]', '[]', '{}', '{}', '{}')
            RETURNING id
        """, (schedule_id_str,))
        parent_id = cur1.fetchone()[0]
        print(f"Parent inserted with ID={parent_id}")
        conn1.close()
        
        # Connection 2: Insert child
        print("Opening new connection for child insert...")
        conn2 = psycopg2.connect(db_url)
        conn2.autocommit = True
        cur2 = conn2.cursor()
        
        print(f"Checking if parent ID={parent_id} is visible...")
        cur2.execute("SELECT id FROM multi_route_schedules WHERE id = %s", (parent_id,))
        if cur2.fetchone():
            print("  Parent is VISIBLE.")
        else:
            print("  Parent is NOT VISIBLE!")
            
        print(f"Attempting child insert for parent ID={parent_id}...")
        try:
            cur2.execute("""
                INSERT INTO performance_history (
                    schedule_id, metric_date, total_cargo_delivered,
                    trains_used, efficiency, net_profit_zmw
                ) VALUES (%s, CURRENT_DATE, 0, 0, 0, 0)
            """, (parent_id,))
            print("  Child insert SUCCESS.")
        except Exception as e:
            print(f"  Child insert FAILED: {e}")
            
        conn2.close()
        
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    test_save_visibility()
