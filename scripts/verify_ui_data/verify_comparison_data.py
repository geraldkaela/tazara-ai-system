import requests
import os
import pandas as pd
import io

# Configuration
COMPARE_URL = "http://127.0.0.1:8000/compare/"

def create_test_file():
    """Create a temporary excel file for testing"""
    data = {
        'route': ['DAR_KAPIRI', 'DAR_MBEYA', 'KAPIRI_NDOLA'],
        'cargo': [500, 300, 200],
        'priority': [1, 2, 3]
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

def main():
    print("=" * 60)
    print("VERIFYING COMPARISON DATA (comparison.html)")
    print("=" * 60)
    
    file_content = create_test_file()
    
    try:
        files = {'file': ('test.xlsx', file_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(COMPARE_URL, files=files)
        data = response.json()
        
        print(f"\nAPI Status: {data.get('message', 'No message')}")
        print(f"Routes Detected: {data.get('routes_detected', 0)}")
        
        comp = data.get('comparison', {})
        if not comp:
            print("❌ FAIL: Comparison data not found.")
            return
            
        # Verify analysis keys
        analysis = comp.get('analysis', {})
        required_keys = ['profit_improvement_zmw', 'revenue_improvement_zmw', 'cost_reduction_zmw']
        
        all_pass = True
        print("\nVerifying Analysis Metrics:")
        for key in required_keys:
            val = analysis.get(key)
            status = "✅ PASS" if val is not None else "❌ FAIL"
            print(f"  {key:25}: Value={val:<10} | {status}")
            if status == "❌ FAIL": all_pass = False
            
        if all_pass:
            print("\n✨ VERIFICATION SUCCESSFUL: Comparison engine returned valid metrics.")
        else:
            print("\n⚠️ VERIFICATION FAILED: Missing comparison metrics.")
            import sys
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error performing comparison: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
