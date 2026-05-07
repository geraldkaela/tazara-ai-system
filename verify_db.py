import psycopg2

DATABASE_URL = 'postgresql://postgres:tSaCccFLweXbbXLOQiXDxRLhyljbGEZF@trolley.proxy.rlwy.net:48704/railway'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Count all tables
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
table_count = cur.fetchone()[0]
print(f'Total tables: {table_count}')

# Check users
try:
    cur.execute('SELECT COUNT(*) FROM users')
    user_count = cur.fetchone()[0]
    print(f'Total users: {user_count}')
    
    cur.execute('SELECT username, role FROM users LIMIT 10')
    print('\nUsers in database:')
    for row in cur.fetchall():
        print(f'  - {row[0]}: {row[1]}')
except Exception as e:
    print(f'Users table check: {e}')

cur.close()
conn.close()
