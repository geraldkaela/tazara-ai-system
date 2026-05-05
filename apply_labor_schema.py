#!/usr/bin/env python3
"""
Apply labor cost tracking schema to database
"""

import psycopg2
import os

def apply_labor_schema():
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        # Read and execute schema file
        with open('database/labor_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('labor_costs', 'optimization_events', 'driver_skills', 'shift_assignments', 'optimization_recommendations', 'labor_performance_trends')
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Labor schema applied successfully!")
        print(f"📊 Created {len(tables)} new tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM driver_skills")
        driver_count = cursor.fetchone()[0]
        print(f"👥 Sample driver skills inserted: {driver_count} drivers")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error applying labor schema: {e}")
        return False

if __name__ == "__main__":
    apply_labor_schema()
