import subprocess
import sys
import os

def run_multi_route_dashboard():
    """Run multi-route operations dashboard"""
    try:
        print("🚂 Starting TAZARA Multi-Route Dashboard...")
        print("📊 Advanced multi-train scheduling and analytics")
        print("🌐 Dashboard will open in your browser at http://localhost:8505")
        print("\n🎯 Features Available:")
        print("   • Real-time multi-train monitoring")
        print("   • Advanced schedule creation and visualization")
        print("   • Performance analytics and trend analysis")
        print("   • Route efficiency comparison")
        print("   • ZMW cost breakdown and analysis")
        print("   • System configuration management")
        print("   • Executive-friendly interface for non-technical users")
        print("   • Multi-tab interface for different user roles")
        print("\n⚠️  Make sure API server is running on http://127.0.0.1:8000")
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard/multi_route_dashboard.py",
            "--server.port", "8505"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Multi-Route Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    run_multi_route_dashboard()
