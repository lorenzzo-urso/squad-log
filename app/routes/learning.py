import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_user, require_user
from app.db import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

TYPES = [
    ("curso", "Curso"),
    ("palestra", "Palestra"),
    ("livro", "Livro"),
    ("artigo", "Artigo"),
    ("noticia", "Notícia"),
    ("video", "Vídeo"),
    ("treinamento", "Treinamento"),
    ("projeto", "Projeto"),
    ("outro", "Outro"),
]


def _all_users(conn: sqlite3.Connection):
    return conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()


def _as_int(value: str) -> int | None:
    return int(value) if value else None


@router.get("/aprendizado", response_class=HTMLResponse)
def learning_list(
    request: Request,
    person: str = "",
    user=Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    all_users = _all_users(conn)
    types_by_key = dict(TYPES)

    person_id = _as_int(person)
    if not person_id:
        person_id = user["id"] if user else (all_users[0]["id"] if all_users else None)

    query = (
        "SELECT learning_items.*, users.name AS owner_name FROM learning_items "
        "JOIN users ON users.id = learning_items.user_id WHERE learning_items.user_id = ? "
        "ORDER BY learning_items.consumed_at DESC"
    )
    items = conn.execute(query, (person_id,)).fetchall() if person_id else []

    profile_users = [u for u in all_users if u["id"] == person_id]
    profiles = {u["id"]: {"name": u["name"], "items": []} for u in profile_users}
    for item in items:
        if item["user_id"] in profiles:
            profiles[item["user_id"]]["items"].append(
                {**dict(item), "type_label": types_by_key.get(item["type"], item["type"])}
            )

    return templates.TemplateResponse(
        request,
        "learning.html",
        {
            "user": user,
            "profiles": [profiles[u["id"]] for u in profile_users],
            "all_users": all_users,
            "filter_person": person_id,
        },
    )


@router.get("/aprendizado/new", response_class=HTMLResponse)
def learning_new_form(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse(
        request,
        "learning_form.html",
        {"user": user, "editing": False, "item": {"title": "", "type": "curso", "description": "", "link": "", "consumed_at": ""}, "types": TYPES},
    )


def _insert_item(conn: sqlite3.Connection, owner_id: int, title, type_, description, link, consumed_at) -> int:
    if type_ not in dict(TYPES):
        raise HTTPException(status_code=400, detail=f"Tipo inválido: {type_}")
    cur = conn.execute(
        "INSERT INTO learning_items (user_id, title, type, description, link, consumed_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (owner_id, title, type_, description, link, consumed_at),
    )
    conn.commit()
    return cur.lastrowid


@router.post("/aprendizado")
def learning_create(
    title: str = Form(...),
    type: str = Form(...),
    description: str = Form(""),
    link: str = Form(""),
    consumed_at: str = Form(...),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    # owner is always the logged-in session user — never trust a client-supplied id,
    # so a shared browser can never attribute a capture to the wrong person.
    _insert_item(conn, user["id"], title, type, description, link, consumed_at)
    return RedirectResponse("/aprendizado", status_code=303)


@router.get("/api/whoami")
def whoami(user=Depends(require_user)):
    return {"id": user["id"], "name": user["name"]}


@router.get("/api/learning")
def api_list_learning(conn: sqlite3.Connection = Depends(get_db)):
    items = conn.execute(
        "SELECT learning_items.*, users.name AS owner_name FROM learning_items "
        "JOIN users ON users.id = learning_items.user_id ORDER BY learning_items.consumed_at DESC"
    ).fetchall()
    return [dict(i) for i in items]


class CaptureBody(BaseModel):
    title: str
    type: str
    description: str = ""
    link: str = ""
    consumed_at: str


@router.post("/api/learning")
def capture_learning(
    body: CaptureBody, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)
):
    # Same rule as the web form: owner comes only from the authenticated session.
    item_id = _insert_item(
        conn, user["id"], body.title, body.type, body.description, body.link, body.consumed_at
    )
    return JSONResponse({"ok": True, "id": item_id, "owner": user["name"]})


def _require_owner_or_admin(item: sqlite3.Row, user: sqlite3.Row) -> None:
    if user["role"] != "admin" and item["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Só o autor ou um admin pode editar isso")


@router.get("/aprendizado/{item_id}/edit", response_class=HTMLResponse)
def learning_edit_form(item_id: int, request: Request, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    item = conn.execute("SELECT * FROM learning_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404)
    _require_owner_or_admin(item, user)
    return templates.TemplateResponse(
        request, "learning_form.html", {"user": user, "editing": True, "item": item, "types": TYPES}
    )


@router.post("/aprendizado/{item_id}/edit")
def learning_edit_submit(
    item_id: int,
    title: str = Form(...),
    type: str = Form(...),
    description: str = Form(""),
    link: str = Form(""),
    consumed_at: str = Form(...),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    item = conn.execute("SELECT * FROM learning_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404)
    _require_owner_or_admin(item, user)
    if type not in dict(TYPES):
        raise HTTPException(status_code=400)
    conn.execute(
        "UPDATE learning_items SET title = ?, type = ?, description = ?, link = ?, consumed_at = ? WHERE id = ?",
        (title, type, description, link, consumed_at, item_id),
    )
    conn.commit()
    return RedirectResponse("/aprendizado", status_code=303)


@router.post("/aprendizado/{item_id}/delete")
def learning_delete(item_id: int, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    item = conn.execute("SELECT * FROM learning_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404)
    _require_owner_or_admin(item, user)
    conn.execute("DELETE FROM learning_items WHERE id = ?", (item_id,))
    conn.commit()
    return RedirectResponse("/aprendizado", status_code=303)
