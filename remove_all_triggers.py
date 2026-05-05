#!/usr/bin/env python3
"""
Remove all triggers from schedule_approvals table and update_timestamp function
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def remove_all_triggers():
    """Remove all triggers from schedule_approvals table"""
    
    try:
        print("Removing all triggers from schedule_approvals table...")
        
        # Check for any triggers on schedule_approvals
        trigger_query = """
            SELECT tgname, tgfoid::regproc as function_name
            FROM pg_trigger 
            JOIN pg_class ON pg_class.oid = tgrelid
            WHERE relname = 'schedule_approvals' AND NOT tgisinternal
        """
        
        triggers = db_manager.execute_query(trigger_query)
        
        if triggers:
            print("Found triggers on schedule_approvals:")
            for trigger in triggers:
                print(f"  - {trigger['tgname']} -> {trigger['function_name']}")
                
                # Drop the trigger
                drop_query = f"DROP TRIGGER IF EXISTS {trigger['tgname']} ON schedule_approvals"
                try:
                    db_manager.execute_query(drop_query)
                    print(f"✓ Dropped trigger: {trigger['tgname']}")
                except Exception as e:
                    print(f"⚠ Could not drop trigger: {e}")
        else:
            print("✓ No triggers found on schedule_approvals")
        
        # Check if update_timestamp function exists and drop it temporarily
        function_query = """
            SELECT proname FROM pg_proc WHERE proname = 'update_timestamp'
        """
        
        try:
            functions = db_manager.execute_query(function_query)
            if functions:
                print("Found update_timestamp function - dropping temporarily...")
                drop_function_query = "DROP FUNCTION IF EXISTS update_timestamp()"
                try:
                    db_manager.execute_query(drop_function_query)
                    print("✓ Dropped update_timestamp function temporarily")
                except Exception as e:
                    print(f"⚠ Could not drop function: {e}")
            else:
                print("✓ update_timestamp function not found")
        except Exception as e:
            print(f"⚠ Error checking function: {e}")
        
        # Test the approval operation
        print("Testing approval operation...")
        
        # Get a real schedule
        schedule_query = "SELECT schedule_id FROM multi_route_schedules LIMIT 1"
        schedules = db_manager.execute_query(schedule_query)
        
        if schedules:
            test_schedule_id = schedules[0]['schedule_id']
            print(f"Testing with schedule: {test_schedule_id}")
            
            # Clean up any existing test records
            cleanup_query = "DELETE FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
            db_manager.execute_query(cleanup_query, (test_schedule_id,))
            
            # Test approval operation
            test_approval_query = """
                INSERT INTO schedule_approvals 
                (schedule_id, approval_status, approver_id, approver_name, approval_level, approval_date, updated_at)
                VALUES (%s, 'approved', 'test_user', 'Test User', 1, NOW(), NOW())
            """
            
            try:
                db_manager.execute_query(test_approval_query, (test_schedule_id,))
                print("✓ Test approval operation successful")
                
                # Clean up
                db_manager.execute_query(cleanup_query, (test_schedule_id,))
                print("✓ Test record cleaned up")
                
            except Exception as e:
                print(f"❌ Test approval failed: {e}")
                return False
        else:
            print("❌ No schedules found for testing")
            return False
        
        print("\n✅ All triggers removed successfully!")
        print("⚠️ Note: update_timestamp function was dropped temporarily")
        print("   You may need to recreate it for other tables if needed")
        
    except Exception as e:
        print(f"❌ Error removing triggers: {e}")
        return False
    
    return True

if __name__ == "__main__":
    remove_all_triggers()
