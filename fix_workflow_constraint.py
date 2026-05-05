#!/usr/bin/env python3
"""
Fix the unique constraint on schedule_approvals table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def fix_schedule_approvals_constraint():
    """Add unique constraint to schedule_approvals table"""
    
    try:
        print("Adding unique constraint to schedule_approvals table...")
        
        # First, remove any duplicate schedule_id entries
        cleanup_query = """
            DELETE FROM schedule_approvals 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM schedule_approvals 
                GROUP BY schedule_id
            )
        """
        
        try:
            db_manager.execute_query(cleanup_query)
            print("✓ Cleaned up duplicate schedule_id entries")
        except Exception as e:
            print(f"⚠ Cleanup not needed or failed: {e}")
        
        # Add the unique constraint
        constraint_query = """
            ALTER TABLE schedule_approvals 
            ADD CONSTRAINT schedule_approvals_schedule_id_unique 
            UNIQUE (schedule_id)
        """
        
        try:
            db_manager.execute_query(constraint_query)
            print("✓ Added unique constraint to schedule_id")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("✓ Unique constraint already exists")
            else:
                print(f"⚠ Could not add constraint: {e}")
                # Try alternative approach
                print("Trying alternative approach...")
                alt_query = """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_schedule_approvals_schedule_id_unique 
                    ON schedule_approvals(schedule_id)
                """
                db_manager.execute_query(alt_query)
                print("✓ Created unique index instead")
        
        # Test the table
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM schedule_approvals")
        print(f"📋 Schedule approvals table: {result[0]['count']} records")
        
        print("\n✅ Schedule approvals constraint fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing constraint: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_schedule_approvals_constraint()
