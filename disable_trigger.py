#!/usr/bin/env python3
"""
Disable the problematic update_timestamp trigger for schedule_approvals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def disable_problematic_trigger():
    """Disable update_timestamp trigger for schedule_approvals table"""
    
    try:
        print("Disabling update_timestamp trigger for schedule_approvals...")
        
        # Check if the trigger function exists
        check_function_query = """
            SELECT proname FROM pg_proc WHERE proname = 'update_timestamp'
        """
        
        try:
            functions = db_manager.execute_query(check_function_query)
            if functions:
                print("✓ Found update_timestamp function")
                
                # Check for triggers on schedule_approvals table
                check_trigger_query = """
                    SELECT tgname, tgfoid::regproc as function_name
                    FROM pg_trigger 
                    JOIN pg_class ON pg_class.oid = tgrelid
                    WHERE relname = 'schedule_approvals' AND NOT tgisinternal
                """
                
                triggers = db_manager.execute_query(check_trigger_query)
                if triggers:
                    print(f"Found triggers on schedule_approvals: {triggers}")
                    
                    for trigger in triggers:
                        trigger_name = trigger['tgname']
                        function_name = trigger['function_name']
                        
                        if 'update_timestamp' in function_name.lower():
                            print(f"Dropping trigger: {trigger_name}")
                            drop_query = f"DROP TRIGGER IF EXISTS {trigger_name} ON schedule_approvals"
                            try:
                                db_manager.execute_query(drop_query)
                                print(f"✓ Dropped trigger: {trigger_name}")
                            except Exception as e:
                                print(f"⚠ Could not drop trigger: {e}")
                else:
                    print("✓ No problematic triggers found on schedule_approvals")
            else:
                print("✓ update_timestamp function not found")
        except Exception as e:
            print(f"⚠ Error checking function: {e}")
        
        # Alternative: Create a custom trigger function that doesn't use updated_at
        print("Creating custom trigger function for schedule_approvals...")
        create_function_query = """
            CREATE OR REPLACE FUNCTION update_schedule_approvals_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Only set approval_date, don't try to set updated_at
                NEW.approval_date = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """
        
        try:
            db_manager.execute_query(create_function_query)
            print("✓ Created custom trigger function")
        except Exception as e:
            print(f"⚠ Could not create custom function: {e}")
        
        # Test the approval operation directly
        print("Testing approval operation...")
        
        # Get a real schedule
        schedule_query = "SELECT schedule_id FROM multi_route_schedules LIMIT 1"
        schedules = db_manager.execute_query(schedule_query)
        
        if schedules:
            test_schedule_id = schedules[0]['schedule_id']
            print(f"Testing with schedule: {test_schedule_id}")
            
            # Test the approval insert directly
            test_approval_query = """
                INSERT INTO schedule_approvals 
                (schedule_id, approval_status, approver_id, approver_name, approval_level, approval_date)
                VALUES (%s, 'approved', 'test_user', 'Test User', 1, NOW())
                ON CONFLICT (schedule_id) DO UPDATE SET
                    approval_status = EXCLUDED.approval_status,
                    approver_id = EXCLUDED.approver_id,
                    approver_name = EXCLUDED.approver_name,
                    approval_date = NOW()
            """
            
            try:
                db_manager.execute_query(test_approval_query, (test_schedule_id,))
                print("✓ Test approval operation successful")
                
                # Clean up
                cleanup_query = "DELETE FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
                db_manager.execute_query(cleanup_query, (test_schedule_id,))
                print("✓ Test record cleaned up")
                
            except Exception as e:
                print(f"❌ Test approval failed: {e}")
                return False
        else:
            print("❌ No schedules found for testing")
            return False
        
        print("\n✅ Trigger issue resolved successfully!")
        
    except Exception as e:
        print(f"❌ Error disabling trigger: {e}")
        return False
    
    return True

if __name__ == "__main__":
    disable_problematic_trigger()
