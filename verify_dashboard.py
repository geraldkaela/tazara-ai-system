"""Quick verification of analytics dashboard module."""
import sys
from pathlib import Path

# Test import
try:
    from api.routes.analytics_dashboard import DashboardData, router
    print("✅ analytics_dashboard module imports successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test database connection
try:
    risk_data = DashboardData.get_risk_trends(days=90)
    print(f"✅ Risk trends retrieved: {risk_data.get('total_days', 0)} days")
except Exception as e:
    print(f"❌ Error retrieving risk trends: {e}")
    sys.exit(1)

# Test fragility data
try:
    frag_data = DashboardData.get_fragility_trends(days=90)
    print(f"✅ Fragility trends retrieved: {frag_data.get('total_days', 0)} days")
except Exception as e:
    print(f"❌ Error retrieving fragility trends: {e}")
    sys.exit(1)

# Test bottleneck data
try:
    bn_data = DashboardData.get_bottleneck_analysis()
    print(f"✅ Bottleneck analysis retrieved: {bn_data.get('total_bottlenecks', 0)} bottlenecks")
except Exception as e:
    print(f"❌ Error retrieving bottleneck data: {e}")
    sys.exit(1)

# Test what-if scenarios
try:
    scenario_data = DashboardData.get_what_if_scenarios()
    print(f"✅ What-if scenarios retrieved: {scenario_data.get('total_scenarios', 0)} scenarios")
except Exception as e:
    print(f"❌ Error retrieving scenarios: {e}")
    sys.exit(1)

# Test model performance
try:
    model_data = DashboardData.get_model_performance()
    print(f"✅ Model performance retrieved: {len(model_data.get('models', []))} models")
except Exception as e:
    print(f"❌ Error retrieving model data: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ ANALYTICS DASHBOARD VERIFICATION COMPLETE")
print("="*70)
print("\nDashboard endpoints ready:")
print("  GET /api/dashboard/overview          - Complete overview")
print("  GET /api/dashboard/risk              - Risk analysis (days: 90)")
print("  GET /api/dashboard/fragility         - Fragility analysis (days: 90)")
print("  GET /api/dashboard/bottlenecks       - Bottleneck periods")
print("  GET /api/dashboard/scenarios         - What-if scenarios")
print("  GET /api/dashboard/models            - Model performance")
print("  GET /api/dashboard/health            - Database health check")
print("\n" + "="*70 + "\n")

sys.exit(0)
