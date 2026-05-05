"""
TAZARA Multi-Route Database Setup Script
Phase 2 - Database Backend Integration
"""

import os
import sys
import psycopg2
from database.db_manager import DatabaseManager

def setup_database():
    """Setup and initialize the multi-route database"""
    
    print("🚂 TAZARA Multi-Route Database Setup")
    print("=" * 50)
    
    # Database connection parameters
    db_name = "tazara_multi_route"
    db_user = "tazara"
    db_password = "tazara123"
    db_host = "localhost"
    db_port = "5432"
    
    print(f"📊 Database: {db_name}")
    print(f"👤 User: {db_user}")
    print(f"🌐 Host: {db_host}:{db_port}")
    
    # Step 1: Connect to PostgreSQL server (without database)
    print("\n1️⃣ Connecting to PostgreSQL server...")
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database="postgres"  # Connect to default database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print(f"📝 Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Database '{db_name}' created successfully")
        else:
            print(f"✅ Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("💡 Make sure PostgreSQL is running and credentials are correct")
        return False
    
    # Step 2: Initialize database schema
    print("\n2️⃣ Initializing database schema...")
    try:
        db_manager = DatabaseManager()
        
        # Initialize database with schema
        if db_manager.initialize_database():
            print("✅ Database schema initialized successfully")
        else:
            print("❌ Failed to initialize database schema")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    # Step 3: Test database connection
    print("\n3️⃣ Testing database connection...")
    try:
        stats = db_manager.get_dashboard_statistics()
        print("✅ Database connection successful")
        print(f"📊 Initial statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Step 4: Create environment file
    print("\n4️⃣ Creating environment configuration...")
    env_content = f"""# TAZARA Multi-Route Database Configuration
DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}

# Multi-Route System Configuration
MAX_TRAINS=12
DEFAULT_PLANNING_HORIZON=14
COORDINATION_BONUS_ENABLED=true
PERFORMANCE_THRESHOLD=85
AUTO_RETRAIN_ENABLED=false
"""
    
    env_file = ".env"
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Environment file '{env_file}' created")
        
    except Exception as e:
        print(f"❌ Error creating environment file: {e}")
    
    # Step 5: Install required packages
    print("\n5️⃣ Checking required packages...")
    required_packages = ['psycopg2-binary', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        install_cmd = f"pip install {' '.join(missing_packages)}"
        print(f"💡 Run: {install_cmd}")
    
    # Step 6: Create startup script
    print("\n6️⃣ Creating startup script...")
    startup_script = """#!/bin/bash
# TAZARA Multi-Route System Startup

echo "🚂 Starting TAZARA Multi-Route System..."

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  .env file not found"
fi

# Start API server
echo "🌐 Starting API server..."
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start Multi-Route Dashboard
echo "📊 Starting Multi-Route Dashboard..."
python run_multi_route_dashboard.py &
DASHBOARD_PID=$!

echo "✅ System started successfully!"
echo "🌐 API Server: http://localhost:8000"
echo "📊 Dashboard: http://localhost:8505"
echo "📚 API Docs: http://localhost:8000/docs"

# Wait for user input to stop
echo "Press Ctrl+C to stop the system"
trap "kill $API_PID $DASHBOARD_PID; exit" INT
wait
"""
    
    startup_file = "start_multi_route_system.sh"
    try:
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        os.chmod(startup_file, 0o755)  # Make executable
        print(f"✅ Startup script '{startup_file}' created")
        
    except Exception as e:
        print(f"❌ Error creating startup script: {e}")
    
    print("\n🎉 Database Setup Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Install missing packages if any:")
    print("   pip install psycopg2-binary python-dotenv")
    print("\n2. Start the system:")
    print("   python start_multi_route_system.sh")
    print("\n3. Access the dashboard:")
    print("   🌐 Dashboard: http://localhost:8505")
    print("   📚 API Docs: http://localhost:8000/docs")
    print("\n4. Test database integration:")
    print("   curl http://localhost:8000/multi-route/status")
    
    print("\n🔧 Database Features Enabled:")
    print("✅ Schedule persistence")
    print("✅ Performance tracking")
    print("✅ Audit logging")
    print("✅ Configuration management")
    print("✅ Historical analytics")
    print("✅ Route performance monitoring")
    
    return True

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
