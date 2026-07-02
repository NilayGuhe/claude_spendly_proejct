import os
import sqlite3
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

# Module-level path constant: <project_root>/spendly.db
# __file__ is .../database/db.py, so its parent is the project root.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spendly.db")

# DDL — schema is not user input, so literal SQL is appropriate here.
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_EXPENSES_TABLE = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    description TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    """Open a SQLite connection to the project DB with row_factory + FK enforcement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection = None) -> None:
    """Create both tables. Idempotent — safe to call on every startup."""
    if conn is None:
        conn = get_db()
    conn.execute(CREATE_USERS_TABLE)
    conn.execute(CREATE_EXPENSES_TABLE)
    conn.commit()


def seed_db(conn: sqlite3.Connection = None) -> None:
    """Insert the demo user and 8 sample expenses — once. Idempotent."""
    if conn is None:
        conn = get_db()

    # Guard: skip if data already present.
    (user_count,) = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if user_count > 0:
        return

    # Demo user.
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )

    # Look up the demo user's id rather than hard-coding 1.
    (user_id,) = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()

    # 8 sample expenses — covers all 7 fixed categories (Food appears twice).
    today = date.today()
    sample_expenses = [
        (250.00,  "Food",          today - timedelta(days=0),  "Lunch at campus cafe"),
        (180.00,  "Transport",     today - timedelta(days=1),  "Metro pass top-up"),
        (1500.00, "Bills",         today - timedelta(days=3),  "Electricity bill"),
        (600.00,  "Health",        today - timedelta(days=5),  "Pharmacy"),
        (450.00,  "Entertainment", today - timedelta(days=7),  "Movie ticket"),
        (1200.00, "Shopping",      today - timedelta(days=10), "New headphones"),
        (80.00,   "Other",         today - timedelta(days=14), "Misc supplies"),
        (320.00,  "Food",          today - timedelta(days=18), "Groceries"),
    ]

    for amount, category, d, description in sample_expenses:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, d.isoformat(), description),
        )

    conn.commit()
