import psycopg2
import os

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print('DATABASE_URL not found!')
    exit(1)

# Read the SQL backup file
with open('local_backup.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Connect and execute
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

# Split SQL statements by semicolon
statements = sql_content.split(';')
total = len(statements)
success = 0

for i, stmt in enumerate(statements):
    stmt = stmt.strip()
    if stmt and not stmt.startswith('--'):
        try:
            cur.execute(stmt)
            success += 1
            if success % 100 == 0:
                print(f'Processed {success}/{total} statements')
        except Exception as e:
            print(f'Error in statement {i}: {e}')
            # Continue with next statement

print(f'Import complete! {success}/{total} statements executed successfully')
cur.close()
conn.close()
