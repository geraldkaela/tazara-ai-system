CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    day INTEGER NOT NULL,
    step INTEGER NOT NULL,
    actor TEXT NOT NULL,
    action INTEGER NOT NULL,
    available_trains INTEGER,
    cargo_remaining REAL,
    reward REAL,
    severity TEXT,
    message TEXT
);
