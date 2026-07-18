import logging
import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.auth import get_current_user, require_writer
from app.db import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

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
def item_new_form(request: Request, user=Depends(require_writer)):
    return templates.TemplateResponse(
        request,
        "roadmap_form.html",
        {"user": user, "editing": False, "item": {"title": "", "description": "", "status": "planned"}, "columns": COLUMNS},
    )


@router.post("/roadmap/items")
def item_create(
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form("planned"),
    user=Depends(require_writer),
    conn: sqlite3.Connection = Depends(get_db),
):
    if status not in dict(COLUMNS):
        raise HTTPException(status_code=400)
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), -1) AS p FROM roadmap_items WHERE status = ?", (status,)
    ).fetchone()["p"]
    cur = conn.execute(
        "INSERT INTO roadmap_items (title, description, status, position) VALUES (?, ?, ?, ?)",
        (title, description, status, max_pos + 1),
    )
    conn.commit()
    logger.info("roadmap item created id=%s by user_id=%s", cur.lastrowid, user["id"])
    return RedirectResponse("/roadmap", status_code=303)


@router.get("/roadmap/items/{item_id}/edit", response_class=HTMLResponse)
def item_edit_form(item_id: int, request: Request, user=Depends(require_writer), conn: sqlite3.Connection = Depends(get_db)):
    item = conn.execute("SELECT * FROM roadmap_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "roadmap_form.html", {"user": user, "editing": True, "item": item, "columns": COLUMNS}
    )


@router.post("/roadmap/items/{item_id}/edit")
def item_edit_submit(
    item_id: int,
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form("planned"),
    user=Depends(require_writer),
    conn: sqlite3.Connection = Depends(get_db),
):
    if status not in dict(COLUMNS):
        raise HTTPException(status_code=400)
    item = conn.execute("SELECT * FROM roadmap_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404)
    if item["status"] != status:
        max_pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) AS p FROM roadmap_items WHERE status = ?", (status,)
        ).fetchone()["p"]
        position = max_pos + 1
    else:
        position = item["position"]
    conn.execute(
        "UPDATE roadmap_items SET title = ?, description = ?, status = ?, position = ? WHERE id = ?",
        (title, description, status, position, item_id),
    )
    conn.commit()
    logger.info("roadmap item edited id=%s by user_id=%s", item_id, user["id"])
    return RedirectResponse("/roadmap", status_code=303)


@router.post("/roadmap/items/{item_id}/delete")
def item_delete(item_id: int, user=Depends(require_writer), conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("DELETE FROM roadmap_items WHERE id = ?", (item_id,))
    conn.commit()
    logger.info("roadmap item deleted id=%s by user_id=%s", item_id, user["id"])
    return RedirectResponse("/roadmap", status_code=303)


class ReorderBody(BaseModel):
    status: str
    order: list[int]


@router.post("/roadmap/reorder")
def roadmap_reorder(payload: ReorderBody, user=Depends(require_writer), conn: sqlite3.Connection = Depends(get_db)):
    if payload.status not in dict(COLUMNS):
        raise HTTPException(status_code=400)
    for index, item_id in enumerate(payload.order):
        conn.execute(
            "UPDATE roadmap_items SET status = ?, position = ? WHERE id = ?",
            (payload.status, index, item_id),
        )
    conn.commit()
    return JSONResponse({"ok": True})
