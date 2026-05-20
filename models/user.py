"""User model and SQLite helpers for Flask-Login."""

from __future__ import annotations

from flask_login import UserMixin

from utils.helpers import get_db
from utils.security import hash_password, verify_password


class User(UserMixin):
    def __init__(self, id: int, username: str, password_hash: str) -> None:
        self.id = id
        self.username = username
        self.password_hash = password_hash


def get_user_by_id(user_id: int) -> User | None:
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return User(int(row["id"]), row["username"], row["password_hash"])


def get_user_by_username(username: str) -> User | None:
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        return None
    return User(int(row["id"]), row["username"], row["password_hash"])


def create_user(username: str, password: str) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username.strip(), hash_password(password)),
    )
    db.commit()
    return int(cur.lastrowid)


def authenticate(username: str, password: str) -> User | None:
    user = get_user_by_username(username.strip())
    if user is None:
        return None
    if verify_password(user.password_hash, password):
        return user
    return None
