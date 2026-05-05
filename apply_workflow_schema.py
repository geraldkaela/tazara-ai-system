"""
Apply Workflow Enhancement Schema to TAZARA Database
This script adds tables for approval workflow, customer orders, and schedule modifications
"""

import psycopg2
import os
from datetime import datetime

# Database connection
DB_URL = "postgresql://tazara:tazara123@localhost:5432/tazara_multi_route"

def apply_schema():
    """Apply the workflow schema to the database"""
    try:
        # Connect to database
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🚀 Applying TAZARA Workflow Enhancement Schema...")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Read and execute schema file
        schema_file = os.path.join(os.path.dirname(__file__), "database", "workflow_schema.sql")
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        executed_count = 0
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                    executed_count += 1
                    print(f"✅ Executed statement {executed_count}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"⚠️  Statement {executed_count + 1} skipped (object already exists)")
                    else:
                        print(f"❌ Error in statement {executed_count + 1}: {e}")
        
        print("=" * 60)
        print(f"🎉 Workflow schema application complete!")
        print(f"📊 {executed_count} statements executed successfully")
        
        # Verify tables were created
        print("\n🔍 Verifying table creation...")
        tables_to_check = [
            'customer_orders',
            'schedule_approvals', 
            'schedule_modifications',
            'train_cancellations',
            'scheduling_priorities',
            'scheduling_rules'
        ]
        
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
        
        print("\n" + "=" * 60)
        print("🚀 TAZARA Workflow Enhancement is ready!")
        print("📋 New features available:")
        print("   • Customer order management")
        print("   • Schedule approval workflow")
        print("   • Schedule modification tracking")
        print("   • Train cancellation management")
        print("   • Scheduling priorities configuration")
        print("   • Rules and constraints engine")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    apply_schema()
