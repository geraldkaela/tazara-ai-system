import subprocess
import sys
import os

def run_alerts_dashboard():
    """Run alerts dashboard"""
    try:
        print("🚨 Starting TAZARA Alerts Dashboard...")
        print("📊 Real-time alerts and daily operations monitoring")
        print("🌐 Dashboard will open in your browser at http://localhost:8502")
        print("\n⚠️  Make sure API server is running on http://127.0.0.1:8000")
        print("   Run: uvicorn api.main:app --reload")
        print("\n🚨 Features:")
        print("   • Real-time alert monitoring")
        print("   • Daily operations reports")
        print("   • Alert acknowledgment")
        print("   • Performance trends")
        print("   • ZMW impact tracking")
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard/alerts_dashboard.py",
            "--server.port", "8504"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Alerts dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting alerts dashboard: {e}")

if __name__ == "__main__":
    run_alerts_dashboard()
