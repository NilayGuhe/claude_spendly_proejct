# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**Spendly** — a Flask personal-finance tracker. A student-driven build where features arrive in numbered "Steps." Many routes and the database layer are deliberately placeholder stubs that students will fill in; expect to see "coming in Step N" responses and a `database/db.py` file that is currently a comment-only stub.

Repository name in the working tree is `expense-tracker`; git remote points at `claude_spendly_proejct` on GitHub (`NilayGuhe/claude_spendly_proejct`).

## Running the app

```bash
# from the project root
python -m venv venv
source venv/bin/activate     # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Dev server listens on **port 5001** (not the Flask default 5000) with debug mode on.

## Tests

`requirements.txt` pins `pytest` and `pytest-flask`, but no `tests/` directory or `conftest.py` exists yet. When adding tests:

- Place them under `tests/` and run with `pytest` (or `pytest tests/test_x.py` for a single file).
- `pytest-flask` is available — use its `client` fixture against the `app` object in `app.py` to exercise routes.
- The dev server uses port 5001; do not assume port 5000 in any test fixture or docs.

There is no `Makefile`, `pyproject.toml`, `setup.cfg`, or `pytest.ini`.

## Architecture

Single-module Flask app, no blueprints, no app factory. Everything is in `app.py`.

```
expense-tracker/
├── app.py                  # Flask app + all routes (current + placeholder)
├── database/
│   ├── __init__.py         # empty package marker
│   └── db.py               # STUB — students implement get_db / init_db / seed_db
├── templates/              # Jinja2 templates, all extend base.html
│   ├── base.html           # nav + footer + Google Fonts + style.css + main.js
│   ├── landing.html        # public homepage (hero + features + YouTube demo modal)
│   ├── register.html       # auth form (currently GET-only — no handler yet)
│   ├── login.html          # auth form (currently GET-only — no handler yet)
│   ├── terms.html
│   └── privacy.html
├── static/
│   ├── css/style.css       # single stylesheet, CSS custom properties at :root
│   └── js/main.js          # STUB — currently a single comment line
├── requirements.txt
└── README.md               # contains only a UTF-16 BOM + a single project-name line
```

### Step-based build-out

Routes in `app.py` are split into two groups by a banner comment:

1. **Implemented** (`/`, `/register`, `/login`, `/terms`, `/privacy`) — all currently `GET`-only, returning templates. None of the auth or content routes have `POST` handlers yet.
2. **Placeholders** (return plain strings) for the upcoming steps:
   - `/logout` — Step 3
   - `/profile` — Step 4
   - `/expenses/add` — Step 7
   - `/expenses/<int:id>/edit` — Step 8
   - `/expenses/<int:id>/delete` — Step 9

When a new step is being implemented, the pattern is: add the `POST` handler + DB calls to the existing route, then add a new placeholder for the next step.

### Database layer

`database/db.py` is a comment-only stub documenting the expected interface:

- `get_db()` — returns a SQLite connection with `row_factory` set (so rows behave like dicts) and foreign-key enforcement enabled via `PRAGMA foreign_keys = ON`.
- `init_db()` — creates all tables using `CREATE TABLE IF NOT EXISTS` (idempotent).
- `seed_db()` — inserts sample data for development.

SQLite is implied (no driver listed in `requirements.txt`). The DB file `expense_tracker.db` is gitignored.

### Templates and assets

- `base.html` defines `{% block title %}`, `{% block content %}`, `{% block head %}`, and `{% block scripts %}`.
- All auth/marketing pages extend `base.html`; landing.html is the only template with a per-page `{% block scripts %}` (it embeds the YouTube demo modal controller inline).
- Design tokens live as CSS custom properties in `static/css/style.css` (`:root` block) — colours, fonts (`DM Serif Display` for display, `DM Sans` for body, both loaded from Google Fonts in `base.html`), spacing, and radii. Match the existing variable system when adding styles.
- `static/js/main.js` is a stub; the YouTube modal JS in `landing.html` shows the in-page-script pattern to follow.

## Conventions

- Routes are defined as bare `@app.route(...)` functions — no class-based views, no blueprints.
- Template links use `url_for('endpoint_name')`, not hard-coded paths (e.g. `url_for('landing')`, `url_for('register')`).
- Static assets are referenced via `url_for('static', filename='...')`.
- Keep the banner-comment style in `app.py` (`# --- #` blocks) when grouping new routes.
- `venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `.env`, `.claude/plans/`, and the `expense_tracker.db` SQLite file are all gitignored.
