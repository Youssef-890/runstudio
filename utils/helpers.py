"""SQLite connection and schema bootstrap."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, current_app, g

# Plain ":memory:" opens a new DB per connection; use one shared in-memory DB.
_SHARED_MEMORY_URI = "file:runstudio_shared?mode=memory&cache=shared"


def resolve_database_path(path: str) -> tuple[str, bool]:
    """Return (connect target, use_uri) for sqlite3.connect."""
    if path == ":memory:":
        return _SHARED_MEMORY_URI, True
    return path, False


def connect_database(path: str) -> sqlite3.Connection:
    target, use_uri = resolve_database_path(path)
    if not use_uri:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, uri=use_uri, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect_database(current_app.config["DATABASE"])
    return g.db


def close_db(_e=None) -> None:
    conn: sqlite3.Connection | None = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app: Flask) -> None:
    """Apply schema.sql; migrate older DBs missing optional columns."""
    schema_path = Path(app.root_path) / "database" / "schema.sql"
    with app.app_context():
        db = connect_database(app.config["DATABASE"])
        keep_open = resolve_database_path(app.config["DATABASE"])[0] == _SHARED_MEMORY_URI
        try:
            with open(schema_path, encoding="utf-8") as f:
                db.executescript(f.read())
            cols = [r[1] for r in db.execute("PRAGMA table_info(scripts)").fetchall()]
            if cols and "language" not in cols:
                db.execute(
                    "ALTER TABLE scripts ADD COLUMN language TEXT NOT NULL DEFAULT 'python'"
                )
            db.commit()
        finally:
            if keep_open:
                app.extensions["runstudio_memory_db"] = db
            else:
                db.close()


def safe_next_url(target: str | None, default_endpoint: str = "index") -> str:
    """Allow only same-app relative paths (blocks open redirects)."""
    from flask import url_for

    if not target:
        return url_for(default_endpoint)
    target = target.strip()
    if target.startswith("/") and not target.startswith("//"):
        return target
    return url_for(default_endpoint)
