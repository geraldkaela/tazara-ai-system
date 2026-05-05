import sqlite3
from datetime import datetime

class AuditLogger:
    def __init__(self, db_path="database/tazara.db"):
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()

    def log(
        self,
        day,
        step,
        actor,
        action,
        available_trains,
        cargo_remaining,
        reward,
        severity="INFO",
        message=""
    ):
        # 🔹 Add timestamp
        timestamp = datetime.utcnow().isoformat()

        self.cur.execute("""
INSERT INTO audit_logs (
    timestamp,
    day,
    step,
    actor,
    action,
    available_trains,
    cargo_remaining,
    reward,
    severity,
    message
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    timestamp,                  # ✅ timestamp added
    int(day),
    int(step),
    str(actor),
    int(action),
    int(available_trains),
    float(cargo_remaining),
    float(reward),
    str(severity),
    str(message)
))

        self.conn.commit()

    def close(self):
        self.conn.close()
