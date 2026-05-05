#!/usr/bin/env python3
"""
Initialize workflow tables in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager

def init_workflow_tables():
    """Initialize workflow tables"""
    
    # Read the workflow schema
    with open('database/workflow_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    try:
        print("Creating workflow tables...")
        
        # Split the SQL into individual statements
        statements = schema_sql.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    db_manager.execute_query(statement)
                    print(f"✓ Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"⚠ Error executing statement: {e}")
                    print(f"   Statement: {statement[:100]}...")
        
        print("\n✅ Workflow tables initialized successfully!")
        
        # Test the tables
        print("\n🧪 Testing workflow tables...")
        
        # Test customer orders table
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM customer_orders")
        print(f"📋 Customer orders table: {result[0]['count']} records")
        
        # Test schedule approvals table
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM schedule_approvals")
        print(f"✅ Schedule approvals table: {result[0]['count']} records")
        
        # Test schedule modifications table
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM schedule_modifications")
        print(f"📝 Schedule modifications table: {result[0]['count']} records")
        
        # Test scheduling priorities
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM scheduling_priorities")
        print(f"⚖️ Scheduling priorities table: {result[0]['count']} records")
        
        print("\n🎉 All workflow tables are ready!")
        
    except Exception as e:
        print(f"❌ Error initializing workflow tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    init_workflow_tables()
