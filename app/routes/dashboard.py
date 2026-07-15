import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user
from app.db import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
    posts_by_month = conn.execute(
        "SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS n FROM posts "
        "GROUP BY month ORDER BY month DESC LIMIT 12"
    ).fetchall()
    posts_by_month = list(reversed(posts_by_month))
    max_posts_month = max((row["n"] for row in posts_by_month), default=0)

    done_by_person = conn.execute(
        "SELECT users.name AS name, COUNT(DISTINCT cards.id) AS n FROM cards "
        "JOIN card_responsibles ON card_responsibles.card_id = cards.id "
        "JOIN users ON users.id = card_responsibles.user_id "
        "WHERE cards.status = 'done' "
        "GROUP BY users.id ORDER BY n DESC"
    ).fetchall()
    max_done = max((row["n"] for row in done_by_person), default=0)

    totals = {
        "posts": conn.execute("SELECT COUNT(*) AS n FROM posts").fetchone()["n"],
        "cards_idea": conn.execute("SELECT COUNT(*) AS n FROM cards WHERE status = 'idea'").fetchone()["n"],
        "cards_doing": conn.execute("SELECT COUNT(*) AS n FROM cards WHERE status = 'doing'").fetchone()["n"],
        "cards_done": conn.execute("SELECT COUNT(*) AS n FROM cards WHERE status = 'done'").fetchone()["n"],
        "roadmap_shipped": conn.execute(
            "SELECT COUNT(*) AS n FROM roadmap_items WHERE status = 'shipped'"
        ).fetchone()["n"],
        "roadmap_total": conn.execute("SELECT COUNT(*) AS n FROM roadmap_items").fetchone()["n"],
        "learning": conn.execute("SELECT COUNT(*) AS n FROM learning_items").fetchone()["n"],
    }

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "posts_by_month": posts_by_month,
            "max_posts_month": max_posts_month,
            "done_by_person": done_by_person,
            "max_done": max_done,
            "totals": totals,
        },
    )
