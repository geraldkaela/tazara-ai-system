#!/usr/bin/env python3
"""
Debug Alerts Display Issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

def debug_alerts_api():
    """Debug the alerts API responses"""
    print('🔍 DEBUGGING ALERTS DISPLAY ISSUE')
    print('=' * 50)
    
    # Import the alerts routes to test directly
    try:
        sys.path.append('api')
        from routes.alerts import alerts_db, schedules_db, get_alerts, get_schedules, get_alerts_summary
        
        print('\n📊 STEP 1: Checking direct API function calls')
        
        # Test get_alerts
        alerts = get_alerts()
        print(f'   get_alerts() returns: {len(alerts)} alerts')
        for i, alert in enumerate(alerts[:3]):
            print(f'     {i+1}. {alert.id} - {alert.severity} - {alert.message[:50]}...')
        
        # Test get_schedules  
        schedules = get_schedules()
        print(f'   get_schedules() returns: {len(schedules)} schedules')
        for i, schedule in enumerate(schedules[:3]):
            print(f'     {i+1}. {schedule.id} - {schedule.status} - {schedule.schedule_type}')
        
        # Test get_alerts_summary
        summary = get_alerts_summary()
        print(f'   get_alerts_summary() returns:')
        print(f'     Alerts: {summary.get("alerts", {})}')
        print(f'     Schedules: {summary.get("schedules", {})}')
        print(f'     Performance: {summary.get("performance", {})}')
        
    except Exception as e:
        print(f'   ❌ Error testing API functions: {e}')
        import traceback
        traceback.print_exc()
    
    print('\n🔧 STEP 2: Checking data structure issues')
    
    # Check if alerts have the expected structure
    if 'alerts' in locals() and alerts:
        print(f'   First alert structure:')
        alert = alerts[0]
        print(f'     ID: {getattr(alert, "id", "N/A")}')
        print(f'     Severity: {getattr(alert, "severity", "N/A")}')
        print(f'     Message: {getattr(alert, "message", "N/A")}')
        print(f'     Schedule ID: {getattr(alert, "schedule_id", "N/A")}')
        print(f'     Timestamp: {getattr(alert, "timestamp", "N/A")}')
    
    # Check if schedules have the expected structure
    if 'schedules' in locals() and schedules:
        print(f'   First schedule structure:')
        schedule = schedules[0]
        print(f'     ID: {getattr(schedule, "id", "N/A")}')
        print(f'     Type: {getattr(schedule, "schedule_type", "N/A")}')
        print(f'     Status: {getattr(schedule, "status", "N/A")}')
        print(f'     Routes: {getattr(schedule, "routes", "N/A")}')
        print(f'     Trains: {getattr(schedule, "trains_used", "N/A")}')
        print(f'     Cargo: {getattr(schedule, "total_cargo", "N/A")}')
    
    print('\n🌐 STEP 3: Simulating frontend API calls')
    
    # Simulate what the frontend would receive
    try:
        # Simulate /alerts/ endpoint
        alerts_response = {
            "alerts": alerts if 'alerts' in locals() else [],
            "total": len(alerts) if 'alerts' in locals() else 0
        }
        print(f'   /alerts/ response: {len(alerts_response["alerts"])} alerts')
        
        # Simulate /alerts/schedules endpoint
        schedules_response = schedules if 'schedules' in locals() else []
        print(f'   /alerts/schedules response: {len(schedules_response)} schedules')
        
        # Simulate /alerts/summary endpoint
        summary_response = summary if 'summary' in locals() else {}
        print(f'   /alerts/summary response: {summary_response}')
        
    except Exception as e:
        print(f'   ❌ Error simulating responses: {e}')
    
    print('\n🎯 STEP 4: Identifying potential issues')
    
    issues = []
    
    # Check if alerts are empty
    if 'alerts' in locals() and len(alerts) == 0:
        issues.append("No alerts found in system")
    
    # Check if schedules are empty
    if 'schedules' in locals() and len(schedules) == 0:
        issues.append("No schedules found in system")
    
    # Check summary structure
    if 'summary' in locals():
        if 'alerts' not in summary or 'total_alerts' not in summary.get('alerts', {}):
            issues.append("Summary missing alerts.total_alerts")
        if 'schedules' not in summary:
            issues.append("Summary missing schedules section")
    
    if issues:
        print(f'   🚨 Issues found:')
        for issue in issues:
            print(f'     - {issue}')
    else:
        print(f'   ✅ No obvious issues found')
    
    print('\n🔧 STEP 5: Recommendations')
    
    if len(issues) > 0:
        print(f'   🔧 Fix recommendations:')
        if "No alerts found" in issues:
            print(f'     - Generate sample alerts using the API')
            print(f'     - Check if alert generation is working')
        if "No schedules found" in issues:
            print(f'     - Generate sample schedules using the API')
            print(f'     - Check if schedule creation is working')
        if "Summary missing" in issues:
            print(f'     - Fix summary endpoint to include all required fields')
    else:
        print(f'   ✅ API endpoints appear to be working correctly')
        print(f'   🔍 Issue might be in frontend JavaScript or browser cache')
        print(f'   🔧 Try refreshing the browser or checking browser console')

if __name__ == "__main__":
    debug_alerts_api()
