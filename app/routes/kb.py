import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user, require_user
from app.routes.timeline import render_post_body

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

KB_ROOT = Path("kb")
PUBLIC_DIR = KB_ROOT / "publico"
PRIVATE_DIR = KB_ROOT / "privado"


@dataclass
class KbDoc:
    slug: str
    title: str
    description: str
    body_html: str
    tags: list[str] = field(default_factory=list)
    date: str = ""
    author: str = ""
    image: str = ""
    area: str | None = None
    revisado_em: str | None = None
    toc: list[dict] = field(default_factory=list)


_H2_RE = re.compile(r"<h2>(.*?)</h2>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _inject_heading_ids(html: str) -> tuple[str, list[dict]]:
    """Runs *after* bleach sanitization — bleach's allow-list doesn't permit
    an id attribute on headings, and shouldn't (arbitrary user-supplied ids
    aren't worth the extra surface). These ids are generated here from
    already-sanitized text, not user input, so adding them post-hoc is safe."""
    toc: list[dict] = []
    seen: set[str] = set()

    def slugify(text: str) -> str:
        # "seção" must become "secao", not lose the ç entirely — strip
        # accents to ASCII before dropping non-alphanumerics.
        ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
        base = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "secao"
        slug, i = base, 2
        while slug in seen:
            slug = f"{base}-{i}"
            i += 1
        seen.add(slug)
        return slug

    def repl(match: re.Match) -> str:
        text = _TAG_RE.sub("", match.group(1)).strip()
        slug = slugify(text)
        toc.append({"id": slug, "title": text})
        return f'<h2 id="{slug}">{match.group(1)}</h2>'

    return _H2_RE.sub(repl, html), toc


def _safe_segment(value: str) -> bool:
    """area/slug come straight from the URL into a filesystem path — reject
    anything that could climb out of kb/ (path traversal), not just anything
    that happens to not match a real file."""
    return bool(value) and value != "_index" and "/" not in value and "\\" not in value and ".." not in value


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            front = yaml.safe_load(text[4:end]) or {}
            return front, text[end + 5:]
    return {}, text


def _load_doc(path: Path, area: str | None = None) -> KbDoc:
    front, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    # Same trust boundary as Timeline posts: human-authored markdown
    # rendered to readers who aren't the author, some of them anonymous
    # (público). Reuse the sanitizer already hardened for that in
    # timeline.py rather than trusting KB content by default.
    body_html, toc = _inject_heading_ids(render_post_body(body))
    return KbDoc(
        slug=path.stem,
        title=front.get("title") or path.stem,
        description=front.get("description") or "",
        body_html=body_html,
        tags=[str(t) for t in (front.get("tags") or [])],
        date=str(front.get("date") or ""),
        author=front.get("author") or "",
        image=front.get("image") or "",
        area=area,
        revisado_em=front.get("revisado_em"),
        toc=toc,
    )


def _list_docs(directory: Path, area: str | None = None) -> list[KbDoc]:
    if not directory.exists():
        return []
    return [
        _load_doc(p, area=area)
        for p in sorted(directory.glob("*.md"))
        if p.stem != "_index"
    ]


def _list_areas() -> list[str]:
    if not PRIVATE_DIR.exists():
        return []
    return sorted(p.name for p in PRIVATE_DIR.iterdir() if p.is_dir())


def _load_index(directory: Path, area: str | None = None) -> KbDoc | None:
    index_path = directory / "_index.md"
    if not index_path.exists():
        return None
    return _load_doc(index_path, area=area)


@router.get("/central-de-docs", response_class=HTMLResponse)
def docs_hub(request: Request, user=Depends(get_current_user)):
    tutoriais = _list_docs(PUBLIC_DIR)
    recentes = [{"title": d.title, "date": d.date, "cat": "Tutorial", "url": f"/tutoriais/{d.slug}"} for d in tutoriais]
    if user:
        for area in _list_areas():
            for d in _list_docs(PRIVATE_DIR / area, area=area):
                recentes.append({"title": d.title, "date": d.date, "cat": f"KB · {area}", "url": f"/kb/{area}/{d.slug}"})
    recentes.sort(key=lambda r: r["date"], reverse=True)

    return templates.TemplateResponse(
        request,
        "docs_hub.html",
        {
            "user": user,
            "tutoriais_count": len(tutoriais),
            "areas_count": len(_list_areas()),
            "recentes": recentes[:8],
        },
    )


@router.get("/tutoriais", response_class=HTMLResponse)
def tutoriais_list(
    request: Request, q: str = "", tag: str = "", user=Depends(get_current_user)
):
    docs = _list_docs(PUBLIC_DIR)
    all_tags = sorted({t for d in docs for t in d.tags})

    query = q.strip().lower()
    if query:
        docs = [d for d in docs if query in (d.title + " " + d.description).lower()]
    if tag:
        docs = [d for d in docs if tag in d.tags]

    return templates.TemplateResponse(
        request,
        "kb_tutoriais.html",
        {"user": user, "docs": docs, "query": q, "tag": tag, "all_tags": all_tags},
    )


@router.get("/tutoriais/{slug}", response_class=HTMLResponse)
def tutorial_detail(slug: str, request: Request, user=Depends(get_current_user)):
    if not _safe_segment(slug):
        raise HTTPException(status_code=404)
    path = PUBLIC_DIR / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=404)
    doc = _load_doc(path)
    return templates.TemplateResponse(
        request, "kb_doc.html", {"user": user, "doc": doc, "back_url": "/tutoriais", "back_label": "todos os tutoriais"}
    )


@router.get("/kb", response_class=HTMLResponse)
def kb_home(request: Request, user=Depends(require_user)):
    areas = []
    for slug in _list_areas():
        index = _load_index(PRIVATE_DIR / slug, area=slug)
        areas.append({
            "slug": slug,
            "title": index.title if index else slug,
            "description": index.description if index else "",
        })
    return templates.TemplateResponse(request, "kb_areas.html", {"user": user, "areas": areas})


@router.get("/kb/{area}", response_class=HTMLResponse)
def kb_area(area: str, request: Request, user=Depends(require_user)):
    if not _safe_segment(area) or area not in _list_areas():
        raise HTTPException(status_code=404)
    area_dir = PRIVATE_DIR / area
    index = _load_index(area_dir, area=area)
    docs = _list_docs(area_dir, area=area)
    return templates.TemplateResponse(
        request, "kb_area.html", {"user": user, "area": area, "index": index, "docs": docs}
    )


@router.get("/kb/{area}/{slug}", response_class=HTMLResponse)
def kb_doc_detail(area: str, slug: str, request: Request, user=Depends(require_user)):
    if not _safe_segment(area) or not _safe_segment(slug) or area not in _list_areas():
        raise HTTPException(status_code=404)
    path = PRIVATE_DIR / area / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=404)
    doc = _load_doc(path, area=area)
    siblings = _list_docs(PRIVATE_DIR / area, area=area)
    return templates.TemplateResponse(
        request,
        "kb_doc.html",
        {
            "user": user,
            "doc": doc,
            "back_url": f"/kb/{area}",
            "back_label": f"área {area}",
            "siblings": siblings,
        },
    )
