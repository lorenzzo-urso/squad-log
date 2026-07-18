import logging
import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import require_admin
from app.db import get_db
from app.security import hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

MAX_USERS = 4


@router.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request, user=Depends(require_admin), conn: sqlite3.Connection = Depends(get_db)):
    users = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    tags = conn.execute("SELECT * FROM tech_tags ORDER BY name").fetchall()
    write_user_count = sum(1 for u in users if u["role"] != "leitor")
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "user": user,
            "users": users,
            "tags": tags,
            "max_users": MAX_USERS,
            "write_user_count": write_user_count,
        },
    )


@router.post("/admin/users")
def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user=Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    if role not in ("admin", "membro", "leitor"):
        raise HTTPException(status_code=400)
    if role != "leitor":
        # MAX_USERS is a squad-seat limit (write access) from the PRD — leitor
        # accounts (read-only, for outside colleagues/managers via MCP) don't
        # compete for those seats.
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role != 'leitor'"
        ).fetchone()["n"]
        if count >= MAX_USERS:
            raise HTTPException(status_code=400, detail=f"Limite de {MAX_USERS} usuários atingido")
    password_hash, salt = hash_password(password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
        (name, email, password_hash, salt, role),
    )
    conn.commit()
    logger.info("user created by admin_id=%s email=%s role=%s", user["id"], email, role)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/{user_id}/rename")
def rename_user(
    user_id: int,
    name: str = Form(...),
    user=Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    password: str = Form(...),
    user=Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    password_hash, salt = hash_password(password)
    conn.execute(
        "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
        (password_hash, salt, user_id),
    )
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    logger.info("password reset by admin_id=%s target_user_id=%s", user["id"], user_id)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/{user_id}/delete")
def delete_user(user_id: int, user=Depends(require_admin), conn: sqlite3.Connection = Depends(get_db)):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Não é possível remover a própria conta")
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    logger.info("user deleted by admin_id=%s target_user_id=%s", user["id"], user_id)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/tags")
def create_tag(name: str = Form(...), user=Depends(require_admin), conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("INSERT OR IGNORE INTO tech_tags (name) VALUES (?)", (name,))
    conn.commit()
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/tags/{tag_id}/delete")
def delete_tag(tag_id: int, user=Depends(require_admin), conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("DELETE FROM tech_tags WHERE id = ?", (tag_id,))
    conn.commit()
    return RedirectResponse("/admin", status_code=303)
