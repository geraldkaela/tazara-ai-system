import sqlite3
from pathlib import Path

DB_PATH = Path("database/tazara.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get existing columns
cur.execute("PRAGMA table_info(daily_operations);")
existing_columns = {row[1] for row in cur.fetchall()}

# Columns required by Phase 2
required_columns = {
    "total_reward": "REAL DEFAULT 0",
    "cargo_delivered": "REAL DEFAULT 0",
    "trains_used": "INTEGER DEFAULT 0",
    "idle_penalty": "REAL DEFAULT 0",
    "assign_count": "INTEGER DEFAULT 0",
    "delay_count": "INTEGER DEFAULT 0",
    "skip_count": "INTEGER DEFAULT 0",
}

# Add missing columns safely
for column, col_type in required_columns.items():
    if column not in existing_columns:
        print(f"➕ Adding column: {column}")
        cur.execute(
            f"ALTER TABLE daily_operations ADD COLUMN {column} {col_type};"
        )

conn.commit()
conn.close()

print("✅ Database schema updated successfully")
