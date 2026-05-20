"""
Server-side script storage. Every query is scoped by user_id so each account
only reads and writes its own rows (no cross-user access).
"""

from __future__ import annotations

from typing import Any

from services.executor import normalize_language
from utils.helpers import get_db


def list_scripts_for_user(user_id: int) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, user_id, title, code, language, updated_at
        FROM scripts WHERE user_id = ?
        ORDER BY datetime(updated_at) DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_script(user_id: int, script_id: int) -> dict[str, Any] | None:
    db = get_db()
    row = db.execute(
        """
        SELECT id, user_id, title, code, language, updated_at
        FROM scripts WHERE id = ? AND user_id = ?
        """,
        (script_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def save_script(user_id: int, title: str, code: str, language: str = "python") -> int:
    title = title.strip() or "Untitled"
    lang = normalize_language(language)
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO scripts (user_id, title, code, language)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, title, code, lang),
    )
    db.commit()
    return int(cur.lastrowid)


def update_script(
    user_id: int,
    script_id: int,
    title: str | None,
    code: str | None,
    language: str | None = None,
) -> bool:
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM scripts WHERE id = ? AND user_id = ?",
        (script_id, user_id),
    ).fetchone()
    if row is None:
        return False
    fields: list[str] = []
    args: list[Any] = []
    if title is not None:
        fields.append("title = ?")
        args.append(title.strip() or "Untitled")
    if code is not None:
        fields.append("code = ?")
        args.append(code)
    if language is not None:
        fields.append("language = ?")
        args.append(normalize_language(language))
    if not fields:
        return True
    fields.append("updated_at = datetime('now')")
    args.extend([script_id, user_id])
    sql = f"UPDATE scripts SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
    db.execute(sql, args)
    db.commit()
    return True


def delete_script(user_id: int, script_id: int) -> bool:
    db = get_db()
    cur = db.execute(
        "DELETE FROM scripts WHERE id = ? AND user_id = ?",
        (script_id, user_id),
    )
    db.commit()
    return cur.rowcount > 0
