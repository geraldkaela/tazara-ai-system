"""
Priority Services Startup Script
Initializes and starts priority auto-scheduling services
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from api.routes.priority_queue import initialize_services
from database.init_priority_queue import init_priority_queue_database, create_sample_orders

logger = logging.getLogger(__name__)

async def startup_priority_services():
    """Initialize and start priority auto-scheduling services"""
    try:
        print("🚀 Starting TAZARA Priority Auto-Scheduling Services...")
        print(f"📅 Startup Time: {datetime.now().isoformat()}")
        
        # Step 1: Initialize database schema
        print("\n📊 Step 1: Initializing Priority Queue Database...")
        if init_priority_queue_database():
            print("✅ Database schema initialized successfully")
        else:
            print("❌ Failed to initialize database schema")
            return False
        
        # Step 2: Create sample data
        print("\n📦 Step 2: Creating Sample Priority Orders...")
        if create_sample_orders():
            print("✅ Sample orders created successfully")
        else:
            print("❌ Failed to create sample orders")
            return False
        
        # Step 3: Initialize priority services
        print("\n🤖 Step 3: Initializing Priority Services...")
        if await initialize_services():
            print("✅ Priority services initialized and started")
        else:
            print("❌ Failed to initialize priority services")
            return False
        
        print("\n🎉 Priority Auto-Scheduling System Started Successfully!")
        print("=" * 60)
        print("📋 Available Services:")
        print("   • Priority Monitor: Running (5-minute intervals)")
        print("   • Auto-Scheduler: Running (10-minute intervals)")
        print("   • Priority Queue API: Available at /priority/*")
        print("   • Database: Connected and ready")
        print("   • Sample Data: 3 test orders loaded")
        print("=" * 60)
        print("🌐 Access Points:")
        print("   • Dashboard: http://127.0.0.1:8000/dashboard/multi_route.html")
        print("   • API Docs: http://127.0.0.1:8000/docs")
        print("   • Priority Queue: http://127.0.0.1:8000/priority/queue/status")
        print("   • Health Check: http://127.0.0.1:8000/priority/health")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Fatal error starting priority services: {e}")
        print(f"❌ Fatal Error: {e}")
        return False

def check_dependencies():
    """Check if all dependencies are available"""
    print("🔍 Checking Dependencies...")
    
    dependencies = {
        'psycopg2': 'PostgreSQL Database Connection',
        'fastapi': 'FastAPI Framework',
        'asyncio': 'Asyncio for Background Services'
    }
    
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} - MISSING")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n❌ Missing Dependencies: {', '.join(missing_deps)}")
        print("Please install missing dependencies and try again.")
        return False
    
    print("✅ All dependencies available")
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host='localhost',
            database='tazara_multi_route',
            user='tazara',
            password='tazara123'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def show_system_info():
    """Display system information"""
    print("\n📋 System Information:")
    print(f"   • Python Version: {sys.version}")
    print(f"   • Startup Time: {datetime.now().isoformat()}")
    print(f"   • Working Directory: {os.getcwd()}")
    print(f"   • Project Root: {os.path.dirname(os.path.dirname(os.path.abspath(__file__))}")

def main():
    """Main startup function"""
    print("🚂 TAZARA AI - Priority Auto-Scheduling System")
    print("=" * 60)
    
    # Show system info
    show_system_info()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Test database connection
    if not test_database_connection():
        return
    
    # Start services
    try:
        success = asyncio.run(startup_priority_services())
        if success:
            print("\n🎯 Priority Auto-Scheduling is now running!")
            print("📊 Monitor the system at: http://127.0.0.1:8000/priority/health")
            print("\n💡 Press Ctrl+C to stop services")
            
            # Keep running
            try:
                while True:
                    asyncio.sleep(60)
            except KeyboardInterrupt:
                print("\n🛑 Stopping Priority Auto-Scheduling Services...")
                # Services will be stopped gracefully
                break
        else:
            print("\n❌ Failed to start Priority Auto-Scheduling Services")
            
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted by user")
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")

if __name__ == "__main__":
    main()
