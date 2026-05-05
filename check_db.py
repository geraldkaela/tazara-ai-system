import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='tazara_multi_route',
        user='tazara',
        password='tazara123'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()
    print('Available tables:')
    for table in tables:
        print(f'  - {table[0]}')
    cursor.execute("SELECT COUNT(*) FROM schedules")
    schedules_count = cursor.fetchone()[0]
    print(f'Schedules table count: {schedules_count}')
    cursor.close()
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database error: {e}')
