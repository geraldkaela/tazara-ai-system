#!/usr/bin/env python3
"""
Check the structure of schedule_modifications table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

def check_modification_table():
    """Check structure of schedule_modifications table"""
    
    try:
        print("Checking schedule_modifications table structure...")
        
        # Get table structure
        structure_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'schedule_modifications'
            ORDER BY ordinal_position
        """
        
        columns = db_manager.execute_query(structure_query)
        
        print("Table structure:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check if modification_date column exists
        has_modification_date = any(col['column_name'] == 'modification_date' for col in columns)
        
        if has_modification_date:
            print("\n✓ modification_date column exists")
        else:
            print("\n❌ modification_date column does NOT exist")
            
            # Add the column
            alter_query = """
                ALTER TABLE schedule_modifications 
                ADD COLUMN modification_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            """
            
            try:
                db_manager.execute_query(alter_query)
                print("✓ Added modification_date column")
            except Exception as e:
                print(f"❌ Could not add column: {e}")
                return False
        
        print("\n✅ Schedule modifications table check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        return False

if __name__ == "__main__":
    check_modification_table()
