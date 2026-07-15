import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth import require_user
from app.db import get_db
from app.routes.kanban import _card_responsibles, _card_tags
from app.routes.timeline import _post_coauthors

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CARD_STATUS_LABEL = {"idea": "Ideia", "doing": "Em andamento", "done": "Concluído"}


@router.get("/radar", response_class=HTMLResponse)
def radar(request: Request, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    posts = conn.execute(
        "SELECT DISTINCT posts.*, users.name AS author_name FROM posts "
        "JOIN users ON users.id = posts.author_id "
        "LEFT JOIN post_coauthors ON post_coauthors.post_id = posts.id "
        "WHERE posts.author_id = ? OR post_coauthors.user_id = ? "
        "ORDER BY posts.created_at DESC",
        (user["id"], user["id"]),
    ).fetchall()
    posts = [{**dict(p), "coauthors": _post_coauthors(conn, p["id"])} for p in posts]

    cards = conn.execute(
        "SELECT DISTINCT cards.* FROM cards "
        "JOIN card_responsibles ON card_responsibles.card_id = cards.id "
        "WHERE card_responsibles.user_id = ? "
        "ORDER BY cards.status, cards.position",
        (user["id"],),
    ).fetchall()
    cards = [
        {
            **dict(c),
            "status_label": CARD_STATUS_LABEL.get(c["status"], c["status"]),
            "tags": _card_tags(conn, c["id"]),
            "responsibles": _card_responsibles(conn, c["id"]),
        }
        for c in cards
    ]

    return templates.TemplateResponse(
        request, "radar.html", {"user": user, "posts": posts, "cards": cards}
    )
