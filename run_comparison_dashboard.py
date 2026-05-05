import subprocess
import sys
import os

def run_dashboard():
    """Run the comparison dashboard"""
    try:
        print("🚀 Starting TAZARA Comparison Dashboard...")
        print("📊 This will show Baseline vs RL performance comparison")
        print("🌐 Dashboard will open in your browser at http://localhost:8501")
        print("\n⚠️  Make sure the API server is running on http://127.0.0.1:8000")
        print("   Run: uvicorn api.main:app --reload")
        print("\n📁 Upload your Excel file to compare performance")
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard/comparison_dashboard.py",
            "--server.port", "8501"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    run_dashboard()
