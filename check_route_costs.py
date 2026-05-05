#!/usr/bin/env python3
"""
Check route segments and labor costs to understand the economics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

def check_route_costs():
    """Check route segments and labor costs"""
    
    try:
        print("🔍 Checking Route Segments and Costs...")
        print("=" * 50)
        
        # Check route segments
        try:
            route_query = "SELECT * FROM route_segments LIMIT 10"
            routes = db_manager.execute_query(route_query)
            
            print("🛤️ Route Segments:")
            for route in routes:
                print(f"  - {route}")
        except Exception as e:
            print(f"⚠️ Could not read route segments: {e}")
        
        # Check labor costs
        try:
            labor_query = "SELECT * FROM labor_costs LIMIT 10"
            labor = db_manager.execute_query(labor_query)
            
            print("\n💰 Labor Costs:")
            for cost in labor:
                print(f"  - {cost}")
        except Exception as e:
            print(f"⚠️ Could not read labor costs: {e}")
        
        # Check recent schedule performance metrics
        try:
            schedule_query = """
                SELECT schedule_id, status, performance_metrics, cost_breakdown_zmw
                FROM multi_route_schedules 
                ORDER BY timestamp DESC 
                LIMIT 3
            """
            schedules = db_manager.execute_query(schedule_query)
            
            print("\n📊 Recent Schedule Performance:")
            for schedule in schedules:
                print(f"  - {schedule['schedule_id']}: {schedule['status']}")
                print(f"    Performance: {schedule['performance_metrics']}")
                print(f"    Costs: {schedule['cost_breakdown_zmw']}")
                print()
        except Exception as e:
            print(f"⚠️ Could not read schedule performance: {e}")
        
        print("\n💡 Diagnosis:")
        print("1. Check if route distances are realistic")
        print("2. Verify labor costs per day are reasonable")
        print("3. Ensure fuel costs are not too high")
        print("4. Check if revenue per ton is profitable")
        
    except Exception as e:
        print(f"❌ Error checking costs: {e}")

if __name__ == "__main__":
    check_route_costs()
