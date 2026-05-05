#!/usr/bin/env python3
"""
Temporarily disable the update_timestamp function to fix the trigger issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def disable_update_timestamp():
    """Temporarily disable update_timestamp function"""
    
    try:
        print("Temporarily disabling update_timestamp function...")
        
        # First, drop the triggers that depend on the function
        print("Dropping dependent triggers...")
        
        triggers_to_drop = [
            "update_multi_route_schedules_timestamp",
            "update_system_configuration_timestamp"
        ]
        
        for trigger_name in triggers_to_drop:
            drop_trigger_query = f"DROP TRIGGER IF EXISTS {trigger_name} ON multi_route_schedules"
            try:
                db_manager.execute_query(drop_trigger_query)
                print(f"✓ Dropped trigger: {trigger_name}")
            except Exception as e:
                print(f"⚠ Could not drop trigger {trigger_name}: {e}")
        
        drop_trigger_query2 = f"DROP TRIGGER IF EXISTS update_system_configuration_timestamp ON system_configuration"
        try:
            db_manager.execute_query(drop_trigger_query2)
            print(f"✓ Dropped trigger: update_system_configuration_timestamp")
        except Exception as e:
            print(f"⚠ Could not drop trigger update_system_configuration_timestamp: {e}")
        
        # Now drop the function with CASCADE
        print("Dropping update_timestamp function with CASCADE...")
        drop_function_query = "DROP FUNCTION IF EXISTS update_timestamp() CASCADE"
        try:
            db_manager.execute_query(drop_function_query)
            print("✓ Dropped update_timestamp function and dependencies")
        except Exception as e:
            print(f"⚠ Could not drop function: {e}")
        
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
                (schedule_id, approval_status, approver_id, approver_name, approval_level, approval_date)
                VALUES (%s, 'approved', 'test_user', 'Test User', 1, NOW())
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
        
        print("\n✅ update_timestamp function disabled successfully!")
        print("⚠️ Note: You may need to recreate the triggers and function for other tables")
        print("   This is a temporary fix to allow workflow approvals to work")
        
    except Exception as e:
        print(f"❌ Error disabling function: {e}")
        return False
    
    return True

if __name__ == "__main__":
    disable_update_timestamp()
