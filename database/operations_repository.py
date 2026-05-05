from database.db import get_connection

def init_db():
    conn = get_connection()
    with open("database/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def log_operation(
    day,
    route,
    cargo_remaining,
    trains_available,
    action,
    reward
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO daily_operations
        (day, route, cargo_remaining, trains_available, action, reward)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (day, route, cargo_remaining, trains_available, action, reward)
    )

    conn.commit()
    conn.close()
