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


def _card_tags(conn: sqlite3.Connection, card_id: int):
    return conn.execute(
        "SELECT tech_tags.id, tech_tags.name FROM card_tags "
        "JOIN tech_tags ON tech_tags.id = card_tags.tech_tag_id "
        "WHERE card_tags.card_id = ? ORDER BY tech_tags.name",
        (card_id,),
    ).fetchall()


def _as_int(value: str) -> int | None:
    return int(value) if value else None


@router.get("/kanban", response_class=HTMLResponse)
def kanban_board(
    request: Request,
    person: str = "",
    tag: str = "",
    user=Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    person_id = _as_int(person)
    tag_id = _as_int(tag)

    query = (
        "SELECT DISTINCT cards.* FROM cards "
        "LEFT JOIN card_responsibles ON card_responsibles.card_id = cards.id "
        "LEFT JOIN card_tags ON card_tags.card_id = cards.id WHERE 1=1"
    )
    params: list = []
    if person_id:
        query += " AND card_responsibles.user_id = ?"
        params.append(person_id)
    if tag_id:
        query += " AND card_tags.tech_tag_id = ?"
        params.append(tag_id)
    query += " ORDER BY cards.position ASC"
    cards = conn.execute(query, params).fetchall()

    columns = {status: [] for status, _ in COLUMNS}
    for card in cards:
        columns[card["status"]].append(
            {
                **dict(card),
                "tags": _card_tags(conn, card["id"]),
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
            "filter_person": person_id,
            "filter_tag": tag_id,
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
            "card": {"title": "", "description": ""},
            "responsible_ids": {user["id"]},
            "tag_ids": set(),
            "all_users": _all_users(conn),
            "all_tags": _tech_tags(conn),
        },
    )


def _save_tags(conn: sqlite3.Connection, card_id: int, tag_ids: list[int]) -> None:
    conn.execute("DELETE FROM card_tags WHERE card_id = ?", (card_id,))
    for tid in set(tag_ids):
        conn.execute(
            "INSERT OR IGNORE INTO card_tags (card_id, tech_tag_id) VALUES (?, ?)",
            (card_id, tid),
        )


@router.post("/kanban/cards")
def card_create(
    title: str = Form(...),
    description: str = Form(""),
    tag_ids: list[int] = Form(default=[]),
    responsible_ids: list[int] = Form(default=[]),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    if not tag_ids:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma tag")
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) AS p FROM cards WHERE status = 'idea'"
    ).fetchone()["p"]
    cur = conn.execute(
        "INSERT INTO cards (title, description, status, position) VALUES (?, ?, 'idea', ?)",
        (title, description, max_pos + 1),
    )
    card_id = cur.lastrowid
    _save_tags(conn, card_id, tag_ids)
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
    tag_ids = {t["id"] for t in _card_tags(conn, card_id)}
    return templates.TemplateResponse(
        request,
        "kanban_form.html",
        {
            "user": user,
            "editing": True,
            "card": card,
            "responsible_ids": responsible_ids,
            "tag_ids": tag_ids,
            "all_users": _all_users(conn),
            "all_tags": _tech_tags(conn),
        },
    )


@router.post("/kanban/cards/{card_id}/edit")
def card_edit_submit(
    card_id: int,
    title: str = Form(...),
    description: str = Form(""),
    tag_ids: list[int] = Form(default=[]),
    responsible_ids: list[int] = Form(default=[]),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        raise HTTPException(status_code=404)
    if not tag_ids:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma tag")
    conn.execute(
        "UPDATE cards SET title = ?, description = ? WHERE id = ?",
        (title, description, card_id),
    )
    _save_tags(conn, card_id, tag_ids)
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


# ── JSON API (used by the MCP server; intentionally no delete tool) ─────────
def _serialize_card(conn: sqlite3.Connection, card: sqlite3.Row) -> dict:
    return {
        **dict(card),
        "tags": [dict(t) for t in _card_tags(conn, card["id"])],
        "responsibles": [dict(r) for r in _card_responsibles(conn, card["id"])],
    }


class CardIn(BaseModel):
    title: str
    description: str = ""
    tag_ids: list[int]
    responsible_ids: list[int] = []
    status: str = "idea"


class CardPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    tag_ids: list[int] | None = None
    responsible_ids: list[int] | None = None
    status: str | None = None


@router.get("/api/kanban/cards")
def api_list_cards(conn: sqlite3.Connection = Depends(get_db)):
    cards = conn.execute("SELECT * FROM cards ORDER BY status, position").fetchall()
    return [_serialize_card(conn, c) for c in cards]


@router.post("/api/kanban/cards")
def api_create_card(
    body: CardIn, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)
):
    if body.status not in dict(COLUMNS):
        raise HTTPException(status_code=400, detail=f"status inválido: {body.status}")
    if not body.tag_ids:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma tag")
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) AS p FROM cards WHERE status = ?", (body.status,)
    ).fetchone()["p"]
    cur = conn.execute(
        "INSERT INTO cards (title, description, status, position) VALUES (?, ?, ?, ?)",
        (body.title, body.description, body.status, max_pos + 1),
    )
    card_id = cur.lastrowid
    _save_tags(conn, card_id, body.tag_ids)
    for uid in set(body.responsible_ids) or {user["id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO card_responsibles (card_id, user_id) VALUES (?, ?)",
            (card_id, uid),
        )
    conn.commit()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    return _serialize_card(conn, card)


@router.post("/api/kanban/cards/{card_id}")
def api_update_card(
    card_id: int,
    body: CardPatch,
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        raise HTTPException(status_code=404)

    title = body.title if body.title is not None else card["title"]
    description = body.description if body.description is not None else card["description"]
    status = body.status if body.status is not None else card["status"]
    if status not in dict(COLUMNS):
        raise HTTPException(status_code=400, detail=f"status inválido: {status}")

    position = card["position"]
    if body.status is not None and body.status != card["status"]:
        max_pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) AS p FROM cards WHERE status = ?", (status,)
        ).fetchone()["p"]
        position = max_pos + 1

    conn.execute(
        "UPDATE cards SET title = ?, description = ?, status = ?, position = ? WHERE id = ?",
        (title, description, status, position, card_id),
    )
    if body.tag_ids is not None:
        if not body.tag_ids:
            raise HTTPException(status_code=400, detail="Selecione ao menos uma tag")
        _save_tags(conn, card_id, body.tag_ids)
    if body.responsible_ids is not None:
        conn.execute("DELETE FROM card_responsibles WHERE card_id = ?", (card_id,))
        for uid in set(body.responsible_ids) or {user["id"]}:
            conn.execute(
                "INSERT OR IGNORE INTO card_responsibles (card_id, user_id) VALUES (?, ?)",
                (card_id, uid),
            )
    conn.commit()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    return _serialize_card(conn, card)
