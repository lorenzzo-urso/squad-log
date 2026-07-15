import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import require_user
from app.db import get_db
from app.security import generate_api_token, hash_api_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/tokens", response_class=HTMLResponse)
def tokens_list(request: Request, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    tokens = conn.execute(
        "SELECT id, name, created_at, last_used_at FROM api_tokens "
        "WHERE user_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    return templates.TemplateResponse(
        request, "tokens.html", {"user": user, "tokens": tokens, "new_token": None}
    )


@router.post("/tokens")
def tokens_create(
    request: Request,
    name: str = Form(...),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    raw_token = generate_api_token()
    conn.execute(
        "INSERT INTO api_tokens (user_id, name, token_hash) VALUES (?, ?, ?)",
        (user["id"], name, hash_api_token(raw_token)),
    )
    conn.commit()
    tokens = conn.execute(
        "SELECT id, name, created_at, last_used_at FROM api_tokens "
        "WHERE user_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    return templates.TemplateResponse(
        request, "tokens.html", {"user": user, "tokens": tokens, "new_token": raw_token}
    )


@router.post("/tokens/{token_id}/revoke")
def tokens_revoke(token_id: int, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute("SELECT * FROM api_tokens WHERE id = ?", (token_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404)
    if row["user_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Só o dono do token ou um admin pode revogar")
    conn.execute("DELETE FROM api_tokens WHERE id = ?", (token_id,))
    conn.commit()
    return RedirectResponse("/tokens", status_code=303)
