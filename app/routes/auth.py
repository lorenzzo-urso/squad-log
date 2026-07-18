import logging
import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import SESSION_COOKIE, create_session, delete_session, get_current_user
from app.db import get_db
from app.security import verify_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse("/timeline", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"user": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    conn: sqlite3.Connection = Depends(get_db),
):
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"], row["password_salt"]):
        logger.warning("login failed email=%s", email)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "error": "Email ou senha inválidos"},
            status_code=401,
        )
    token = create_session(conn, row["id"])
    logger.info("login ok user_id=%s email=%s", row["id"], email)
    response = RedirectResponse("/timeline", status_code=303)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax")
    return response


@router.post("/logout")
def logout(request: Request, conn: sqlite3.Connection = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        delete_session(conn, token)
        logger.info("logout")
    response = RedirectResponse("/timeline", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response
