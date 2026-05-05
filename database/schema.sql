CREATE TABLE IF NOT EXISTS daily_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER,
    route TEXT,
    cargo_remaining REAL,
    trains_available INTEGER,
    action INTEGER,
    reward REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
