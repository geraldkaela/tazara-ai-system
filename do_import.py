import psycopg2

DATABASE_URL = 'postgresql://postgres:tSaCccFLweXbbXLOQiXDxRLhyljbGEZF@trolley.proxy.rlwy.net:48704/railway'

print('Connecting to Railway database...')
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

print('Reading SQL file...')
with open('local_backup_nobom.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

print('Executing SQL...')
statements = sql.split(';')
count = 0
for stmt in statements:
    stmt = stmt.strip()
    if stmt and not stmt.startswith('--'):
        try:
            cur.execute(stmt)
            count += 1
            if count % 100 == 0:
                print(f'Executed {count} statements...')
        except Exception as e:
            if 'already exists' not in str(e):
                print(f'Error: {str(e)[:60]}')

print(f'✅ Executed {count} statements')

# Check tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = cur.fetchall()
print(f'\nTables in database: {len(tables)}')
for table in tables[:20]:
    print(f'  - {table[0]}')

cur.close()
conn.close()
