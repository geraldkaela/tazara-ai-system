#!/usr/bin/env python3
"""
Apply Phase 4 Database Schema - Intelligent Resource Matching
Creates tables for skill-based assignment, geographic clustering, and asset management
"""

import psycopg2
import sys

def apply_phase4_schema():
    """Apply Phase 4 schema to database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        print("🚀 Applying Phase 4 Database Schema...")
        print("=" * 60)
        
        # Read and execute schema file
        with open('database/phase4_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'driver_skills', 'skill_task_matching', 'geographic_clusters',
                'route_segments', 'asset_assignments', 'asset_utilization_daily',
                'resource_conflicts', 'optimization_recommendations'
            )
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Phase 4 Schema Applied Successfully!")
        print(f"📊 Created {len(tables)} new tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check sample data
        print("\n👥 Checking Sample Data:")
        
        cursor.execute("SELECT COUNT(*) FROM driver_skills")
        driver_count = cursor.fetchone()[0]
        print(f"  - Driver skills: {driver_count} drivers")
        
        cursor.execute("SELECT COUNT(*) FROM geographic_clusters")
        cluster_count = cursor.fetchone()[0]
        print(f"  - Geographic clusters: {cluster_count} clusters")
        
        cursor.execute("SELECT COUNT(*) FROM route_segments")
        segment_count = cursor.fetchone()[0]
        print(f"  - Route segments: {segment_count} segments")
        
        cursor.execute("SELECT COUNT(*) FROM asset_assignments")
        asset_count = cursor.fetchone()[0]
        print(f"  - Asset assignments: {asset_count} assignments")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname, tablename FROM pg_indexes 
            WHERE tablename IN (
                'driver_skills', 'skill_task_matching', 'geographic_clusters',
                'route_segments', 'asset_assignments', 'asset_utilization_daily',
                'resource_conflicts', 'optimization_recommendations'
            )
            AND indexname LIKE 'idx_%'
        """)
        
        indexes = cursor.fetchall()
        print(f"\n📈 Created {len(indexes)} performance indexes:")
        for idx in indexes[:5]:  # Show first 5
            print(f"  - {idx[0]} on {idx[1]}")
        if len(indexes) > 5:
            print(f"  ... and {len(indexes) - 5} more")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Phase 4 Database Setup Complete!")
        print("\nNew Features Enabled:")
        print("  - Skill-based driver assignment")
        print("  - Geographic clustering for routes")
        print("  - Asset utilization tracking")
        print("  - Resource conflict detection")
        print("  - AI optimization recommendations")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: database/phase4_schema.sql not found")
        return False
    except Exception as e:
        print(f"❌ Error applying Phase 4 schema: {e}")
        return False

if __name__ == "__main__":
    success = apply_phase4_schema()
    sys.exit(0 if success else 1)
