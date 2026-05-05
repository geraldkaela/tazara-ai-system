import psycopg2
import os

DB_URL = "postgresql://tazara:tazara123@localhost:5432/tazara_multi_route"

def check_tables():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Check for new workflow tables
        tables_to_check = [
            'customer_orders',
            'schedule_approvals', 
            'schedule_modifications',
            'train_cancellations',
            'scheduling_priorities',
            'scheduling_rules'
        ]
        
        print("🔍 Checking workflow tables...")
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"{status} {table}")
        
        # Check default data
        print("\n📋 Checking default data...")
        
        cursor.execute("SELECT COUNT(*) FROM scheduling_priorities")
        priority_count = cursor.fetchone()[0]
        print(f"🎯 Scheduling priorities: {priority_count} records")
        
        cursor.execute("SELECT COUNT(*) FROM scheduling_rules")
        rule_count = cursor.fetchone()[0]
        print(f"📜 Scheduling rules: {rule_count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_tables()
