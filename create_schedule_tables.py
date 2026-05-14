"""
Create Schedule Tables
Creates necessary database tables for auto-scheduling
"""

import os
import psycopg2

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

def create_schedule_tables():
    """Create tables for schedule management"""
    
    print("🚂 Creating Schedule Database Tables")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create schedules table
        print("📊 Creating schedules table...")
        schedules_query = """
        CREATE TABLE IF NOT EXISTS schedules (
            schedule_id VARCHAR(50) PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            num_trains INTEGER,
            max_days INTEGER,
            total_cargo_delivered REAL,
            efficiency_score REAL,
            total_reward REAL,
            schedule_data TEXT,
            metadata TEXT
        )
        """
        cursor.execute(schedules_query)
        print("   ✅ Schedules table created")
        
        # Create daily_assignments table
        print("📊 Creating daily_assignments table...")
        daily_assignments_query = """
        CREATE TABLE IF NOT EXISTS daily_assignments (
            id SERIAL PRIMARY KEY,
            schedule_id VARCHAR(50) REFERENCES schedules(schedule_id),
            day INTEGER,
            train_id VARCHAR(20),
            route VARCHAR(50),
            cargo_tons REAL,
            action VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(daily_assignments_query)
        print("   ✅ Daily assignments table created")

        # Train movement tracking (trip legs + optional daily_assignments column)
        schema_path = os.path.join(os.path.dirname(__file__), "database", "train_tracking_schema.sql")
        if os.path.isfile(schema_path):
            print("📊 Applying train_tracking_schema.sql...")
            with open(schema_path, "r", encoding="utf-8") as sf:
                cursor.execute(sf.read())
            print("   ✅ Train trip tracking tables ready")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 All schedule tables created successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_schedule_tables()
