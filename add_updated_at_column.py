#!/usr/bin/env python3
"""
Add updated_at column to schedule_approvals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def add_updated_at_column():
    """Add updated_at column to schedule_approvals table"""
    
    try:
        print("Adding updated_at column to schedule_approvals table...")
        
        # Add the updated_at column
        alter_query = """
            ALTER TABLE schedule_approvals 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        """
        
        try:
            db_manager.execute_query(alter_query)
            print("✓ Added updated_at column to schedule_approvals")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("✓ updated_at column already exists")
            else:
                print(f"⚠ Could not add column: {e}")
                return False
        
        # Test the table
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM schedule_approvals")
        print(f"📋 Schedule approvals table: {result[0]['count']} records")
        
        # Test an approval operation
        print("Testing approval operation...")
        
        # Get a real schedule
        schedule_query = "SELECT schedule_id FROM multi_route_schedules LIMIT 1"
        schedules = db_manager.execute_query(schedule_query)
        
        if schedules:
            test_schedule_id = schedules[0]['schedule_id']
            print(f"Testing with schedule: {test_schedule_id}")
            
            # Test the approval insert
            test_approval_query = """
                INSERT INTO schedule_approvals 
                (schedule_id, approval_status, approver_id, approver_name, approval_level)
                VALUES (%s, 'approved', 'test_user', 'Test User', 1)
                ON CONFLICT (schedule_id) DO UPDATE SET
                    approval_status = EXCLUDED.approval_status,
                    approver_id = EXCLUDED.approver_id,
                    approver_name = EXCLUDED.approver_name,
                    approval_date = NOW(),
                    updated_at = NOW()
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
        
        print("\n✅ updated_at column added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_updated_at_column()
