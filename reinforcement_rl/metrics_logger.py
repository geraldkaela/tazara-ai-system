import sqlite3
import os
import pandas as pd

class MetricsLogger:
    def __init__(self, save_path="metrics/rl_daily_report.csv", db_path="database/tazara.db"):
        self.save_path = save_path
        self.db_path = db_path
        self.day_data = []
        self.step_data = []

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to DB
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()

        # Create table if it doesn't exist
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_operations (
            day INTEGER PRIMARY KEY,
            total_reward REAL,
            cargo_delivered REAL,
            trains_used INTEGER,
            idle_penalty REAL,
            assign_count INTEGER,
            delay_count INTEGER,
            skip_count INTEGER
        )
        """)
        self.conn.commit()

    def log_step(self, action, reward, cargo, trains_before, trains_after):
        trains_used = max(0, trains_before - trains_after)
        idle_penalty = max(0, -reward)
        self.step_data.append({
            "action": action,
            "reward": reward,
            "cargo_delivered": cargo,
            "trains_before": trains_before,
            "trains_after": trains_after,
            "trains_used": trains_used,
            "idle_penalty": idle_penalty
        })

    def end_day(self, day_number):
        if not self.step_data:
            return

        total_reward = sum(s["reward"] for s in self.step_data)
        total_cargo = sum(s["cargo_delivered"] for s in self.step_data)
        total_trains_used = sum(s["trains_used"] for s in self.step_data)
        total_idle_penalty = sum(s["idle_penalty"] for s in self.step_data)

        assign_count = sum(1 for s in self.step_data if s["action"] == 0)
        delay_count = sum(1 for s in self.step_data if s["action"] == 1)
        skip_count = sum(1 for s in self.step_data if s["action"] == 2)

        self.day_data.append({
            "day": day_number,
            "total_reward": round(total_reward, 2),
            "cargo_delivered": round(total_cargo, 2),
            "trains_used": total_trains_used,
            "idle_penalty": round(total_idle_penalty, 2),
            "assign_count": assign_count,
            "delay_count": delay_count,
            "skip_count": skip_count
        })

        # Insert into DB
        self.cur.execute("""
            INSERT OR REPLACE INTO daily_operations
            (day, total_reward, cargo_delivered, trains_used, idle_penalty, assign_count, delay_count, skip_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            day_number, total_reward, total_cargo, total_trains_used,
            total_idle_penalty, assign_count, delay_count, skip_count
        ))
        self.conn.commit()

        self.step_data = []

    def save(self):
        df = pd.DataFrame(self.day_data)
        df.to_csv(self.save_path, index=False)

    def close(self):
        self.conn.close()
