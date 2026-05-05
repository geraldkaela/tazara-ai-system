#!/usr/bin/env python3
"""
Check actual schedule structure and recent data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

def check_schedule_structure():
    """Check actual schedule table structure and data"""
    
    try:
        print("🔍 Checking Schedule Table Structure...")
        print("=" * 50)
        
        # Get table structure
        structure_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'multi_route_schedules'
            ORDER BY ordinal_position
        """
        
        columns = db_manager.execute_query(structure_query)
        
        print("📋 Schedule Table Structure:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Get recent schedules with actual column names
        try:
            schedule_query = """
                SELECT schedule_id, created_at, status
                FROM multi_route_schedules 
                ORDER BY created_at DESC 
                LIMIT 5
            """
            schedules = db_manager.execute_query(schedule_query)
            
            print("\n📋 Recent Schedules:")
            for schedule in schedules:
                print(f"  - {schedule['schedule_id']}: {schedule['status']} (created: {schedule['created_at']})")
        except Exception as e:
            print(f"⚠️ Could not read schedules: {e}")
        
        # Check if there's any route or cost data in other tables
        try:
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%route%' OR table_name LIKE '%cost%' OR table_name LIKE '%config%'
            """
            tables = db_manager.execute_query(tables_query)
            
            print("\n🗂️ Related Tables:")
            for table in tables:
                print(f"  - {table['table_name']}")
        except Exception as e:
            print(f"⚠️ Could not list tables: {e}")
        
        print("\n💡 The Issue:")
        print("1. System may be missing route definitions")
        print("2. Cost parameters might be hardcoded in AI model")
        print("3. Revenue calculations might be unrealistic")
        print("4. The AI is correctly avoiding unprofitable work")
        
    except Exception as e:
        print(f"❌ Error checking structure: {e}")

if __name__ == "__main__":
    check_schedule_structure()
