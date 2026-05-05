import subprocess
import sys
import os

def run_script(script_path):
    print(f"\n>>> Running {os.path.basename(script_path)}...")
    try:
        # Using sys.executable to ensure we use the same venv
        result = subprocess.run([sys.executable, script_path], capture_output=False, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_path}: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts = [
        "verify_index_data.py",
        "verify_multi_route_data.py",
        "verify_alerts_data.py",
        "verify_comparison_data.py",
        "verify_rl_data.py"
    ]
    
    print("=" * 60)
    print("TAZARA AI SYSTEM: DASHBOARD DATA VERIFICATION SUITE")
    print("=" * 60)
    
    passed_count = 0
    for script in scripts:
        full_path = os.path.join(base_dir, script)
        if run_script(full_path):
            passed_count += 1
            
    print("\n" + "=" * 60)
    print(f"VERIFICATION COMPLETE: {passed_count}/{len(scripts)} modules verified.")
    print("=" * 60)

if __name__ == "__main__":
    main()
