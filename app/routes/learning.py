import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user, require_user
from app.db import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

TYPES = [("curso", "Curso"), ("palestra", "Palestra"), ("livro", "Livro"), ("outro", "Outro")]


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
    person_id = _as_int(person)
    all_users = _all_users(conn)
    types_by_key = dict(TYPES)

    query = (
        "SELECT learning_items.*, users.name AS owner_name FROM learning_items "
        "JOIN users ON users.id = learning_items.user_id"
    )
    params: list = []
    if person_id:
        query += " WHERE learning_items.user_id = ?"
        params.append(person_id)
    query += " ORDER BY learning_items.consumed_at DESC"
    items = conn.execute(query, params).fetchall()

    profile_users = [u for u in all_users if not person_id or u["id"] == person_id]
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
    if type not in dict(TYPES):
        raise HTTPException(status_code=400)
    conn.execute(
        "INSERT INTO learning_items (user_id, title, type, description, link, consumed_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user["id"], title, type, description, link, consumed_at),
    )
    conn.commit()
    return RedirectResponse("/aprendizado", status_code=303)


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
