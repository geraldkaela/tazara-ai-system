#!/usr/bin/env python3
"""Comprehensive Database Inspector"""

import psycopg2

def inspect_all():
    conn = psycopg2.connect(
        host='localhost', database='tazara_multi_route', 
        user='tazara', password='tazara123'
    )
    cursor = conn.cursor()
    
    print("=" * 70)
    print("📊 COMPLETE DATABASE INVENTORY")
    print("=" * 70)
    
    # 1. All Tables
    print("\n🔹 ALL TABLES:")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    for t in tables:
        print(f"   • {t[0]}")
    
    # 2. Detailed Table Structures
    print("\n" + "=" * 70)
    print("🔹 TABLE STRUCTURES & DATA:")
    print("=" * 70)
    
    for table in tables:
        table_name = table[0]
        print(f"\n📁 {table_name.upper()}")
        print("-" * 50)
        
        # Columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        
        print("   Columns:")
        for col in columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f" [{col[3]}]" if col[3] else ""
            print(f"      • {col[0]} ({col[1]}) {nullable}{default}")
        
        # Row count
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            print(f"   Rows: {count}")
            
            # Sample data
            if count > 0:
                cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 2')
                rows = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
                print("   Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"      Row {i}:")
                    for name, value in zip(col_names, row):
                        if value is not None:
                            val_str = str(value)[:40] + "..." if len(str(value)) > 40 else str(value)
                            print(f"         {name}: {val_str}")
        except Exception as e:
            print(f"   Error: {e}")
    
    conn.close()
    print("\n" + "=" * 70)
    print("✅ INVENTORY COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    inspect_all()
