#!/usr/bin/env python3
"""
Test approval operation directly to isolate the issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def test_approval_direct():
    """Test approval operation directly"""
    
    try:
        print("Testing approval operation directly...")
        
        # Get a real schedule
        schedule_query = "SELECT schedule_id FROM multi_route_schedules LIMIT 1"
        schedules = db_manager.execute_query(schedule_query)
        
        if not schedules:
            print("❌ No schedules found")
            return False
        
        test_schedule_id = schedules[0]['schedule_id']
        print(f"Testing with schedule: {test_schedule_id}")
        
        # First, delete any existing test approval
        cleanup_query = "DELETE FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
        db_manager.execute_query(cleanup_query, (test_schedule_id,))
        
        # Test INSERT operation
        print("Testing INSERT...")
        insert_query = """
            INSERT INTO schedule_approvals 
            (schedule_id, approval_status, approver_id, approver_name, approval_level, approval_date, updated_at)
            VALUES (%s, 'approved', 'test_user', 'Test User', 1, NOW(), NOW())
        """
        
        try:
            db_manager.execute_query(insert_query, (test_schedule_id,))
            print("✓ INSERT successful")
        except Exception as e:
            print(f"❌ INSERT failed: {e}")
            return False
        
        # Verify the insert worked
        verify_query = "SELECT * FROM schedule_approvals WHERE schedule_id = %s AND approver_id = 'test_user'"
        try:
            result = db_manager.execute_query(verify_query, (test_schedule_id,))
            if result:
                print(f"✓ Verification successful: {result[0]['approval_status']}")
            else:
                print("❌ Verification failed: no record found")
                return False
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
        
        # Test UPDATE operation
        print("Testing UPDATE...")
        update_query = """
            UPDATE schedule_approvals 
            SET approval_status = 'rejected', approver_name = 'Updated User', updated_at = NOW()
            WHERE schedule_id = %s AND approver_id = 'test_user'
        """
        
        try:
            db_manager.execute_query(update_query, (test_schedule_id,))
            print("✓ UPDATE successful")
        except Exception as e:
            print(f"❌ UPDATE failed: {e}")
            return False
        
        # Verify the update worked
        try:
            result = db_manager.execute_query(verify_query, (test_schedule_id,))
            if result:
                print(f"✓ Update verification successful: {result[0]['approval_status']}")
            else:
                print("❌ Update verification failed: no record found")
                return False
        except Exception as e:
            print(f"❌ Update verification failed: {e}")
            return False
        
        # Clean up
        db_manager.execute_query(cleanup_query, (test_schedule_id,))
        print("✓ Test record cleaned up")
        
        print("\n✅ Direct approval test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_approval_direct()
