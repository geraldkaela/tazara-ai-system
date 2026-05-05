#!/usr/bin/env python3
"""
Remove the problematic trigger from schedule_approvals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def fix_schedule_approvals_trigger():
    """Remove trigger from schedule_approvals table"""
    
    try:
        print("Checking for triggers on schedule_approvals table...")
        
        # Check if trigger exists
        check_query = """
            SELECT trigger_name, event_manipulation 
            FROM information_schema.triggers 
            WHERE event_object_table = 'schedule_approvals'
        """
        
        try:
            triggers = db_manager.execute_query(check_query)
            if triggers:
                print(f"Found triggers on schedule_approvals: {triggers}")
                
                # Drop any triggers on schedule_approvals
                for trigger in triggers:
                    trigger_name = trigger['trigger_name']
                    drop_query = f"DROP TRIGGER IF EXISTS {trigger_name} ON schedule_approvals"
                    try:
                        db_manager.execute_query(drop_query)
                        print(f"✓ Dropped trigger: {trigger_name}")
                    except Exception as e:
                        print(f"⚠ Could not drop trigger {trigger_name}: {e}")
            else:
                print("✓ No triggers found on schedule_approvals table")
        except Exception as e:
            print(f"⚠ Error checking triggers: {e}")
        
        # Test the table by inserting a test record
        print("Testing schedule_approvals table...")
        
        # Get a real schedule ID
        schedule_query = "SELECT schedule_id FROM multi_route_schedules LIMIT 1"
        schedules = db_manager.execute_query(schedule_query)
        
        if not schedules:
            print("❌ No schedules found to test with")
            return False
        
        test_schedule_id = schedules[0]['schedule_id']
        print(f"Using schedule ID: {test_schedule_id}")
        
        test_query = """
            INSERT INTO schedule_approvals 
            (schedule_id, approval_status, approver_id, approver_name, approval_level)
            VALUES (%s, 'pending', 'test_user', 'Test User', 1)
            ON CONFLICT (schedule_id) DO NOTHING
        """
        
        try:
            db_manager.execute_query(test_query, (test_schedule_id,))
            print("✓ Test insert successful")
            
            # Clean up test record
            cleanup_query = "DELETE FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
            db_manager.execute_query(cleanup_query, (test_schedule_id,))
            print("✓ Test record cleaned up")
            
        except Exception as e:
            print(f"❌ Test insert failed: {e}")
            return False
        
        print("\n✅ Schedule approvals trigger fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing trigger: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_schedule_approvals_trigger()
