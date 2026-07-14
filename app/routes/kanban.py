import sqlite3
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_user, require_user
from app.db import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COLUMNS = [("idea", "Ideia"), ("doing", "Em andamento"), ("done", "Concluído")]


def _tech_tags(conn: sqlite3.Connection):
    return conn.execute("SELECT * FROM tech_tags ORDER BY name").fetchall()


def _all_users(conn: sqlite3.Connection):
    return conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()


def _card_responsibles(conn: sqlite3.Connection, card_id: int):
    return conn.execute(
        "SELECT users.id, users.name FROM card_responsibles "
        "JOIN users ON users.id = card_responsibles.user_id "
        "WHERE card_responsibles.card_id = ? ORDER BY users.name",
        (card_id,),
    ).fetchall()


@router.get("/kanban", response_class=HTMLResponse)
def kanban_board(
    request: Request,
    person: int | None = None,
    tag: int | None = None,
    user=Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    query = (
        "SELECT DISTINCT cards.* FROM cards "
        "LEFT JOIN card_responsibles ON card_responsibles.card_id = cards.id WHERE 1=1"
    )
    params: list = []
    if person:
        query += " AND card_responsibles.user_id = ?"
        params.append(person)
    if tag:
        query += " AND cards.tech_tag_id = ?"
        params.append(tag)
    query += " ORDER BY cards.position ASC"
    cards = conn.execute(query, params).fetchall()

    tags_by_id = {t["id"]: t["name"] for t in _tech_tags(conn)}
    columns = {status: [] for status, _ in COLUMNS}
    for card in cards:
        columns[card["status"]].append(
            {
                **dict(card),
                "tech_tag_name": tags_by_id.get(card["tech_tag_id"], ""),
                "responsibles": _card_responsibles(conn, card["id"]),
            }
        )

    return templates.TemplateResponse(
        request,
        "kanban.html",
        {
            "user": user,
            "columns": COLUMNS,
            "cards_by_column": columns,
            "all_users": _all_users(conn),
            "all_tags": _tech_tags(conn),
            "filter_person": person,
            "filter_tag": tag,
        },
    )


@router.get("/kanban/new", response_class=HTMLResponse)
def card_new_form(request: Request, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "kanban_form.html",
        {
            "user": user,
            "editing": False,
            "card": {"title": "", "description": "", "tech_tag_id": None},
            "responsible_ids": {user["id"]},
            "all_users": _all_users(conn),
            "all_tags": _tech_tags(conn),
        },
    )


@router.post("/kanban/cards")
def card_create(
    title: str = Form(...),
    description: str = Form(""),
    tech_tag_id: int = Form(...),
    responsible_ids: list[int] = Form(default=[]),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) AS p FROM cards WHERE status = 'idea'"
    ).fetchone()["p"]
    cur = conn.execute(
        "INSERT INTO cards (title, description, tech_tag_id, status, position) "
        "VALUES (?, ?, ?, 'idea', ?)",
        (title, description, tech_tag_id, max_pos + 1),
    )
    card_id = cur.lastrowid
    for uid in set(responsible_ids) or {user["id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO card_responsibles (card_id, user_id) VALUES (?, ?)",
            (card_id, uid),
        )
    conn.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.get("/kanban/cards/{card_id}/edit", response_class=HTMLResponse)
def card_edit_form(card_id: int, request: Request, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        raise HTTPException(status_code=404)
    responsible_ids = {u["id"] for u in _card_responsibles(conn, card_id)}
    return templates.TemplateResponse(
        request,
        "kanban_form.html",
        {
            "user": user,
            "editing": True,
            "card": card,
            "responsible_ids": responsible_ids,
            "all_users": _all_users(conn),
            "all_tags": _tech_tags(conn),
        },
    )


@router.post("/kanban/cards/{card_id}/edit")
def card_edit_submit(
    card_id: int,
    title: str = Form(...),
    description: str = Form(""),
    tech_tag_id: int = Form(...),
    responsible_ids: list[int] = Form(default=[]),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        raise HTTPException(status_code=404)
    conn.execute(
        "UPDATE cards SET title = ?, description = ?, tech_tag_id = ? WHERE id = ?",
        (title, description, tech_tag_id, card_id),
    )
    conn.execute("DELETE FROM card_responsibles WHERE card_id = ?", (card_id,))
    for uid in set(responsible_ids) or {user["id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO card_responsibles (card_id, user_id) VALUES (?, ?)",
            (card_id, uid),
        )
    conn.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/kanban/cards/{card_id}/delete")
def card_delete(card_id: int, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/kanban/cards/{card_id}/publish")
def card_publish(card_id: int, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        raise HTTPException(status_code=404)
    title = quote(card["title"])
    body = quote(card["description"] or "")
    return RedirectResponse(f"/posts/new?title={title}&body={body}", status_code=303)


class ReorderBody(BaseModel):
    status: str
    order: list[int]


@router.post("/kanban/reorder")
def kanban_reorder(payload: ReorderBody, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    if payload.status not in dict(COLUMNS):
        raise HTTPException(status_code=400)
    for index, card_id in enumerate(payload.order):
        conn.execute(
            "UPDATE cards SET status = ?, position = ? WHERE id = ?",
            (payload.status, index, card_id),
        )
    conn.commit()
    return JSONResponse({"ok": True})
