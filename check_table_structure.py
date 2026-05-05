#!/usr/bin/env python3
"""
Check the actual structure of schedule_approvals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def check_table_structure():
    """Check the structure of schedule_approvals table"""
    
    try:
        print("Checking schedule_approvals table structure...")
        
        # Get table structure
        structure_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'schedule_approvals'
            ORDER BY ordinal_position
        """
        
        columns = db_manager.execute_query(structure_query)
        
        print("Table structure:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check if updated_at column exists
        has_updated_at = any(col['column_name'] == 'updated_at' for col in columns)
        
        if has_updated_at:
            print("\n✓ updated_at column exists")
        else:
            print("\n❌ updated_at column does NOT exist")
            
            # Add the column
            print("Adding updated_at column...")
            alter_query = """
                ALTER TABLE schedule_approvals 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            """
            
            try:
                db_manager.execute_query(alter_query)
                print("✓ Added updated_at column")
            except Exception as e:
                print(f"❌ Could not add column: {e}")
                return False
        
        # Check triggers
        print("\nChecking triggers on schedule_approvals...")
        trigger_query = """
            SELECT tgname, tgfoid::regproc as function_name
            FROM pg_trigger 
            JOIN pg_class ON pg_class.oid = tgrelid
            WHERE relname = 'schedule_approvals' AND NOT tgisinternal
        """
        
        triggers = db_manager.execute_query(trigger_query)
        
        if triggers:
            print("Found triggers:")
            for trigger in triggers:
                print(f"  - {trigger['tgname']} -> {trigger['function_name']}")
                
                # Drop problematic triggers
                if 'update_timestamp' in trigger['function_name'].lower():
                    print(f"Dropping problematic trigger: {trigger['tgname']}")
                    drop_query = f"DROP TRIGGER IF EXISTS {trigger['tgname']} ON schedule_approvals"
                    try:
                        db_manager.execute_query(drop_query)
                        print(f"✓ Dropped trigger: {trigger['tgname']}")
                    except Exception as e:
                        print(f"⚠ Could not drop trigger: {e}")
        else:
            print("✓ No triggers found on schedule_approvals")
        
        print("\n✅ Table structure check completed!")
        
    except Exception as e:
        print(f"❌ Error checking structure: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_table_structure()
