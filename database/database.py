from contextlib import contextmanager
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def db_session():
    conn = get_db_connection()
    try:
        with conn:
            yield conn
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise RuntimeError("Database operation failed") from e
    finally:
        conn.close()

def innit_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_session() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
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

def remove_subscription(kind, target_id):
    with db_session() as conn:
        conn.execute("DELETE FROM subscriptions WHERE kind=? AND target_id=?", (kind, target_id))

def get_subscriptions(kind, target_id):
    with db_session() as conn:
        return conn.execute("SELECT * FROM subscriptions WHERE kind=? AND target_id=?", (kind, target_id)).fetchone()

def get_due_subscriptions(now_utc):
    with db_session() as conn:
        return conn.execute("SELECT * FROM subscriptions WHERE next_send_at <= ?", (now_utc,)).fetchall()

def add_or_update_subscription(kind, target_id, send_time, timezone, next_send_at):
    with db_session() as conn:
        conn.execute("""
            INSERT INTO subscriptions (kind, target_id, send_time, timezone, next_send_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(kind, target_id) DO UPDATE SET
                send_time = excluded.send_time,
                timezone = excluded.timezone,
                next_send_at = excluded.next_send_at
            """, (kind, target_id, send_time, timezone, next_send_at))

def update_subscription_next_send(kind, target_id, old_next_send_at, new_next_send_at):
    with db_session() as conn:
        cursor = conn.execute("""
            UPDATE subscriptions 
            SET next_send_at = ? 
            WHERE kind = ? AND target_id = ? AND next_send_at = ?
            """, (new_next_send_at, kind, target_id, old_next_send_at))
        return cursor.rowcount > 0


