import requests
import os
import sys

# Configuration
ALERTS_URL = "http://127.0.0.1:8000/alerts/"
SUMMARY_URL = "http://127.0.0.1:8000/alerts/summary"

def main():
    print("=" * 60)
    print("VERIFYING ALERTS DATA (alerts.html)")
    print("=" * 60)
    
    # 1. Check Alerts List
    try:
        alerts = requests.get(ALERTS_URL).json()
        print(f"\nFetched {len(alerts)} alerts from API.")
        
        counts = {"critical": 0, "warning": 0, "info": 0}
        for a in alerts:
            counts[a['severity']] = counts.get(a['severity'], 0) + 1
            
        print("  Severity Breakdown:")
        for sev, count in counts.items():
            print(f"    - {sev.capitalize()}: {count}")
            
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        sys.exit(1)

    # 2. Check Summary
    try:
        summary = requests.get(SUMMARY_URL).json()
        print("\nVerifying Summary Counts:")
        
        # Mapping summary keys to our calculation
        mapping = {
            "critical_alerts": counts['critical'],
            "warning_alerts": counts['warning'],
            "info_alerts": counts['info']
        }
        
        all_pass = True
        for key, expected in mapping.items():
            actual = summary.get(key, 0)
            status = "✅ PASS" if actual == expected else "❌ FAIL"
            print(f"  {key:18}: API={actual:<5} | Expected={expected:<5} | {status}")
            if status == "❌ FAIL": all_pass = False
            
        if all_pass:
            print("\n✨ VERIFICATION SUCCESSFUL: Alerts summary matches alerts list.")
        else:
            print("\n⚠️ VERIFICATION FAILED: Alerts data inconsistency.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error fetching summary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
