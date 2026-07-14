import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_user, require_user
from app.db import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COLUMNS = [("planned", "Planejado"), ("doing", "Em andamento"), ("shipped", "Entregue")]


@router.get("/roadmap", response_class=HTMLResponse)
def roadmap_board(request: Request, user=Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
    items = conn.execute("SELECT * FROM roadmap_items ORDER BY position ASC").fetchall()
    columns = {status: [] for status, _ in COLUMNS}
    for item in items:
        columns[item["status"]].append(dict(item))
    return templates.TemplateResponse(
        request,
        "roadmap.html",
        {"user": user, "columns": COLUMNS, "items_by_column": columns},
    )


@router.get("/roadmap/new", response_class=HTMLResponse)
def item_new_form(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse(
        request,
        "roadmap_form.html",
        {"user": user, "editing": False, "item": {"title": "", "description": ""}},
    )


@router.post("/roadmap/items")
def item_create(
    title: str = Form(...),
    description: str = Form(...),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) AS p FROM roadmap_items WHERE status = 'planned'"
    ).fetchone()["p"]
    conn.execute(
        "INSERT INTO roadmap_items (title, description, status, position) VALUES (?, ?, 'planned', ?)",
        (title, description, max_pos + 1),
    )
    conn.commit()
    return RedirectResponse("/roadmap", status_code=303)


@router.get("/roadmap/items/{item_id}/edit", response_class=HTMLResponse)
def item_edit_form(item_id: int, request: Request, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    item = conn.execute("SELECT * FROM roadmap_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "roadmap_form.html", {"user": user, "editing": True, "item": item}
    )


@router.post("/roadmap/items/{item_id}/edit")
def item_edit_submit(
    item_id: int,
    title: str = Form(...),
    description: str = Form(...),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    conn.execute(
        "UPDATE roadmap_items SET title = ?, description = ? WHERE id = ?",
        (title, description, item_id),
    )
    conn.commit()
    return RedirectResponse("/roadmap", status_code=303)


@router.post("/roadmap/items/{item_id}/delete")
def item_delete(item_id: int, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("DELETE FROM roadmap_items WHERE id = ?", (item_id,))
    conn.commit()
    return RedirectResponse("/roadmap", status_code=303)


class ReorderBody(BaseModel):
    status: str
    order: list[int]


@router.post("/roadmap/reorder")
def roadmap_reorder(payload: ReorderBody, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)):
    if payload.status not in dict(COLUMNS):
        raise HTTPException(status_code=400)
    for index, item_id in enumerate(payload.order):
        conn.execute(
            "UPDATE roadmap_items SET status = ?, position = ? WHERE id = ?",
            (payload.status, index, item_id),
        )
    conn.commit()
    return JSONResponse({"ok": True})
