#!/usr/bin/env python3
"""
Check system cost parameters to understand why AI chooses IDLE
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

def check_system_costs():
    """Check system configuration for cost parameters"""
    
    try:
        print("🔍 Checking System Cost Configuration...")
        print("=" * 50)
        
        # Check system configuration table
        try:
            config_query = "SELECT * FROM system_configuration LIMIT 10"
            configs = db_manager.execute_query(config_query)
            
            print("📊 System Configuration:")
            for config in configs:
                print(f"  - {config.get('config_key', 'N/A')}: {config.get('config_value', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Could not read system configuration: {e}")
        
        # Check multi_route_schedules for recent schedules
        try:
            schedule_query = """
                SELECT schedule_id, total_cargo_delivered, net_profit_zmw, 
                       fuel_cost_zmw, labor_cost_zmw, revenue_zmw
                FROM multi_route_schedules 
                ORDER BY created_at DESC 
                LIMIT 5
            """
            schedules = db_manager.execute_query(schedule_query)
            
            print("\n📋 Recent Schedules:")
            for schedule in schedules:
                print(f"  - {schedule['schedule_id']}:")
                print(f"    Cargo: {schedule['total_cargo_delivered']} tons")
                print(f"    Revenue: ZMW {schedule['revenue_zmw']}")
                print(f"    Fuel Cost: ZMW {schedule['fuel_cost_zmw']}")
                print(f"    Labor Cost: ZMW {schedule['labor_cost_zmw']}")
                print(f"    Net Profit: ZMW {schedule['net_profit_zmw']}")
                print()
        except Exception as e:
            print(f"⚠️ Could not read schedules: {e}")
        
        # Check if there are any routes defined
        try:
            route_query = """
                SELECT DISTINCT origin, destination, distance_km 
                FROM route_definitions 
                ORDER BY origin, destination
            """
            routes = db_manager.execute_query(route_query)
            
            print("🛤️ Available Routes:")
            for route in routes:
                print(f"  - {route['origin']} → {route['destination']}: {route['distance_km']} km")
        except Exception as e:
            print(f"⚠️ Could not read routes: {e}")
        
        print("\n💡 Recommendations:")
        print("1. Check if revenue per ton is too low")
        print("2. Verify fuel costs are realistic")
        print("3. Ensure route distances are correct")
        print("4. Confirm labor costs are reasonable")
        
    except Exception as e:
        print(f"❌ Error checking system: {e}")

if __name__ == "__main__":
    check_system_costs()
