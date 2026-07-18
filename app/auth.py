import secrets
import sqlite3
from typing import Optional

from fastapi import Depends, HTTPException, Request

from app.db import get_db
from app.security import hash_api_token

SESSION_COOKIE = "session_token"


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    return token


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


def get_current_user(
    request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> Optional[sqlite3.Row]:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        return conn.execute(
            "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token = ?",
            (token,),
        ).fetchone()

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        api_token = auth_header.removeprefix("Bearer ").strip()
        row = conn.execute(
            "SELECT users.*, api_tokens.id AS api_token_id FROM api_tokens "
            "JOIN users ON users.id = api_tokens.user_id "
            "WHERE api_tokens.token_hash = ?",
            (hash_api_token(api_token),),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE api_tokens SET last_used_at = datetime('now') WHERE id = ?",
                (row["api_token_id"],),
            )
            conn.commit()
        return row

    return None


def require_user(user: Optional[sqlite3.Row] = Depends(get_current_user)) -> sqlite3.Row:
    if user is None:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_writer(user: sqlite3.Row = Depends(require_user)) -> sqlite3.Row:
    """Authenticated *and* allowed to create/edit content. `leitor` accounts
    (external colleagues/managers who consume via MCP but shouldn't publish)
    pass require_user but stop here."""
    if user["role"] == "leitor":
        raise HTTPException(status_code=403, detail="Conta leitor não pode criar ou editar")
    return user


def require_admin(user: sqlite3.Row = Depends(require_writer)) -> sqlite3.Row:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin pode fazer isso")
    return user
