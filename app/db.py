import sqlite3
from datetime import datetime, timezone
from .config import DB_PATH

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chat_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                assistant_message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

def create_ticket(customer_name: str, category: str, priority: str, issue: str):
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tickets(customer_name, category, priority, issue, status, created_at) VALUES(?,?,?,?,?,?)",
            (customer_name, category, priority, issue, "open", created_at)
        )
        ticket_id = cur.lastrowid
    return {"ticket_id": f"TKT-{ticket_id:04d}", "category": category, "priority": priority, "status": "open"}

def list_tickets(limit: int = 50):
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, customer_name, category, priority, issue, status, created_at FROM tickets ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) | {"ticket_id": f"TKT-{r['id']:04d}"} for r in rows]

def log_chat(user_message: str, assistant_message: str):
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_log(user_message, assistant_message, created_at) VALUES(?,?,?)",
            (user_message, assistant_message, datetime.now(timezone.utc).isoformat())
        )
