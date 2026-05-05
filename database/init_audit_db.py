import sqlite3

conn = sqlite3.connect("database/tazara.db")
cur = conn.cursor()

with open("database/audit_schema.sql") as f:
    cur.executescript(f.read())

conn.commit()
conn.close()

print("✅ Audit log table initialized")

