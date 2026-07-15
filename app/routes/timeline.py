import math
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import markdown as md

from app.auth import get_current_user, require_admin, require_user
from app.db import UPLOADS_DIR, get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MAX_COVER_BYTES = 5 * 1024 * 1024
PER_PAGE = 6


def _all_users(conn: sqlite3.Connection):
    return conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()


def _post_coauthors(conn: sqlite3.Connection, post_id: int):
    return conn.execute(
        "SELECT users.id, users.name FROM post_coauthors "
        "JOIN users ON users.id = post_coauthors.user_id "
        "WHERE post_coauthors.post_id = ? ORDER BY users.name",
        (post_id,),
    ).fetchall()


def _quarter_label(month: int) -> str:
    return f"{(month - 1) // 3 + 1}º trimestre"


def _group_archive(posts: list[dict]) -> list[dict]:
    """Groups older posts (already sorted by published_at desc) into
    year -> quarter, for the archive section below the recent-30-days view."""
    years: dict[str, dict[str, list[dict]]] = {}
    for p in posts:
        year = p["published_at"][:4]
        month = int(p["published_at"][5:7])
        years.setdefault(year, {}).setdefault(_quarter_label(month), []).append(p)
    return [
        {
            "year": year,
            "quarters": [
                {"label": label, "posts": years[year][label]}
                for label in sorted(years[year].keys(), reverse=True)
            ],
        }
        for year in sorted(years.keys(), reverse=True)
    ]


@router.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse("/timeline", status_code=303)


@router.get("/timeline", response_class=HTMLResponse)
def timeline_list(
    request: Request,
    q: str = "",
    page: int = 1,
    user=Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    posts = conn.execute(
        "SELECT posts.*, users.name AS author_name FROM posts "
        "JOIN users ON users.id = posts.author_id "
        "ORDER BY posts.published_at DESC, posts.created_at DESC"
    ).fetchall()
    posts = [{**dict(p), "coauthors": _post_coauthors(conn, p["id"])} for p in posts]

    query = q.strip()
    filtering = bool(query)
    archive = []
    if filtering:
        needle = query.lower()
        grid_source = [
            p for p in posts if needle in (p["title"] + " " + p["summary"] + " " + p["body"]).lower()
        ]
        featured = None
    else:
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        recent = [p for p in posts if p["published_at"] >= cutoff]
        archive = _group_archive([p for p in posts if p["published_at"] < cutoff])
        grid_source = recent[1:]
        featured = recent[0] if recent else None

    total_pages = max(1, math.ceil(len(grid_source) / PER_PAGE))
    page = min(max(page, 1), total_pages)
    grid_posts = grid_source[(page - 1) * PER_PAGE : page * PER_PAGE]

    return templates.TemplateResponse(
        request,
        "timeline_list.html",
        {
            "user": user,
            "featured": featured,
            "grid_posts": grid_posts,
            "archive": archive,
            "query": query,
            "filtering": filtering,
            "empty": filtering and not grid_source,
            "page": page,
            "total_pages": total_pages,
        },
    )


@router.get("/feed.xml")
def feed(request: Request, conn: sqlite3.Connection = Depends(get_db)):
    posts = conn.execute(
        "SELECT posts.*, users.name AS author_name FROM posts "
        "JOIN users ON users.id = posts.author_id "
        "ORDER BY posts.published_at DESC, posts.created_at DESC LIMIT 20"
    ).fetchall()
    items = []
    for p in posts:
        published = datetime.strptime(p["published_at"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        items.append({**dict(p), "pub_date": format_datetime(published)})
    return templates.TemplateResponse(
        request,
        "feed.xml",
        {"posts": items, "base_url": str(request.base_url)},
        media_type="application/rss+xml",
    )


@router.get("/posts/new", response_class=HTMLResponse)
def post_new_form(
    request: Request,
    title: str = "",
    body: str = "",
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    return templates.TemplateResponse(
        request,
        "post_form.html",
        {
            "user": user,
            "editing": False,
            "post": {
                "title": title,
                "summary": "",
                "body": body,
                "published_at": datetime.now().strftime("%Y-%m-%d"),
            },
            "coauthor_ids": set(),
            "all_users": [u for u in _all_users(conn) if u["id"] != user["id"]],
        },
    )


def _save_cover(cover: Optional[UploadFile]) -> Optional[str]:
    if not cover or not cover.filename:
        return None
    contents = cover.file.read()
    if len(contents) > MAX_COVER_BYTES:
        raise HTTPException(status_code=400, detail="Imagem maior que 5MB")
    ext = Path(cover.filename).suffix
    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOADS_DIR / filename).write_bytes(contents)
    return filename


@router.post("/posts/upload-image")
def upload_inline_image(image: UploadFile, user=Depends(require_user)):
    filename = _save_cover(image)
    if not filename:
        raise HTTPException(status_code=400, detail="Nenhuma imagem enviada")
    return {"url": f"/uploads/{filename}"}


@router.post("/posts")
def post_create(
    request: Request,
    title: str = Form(...),
    summary: str = Form(...),
    body: str = Form(...),
    published_at: str = Form(...),
    coauthor_ids: list[int] = Form(default=[]),
    cover: Optional[UploadFile] = None,
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    cover_path = _save_cover(cover)
    cur = conn.execute(
        "INSERT INTO posts (title, summary, body, cover_path, author_id, published_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, summary, body, cover_path, user["id"], published_at),
    )
    post_id = cur.lastrowid
    for uid in set(coauthor_ids) - {user["id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO post_coauthors (post_id, user_id) VALUES (?, ?)",
            (post_id, uid),
        )
    conn.commit()
    return RedirectResponse(f"/timeline/{post_id}", status_code=303)


@router.get("/timeline/{post_id}", response_class=HTMLResponse)
def post_detail(post_id: int, request: Request, user=Depends(get_current_user), conn: sqlite3.Connection = Depends(get_db)):
    post = conn.execute(
        "SELECT posts.*, users.name AS author_name FROM posts "
        "JOIN users ON users.id = posts.author_id WHERE posts.id = ?",
        (post_id,),
    ).fetchone()
    if not post:
        raise HTTPException(status_code=404)
    post = {**dict(post), "coauthors": _post_coauthors(conn, post_id)}
    post["body_html"] = md.markdown(post["body"])
    print_date = datetime.now().strftime("%d/%m/%Y")
    return templates.TemplateResponse(
        request, "post_detail.html", {"user": user, "post": post, "print_date": print_date}
    )


@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
def post_edit_form(post_id: int, request: Request, user=Depends(require_admin), conn: sqlite3.Connection = Depends(get_db)):
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        raise HTTPException(status_code=404)
    coauthor_ids = {u["id"] for u in _post_coauthors(conn, post_id)}
    return templates.TemplateResponse(
        request,
        "post_form.html",
        {
            "user": user,
            "editing": True,
            "post": post,
            "coauthor_ids": coauthor_ids,
            "all_users": [u for u in _all_users(conn) if u["id"] != post["author_id"]],
        },
    )


@router.post("/posts/{post_id}/edit")
def post_edit_submit(
    post_id: int,
    title: str = Form(...),
    summary: str = Form(...),
    body: str = Form(...),
    published_at: str = Form(...),
    coauthor_ids: list[int] = Form(default=[]),
    cover: Optional[UploadFile] = None,
    user=Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        raise HTTPException(status_code=404)
    cover_path = _save_cover(cover) or post["cover_path"]
    conn.execute(
        "UPDATE posts SET title = ?, summary = ?, body = ?, cover_path = ?, published_at = ? WHERE id = ?",
        (title, summary, body, cover_path, published_at, post_id),
    )
    conn.execute("DELETE FROM post_coauthors WHERE post_id = ?", (post_id,))
    for uid in set(coauthor_ids) - {post["author_id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO post_coauthors (post_id, user_id) VALUES (?, ?)",
            (post_id, uid),
        )
    conn.commit()
    return RedirectResponse(f"/timeline/{post_id}", status_code=303)


@router.post("/posts/{post_id}/delete")
def post_delete(post_id: int, user=Depends(require_admin), conn: sqlite3.Connection = Depends(get_db)):
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    return RedirectResponse("/timeline", status_code=303)


# ── JSON API (used by the MCP server; intentionally no delete tool) ─────────
class PostIn(BaseModel):
    title: str
    summary: str
    body: str
    coauthor_ids: list[int] = []
    published_at: str | None = None  # YYYY-MM-DD; defaults to today if omitted


@router.get("/api/posts")
def api_list_posts(conn: sqlite3.Connection = Depends(get_db)):
    posts = conn.execute(
        "SELECT posts.*, users.name AS author_name FROM posts "
        "JOIN users ON users.id = posts.author_id ORDER BY posts.created_at DESC"
    ).fetchall()
    return [
        {**dict(p), "coauthors": [dict(c) for c in _post_coauthors(conn, p["id"])]}
        for p in posts
    ]


@router.post("/api/posts")
def api_create_post(
    body: PostIn, user=Depends(require_user), conn: sqlite3.Connection = Depends(get_db)
):
    published_at = body.published_at or datetime.now().strftime("%Y-%m-%d")
    cur = conn.execute(
        "INSERT INTO posts (title, summary, body, author_id, published_at) VALUES (?, ?, ?, ?, ?)",
        (body.title, body.summary, body.body, user["id"], published_at),
    )
    post_id = cur.lastrowid
    for uid in set(body.coauthor_ids) - {user["id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO post_coauthors (post_id, user_id) VALUES (?, ?)", (post_id, uid)
        )
    conn.commit()
    return {"ok": True, "id": post_id}


@router.post("/api/posts/{post_id}")
def api_update_post(
    post_id: int,
    body: PostIn,
    user=Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
):
    # only admin, same rule as the web form -- a published record isn't
    # editable by just anyone, MCP included.
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        raise HTTPException(status_code=404)
    published_at = body.published_at or post["published_at"]
    conn.execute(
        "UPDATE posts SET title = ?, summary = ?, body = ?, published_at = ? WHERE id = ?",
        (body.title, body.summary, body.body, published_at, post_id),
    )
    conn.execute("DELETE FROM post_coauthors WHERE post_id = ?", (post_id,))
    for uid in set(body.coauthor_ids) - {post["author_id"]}:
        conn.execute(
            "INSERT OR IGNORE INTO post_coauthors (post_id, user_id) VALUES (?, ?)", (post_id, uid)
        )
    conn.commit()
    return {"ok": True, "id": post_id}
