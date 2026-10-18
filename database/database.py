import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def innit_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS
        subscriptions (
            kind TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            send_time TEXT NOT NULL,
            timezone TEXT NOT NULL,
            next_send_at INTEGER NOT NULL,
            PRIMARY KEY (kind,target_id))
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_next_send ON subscriptions(next_send_at)")
    conn.close()

def remove_subscription(kind,target_id):
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM subscriptions WHERE kind=? AND target_id=?", (kind,target_id))
    conn.close()

def get_subscriptions(kind, target_id):
    conn = get_db_connection()
    result = conn.execute("SELECT * FROM subscriptions WHERE kind=? AND target_id=?", (kind, target_id)).fetchone()
    conn.close()
    return result

def get_due_subscriptions(now_utc):
    conn = get_db_connection()
    results = conn.execute("SELECT * FROM subscriptions WHERE next_send_at <= ?", (now_utc,)).fetchall()
    conn.close()
    return results #returns list of rows

def add_or_update_subscription(kind,target_id,send_time,timezone,next_send_at):
    conn = get_db_connection()
    with conn:
        conn.execute("""
            INSERT INTO subscriptions (kind, target_id, send_time, timezone, next_send_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(kind, target_id) DO UPDATE SET
                send_time = excluded.send_time,
                timezone = excluded.timezone,
                next_send_at = excluded.next_send_at
            """, (kind, target_id, send_time, timezone, next_send_at))
    conn.close()

def set_next_send_times(updates): # accepts list of tuples
    conn = get_db_connection()
    with conn:
        conn.executemany(
            "UPDATE subscriptions SET next_send_at = ? WHERE kind = ? AND target_id = ?",
            updates
        )
    conn.close()

