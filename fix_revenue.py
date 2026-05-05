#!/usr/bin/env python3
"""
Fix the revenue calculation issue by adding realistic revenue per ton
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager

def fix_revenue_calculation():
    """Add realistic revenue per ton to system configuration"""
    
    try:
        print("🔧 Fixing Revenue Calculation...")
        print("=" * 50)
        
        # Check if revenue configuration exists
        try:
            config_query = "SELECT * FROM system_configuration WHERE config_key LIKE '%revenue%'"
            revenue_configs = db_manager.execute_query(config_query)
            
            print("📊 Current Revenue Configuration:")
            for config in revenue_configs:
                print(f"  - {config['config_key']}: {config['config_value']}")
        except Exception as e:
            print(f"⚠️ Could not read revenue config: {e}")
        
        # Add realistic revenue per ton configuration
        revenue_configs = [
            ('revenue_per_ton_fuel', '250'),  # ZMW 250 per ton for fuel
            ('revenue_per_ton_cargo', '350'),  # ZMW 350 per ton for cargo
            ('revenue_per_ton_mixed', '300'),  # ZMW 300 per ton for mixed
            ('min_profit_margin', '0.15'),     # 15% minimum profit margin
            ('base_fuel_cost_per_liter', '5'),  # ZMW 5 per liter
            ('base_labor_cost_per_day', '300'), # ZMW 300 per day
        ]
        
        print("\n🔧 Adding Revenue Configuration...")
        for key, value in revenue_configs:
            try:
                # Check if config exists
                check_query = "SELECT id FROM system_configuration WHERE config_key = %s"
                existing = db_manager.execute_query(check_query, (key,))
                
                if existing:
                    # Update existing
                    update_query = "UPDATE system_configuration SET config_value = %s WHERE config_key = %s"
                    db_manager.execute_query(update_query, (value, key))
                    print(f"  ✅ Updated {key}: {value}")
                else:
                    # Insert new
                    insert_query = "INSERT INTO system_configuration (config_key, config_value) VALUES (%s, %s)"
                    db_manager.execute_query(insert_query, (key, value))
                    print(f"  ✅ Added {key}: {value}")
            except Exception as e:
                print(f"  ❌ Failed to set {key}: {e}")
        
        print("\n✅ Revenue Configuration Updated!")
        print("\n💡 Expected Results:")
        print("1. Revenue per ton: ZMW 250-350")
        print("2. Profit margin: 15% minimum")
        print("3. Fuel cost: ZMW 5 per liter")
        print("4. Labor cost: ZMW 300 per day")
        print("5. AI should now find profitable routes!")
        
        print("\n🚀 Try creating a new schedule now!")
        
    except Exception as e:
        print(f"❌ Error fixing revenue: {e}")

if __name__ == "__main__":
    fix_revenue_calculation()
