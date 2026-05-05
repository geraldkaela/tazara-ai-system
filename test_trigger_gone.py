#!/usr/bin/env python3
"""
Test if the update_timestamp trigger is gone
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def test_trigger_gone():
    """Test if the trigger is gone"""
    
    try:
        print("Testing if update_timestamp trigger is gone...")
        
        # Check if function exists
        function_query = """
            SELECT proname FROM pg_proc WHERE proname = 'update_timestamp'
        """
        
        try:
            functions = db_manager.execute_query(function_query)
            if functions:
                print("❌ update_timestamp function still exists")
                return False
            else:
                print("✓ update_timestamp function is gone")
        except Exception as e:
            print(f"⚠ Error checking function: {e}")
        
        # Test approval operation
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
                print("✓ Test approval operation successful - no trigger errors!")
                
                # Verify the record was created
                verify_query = "SELECT * FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
                result = db_manager.execute_query(verify_query, (test_schedule_id,))
                
                if result:
                    print(f"✓ Record verified: {result[0]['approval_status']}")
                else:
                    print("❌ Record not found")
                    return False
                
                # Clean up
                db_manager.execute_query(cleanup_query, (test_schedule_id,))
                print("✓ Test record cleaned up")
                
            except Exception as e:
                if "updated_at" in str(e):
                    print(f"❌ Trigger still active: {e}")
                    return False
                elif "no results to fetch" in str(e):
                    print("✓ Test approval operation successful - no trigger errors!")
                    
                    # Verify the record was created
                    verify_query = "SELECT * FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
                    result = db_manager.execute_query(verify_query, (test_schedule_id,))
                    
                    if result:
                        print(f"✓ Record verified: {result[0]['approval_status']}")
                        
                        # Clean up
                        db_manager.execute_query(cleanup_query, (test_schedule_id,))
                        print("✓ Test record cleaned up")
                    else:
                        print("❌ Record not found")
                        return False
                else:
                    print(f"⚠ Other error: {e}")
                    return False
        else:
            print("❌ No schedules found for testing")
            return False
        
        print("\n✅ Trigger is gone! Workflow approvals should work now!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing: {e}")
        return False

if __name__ == "__main__":
    test_trigger_gone()
