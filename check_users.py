import psycopg2

DATABASE_URL = 'postgresql://postgres:tSaCccFLweXbbXLOQiXDxRLhyljbGEZF@trolley.proxy.rlwy.net:48704/railway'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check if users table exists
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
table_exists = cur.fetchone()[0]

if table_exists:
    print('Users table exists')
    
    # Count users
    cur.execute('SELECT COUNT(*) FROM users')
    count = cur.fetchone()[0]
    print(f'Total users: {count}')
    
    # List all users
    if count > 0:
        cur.execute('SELECT id, username, role FROM users LIMIT 20')
        users = cur.fetchall()
        print('\nUsers in database:')
        for user in users:
            print(f'  - ID: {user[0]}, Username: {user[1]}, Role: {user[2]}')
    else:
        print('No users found in the users table')
else:
    print('Users table does NOT exist in the database')
    
    # List all tables that do exist
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print(f'\nExisting tables ({len(tables)}):')
    for table in tables:
        print(f'  - {table[0]}')

cur.close()
conn.close()
