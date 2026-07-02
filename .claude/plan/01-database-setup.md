# Plan: 01 — Database Setup

## Context

This is **Step 1** of the Spendly build — the data-layer foundation. Everything that comes after (auth in Step 3, profile in Step 4, expense CRUD in Steps 7–9) reads and writes through the helpers defined here, so getting the schema, connection settings, and seed behavior right now prevents painful migrations later.

Today the project ships only a comment-only stub in `database/db.py` and a Flask app in `app.py` that imports nothing from the database package. The two routes and the `__main__` block in `app.py` will be extended to import and call the new helpers, but no new routes are added and no templates are touched.

Goal: replace the stub with a working SQLite layer (`get_db`, `init_db`, `seed_db`) that satisfies the schema and rules in `.claude/specs/01-database-setup.md`, and wire it into `app.py` startup so the database is ready before any route handles a request.

## Approach

**File 1: `database/db.py`** — full implementation.

- Module-level constants:
  - `DB_PATH = os.path.join(os.path.dirname(...), "spendly.db")` resolving to the project root (sibling of `app.py`). Use `os.path.dirname(os.path.abspath(__file__))` then walk up one level (the file lives in `database/`, root is its parent). Computed at import time; small enough to be a constant.
- `get_db() -> sqlite3.Connection`:
  - Open `sqlite3.connect(DB_PATH)`.
  - Set `conn.row_factory = sqlite3.Row` (dict-like row access).
  - Execute `PRAGMA foreign_keys = ON;` and return.
  - No connection caching here — `app.py` calls it inside `app_context()` and routes will create per-request connections in later steps.
- `init_db() -> None`:
  - Accept a `conn` argument (default `get_db()`) so it can be called from `app.py` inside an existing context.
  - Two `CREATE TABLE IF NOT EXISTS` statements matching the spec exactly:
    - `users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')))`
    - `expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), amount REAL NOT NULL, category TEXT NOT NULL, date TEXT NOT NULL, description TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')))`
  - The spec uses bare `datetime('now')` — wrap it as a default expression in the DDL so SQLite fills it on insert; this matches both the spec wording and SQLite's behaviour.
  - `CREATE` strings are constants at module top — they are the schema, not data, and are not user input, so inline literals are safe (and required for DDL with defaults).
- `seed_db() -> None`:
  - Use the same connection-as-argument pattern (`conn=None`, default `get_db()`).
  - `SELECT COUNT(*) FROM users` — if `> 0`, return early. This is the duplicate-insert guard.
  - One demo user via parameterized `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)` with `generate_password_hash("demo123")`.
  - Eight sample expenses linked to that user, one row at a time, all using `?` placeholders. Categories chosen to cover all 7 fixed categories plus a repeat: `Food, Transport, Bills, Health, Entertainment, Shopping, Other, Food` (repeat Food to fill the 8th row and match "at least one expense per category").
  - Amounts: small varied rupees, e.g. 250, 180, 1500, 600, 450, 1200, 80, 320.
  - Dates: compute `today = date.today()`, then walk backwards using `timedelta(days=N)` for `N` in `[0, 1, 3, 5, 7, 10, 14, 18]`. All land in the current month, spread out across it. `description` values: short strings, all `NOT NULL`-safe (use `None` for one to exercise the nullable column).
  - Look up the demo user's `id` with a parameterized `SELECT id FROM users WHERE email = ?` and use that for `user_id` (avoids hard-coding `1`, which would break if seed were ever re-run after manual inserts).

**File 2: `app.py`** — minimal additions.

- After the existing imports and `app = Flask(__name__)`, add:
  ```python
  from database.db import get_db, init_db, seed_db
  ```
- Immediately after the `app` object is created, add the startup block (kept inside the module body, not inside `if __name__ == "__main__":`, so it runs under both `python app.py` and `flask run`):
  ```python
  with app.app_context():
      conn = get_db()
      init_db(conn)
      seed_db(conn)
      conn.close()
  ```
  Calling `init_db` and `seed_db` with an explicit `conn` reuses the connection that already has `PRAGMA foreign_keys = ON` set, and `close()` is a no-op safety net since the process owns the connection.
- No route changes. No template changes.

### Why these specific choices

- **`spendly.db` in the project root**: confirmed in clarification. The existing `.gitignore` ignores `expense_tracker.db`; using `spendly.db` per the spec means we should also extend `.gitignore` to ignore it (the file is created on first run, must not be committed).
- **Direct startup call inside `app.app_context()`**: confirmed in clarification. It satisfies the spec wording ("call init_db() and seed_db() inside app.app_context() on startup") and is the simplest path that doesn't require a CLI command or a Flask extension.
- **Dates from `date.today()`**: confirmed in clarification. The spec says "current month"; deriving from `today` is unambiguous, self-updating, and meets the wording. A hard-coded day-of-month with anchored year+month would also work but adds magic numbers.
- **All queries parameterized**: required by the spec ("Use parameterized queries only"). The DDL strings are constants, not data, and aren't user input — inline literals there are correct.
- **Connection passed into `init_db`/`seed_db`**: not strictly required, but lets `app.py` open a single connection with `PRAGMA foreign_keys = ON` and reuse it for both calls, so the seed insert happens on a connection that actually enforces the FK it relies on.

## Files to change

- `database/db.py` — replace the comment-only stub with the full implementation described above.
- `app.py` — add the import and the startup block (three lines each, placed adjacent to the existing `app = Flask(__name__)`).
- `.gitignore` — add `spendly.db` so the created file isn't committed (the file is already created on disk; the existing entry ignores `expense_tracker.db` but not this filename).

## Files NOT to touch

- `templates/*.html` — no new routes, no new content.
- `static/**` — no UI changes in this step.
- `requirements.txt` — spec says no new pip packages; `sqlite3` is stdlib and `werkzeug` is already pinned.

## Verification

End-to-end check that everything works from a clean state:

1. **Clean state**
   - `rm -f spendly.db` (or delete the file in the project root) to start fresh.
2. **Install + run**
   - `pip install -r requirements.txt` (only needed if venv is missing).
   - `python app.py` — server should start on `http://127.0.0.1:5001` with no traceback, and `spendly.db` should appear in the project root.
3. **Schema check** (manual `sqlite3` smoke test, no test framework yet):
   - `sqlite3 spendly.db ".schema"` — both `users` and `expenses` tables present with the columns/constraints from the spec.
   - `sqlite3 spendly.db "SELECT COUNT(*) FROM users;"` → `1`.
   - `sqlite3 spendly.db "SELECT COUNT(*) FROM expenses;"` → `8`.
   - `sqlite3 spendly.db "SELECT DISTINCT category FROM expenses;"` → all 7 fixed categories present.
   - `sqlite3 spendly.db "SELECT email, password_hash FROM users;"` → `demo@spendly.com`, hash starts with one of `pbkdf2:`, `scrypt:`, or `argon2:` (whatever `werkzeug` 3.1.6 produces by default).
4. **Idempotency**
   - Stop the server (Ctrl+C) and `python app.py` again — should start cleanly with no errors, and the user/expense counts above should still be `1` and `8` (seed guard worked).
5. **Constraint behaviour** (sanity-check the schema enforces the spec):
   - In a Python REPL with the project venv active:
     ```python
     from database.db import get_db
     c = get_db()
     c.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", ("x", "demo@spendly.com", "x"))
     c.execute("COMMIT")  # or just let implicit transaction commit on close
     ```
     should raise `sqlite3.IntegrityError: UNIQUE constraint failed: users.email`.
   - `c.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)", (9999, 1.0, "Food", "2026-07-01"))` should raise `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
6. **App still serves pages** — `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5001/` returns `200`; same for `/login`, `/register`, `/terms`, `/privacy`. The placeholder routes (`/expenses/add`, etc.) should still return their "coming in Step N" strings.

All six buckets map directly to the "Definition of Done" checklist at the bottom of `.claude/specs/01-database-setup.md`.
