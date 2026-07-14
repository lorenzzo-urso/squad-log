from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import markdown as md

from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

CHANGELOG_PATH = Path("CHANGELOG.md")


@router.get("/changelog", response_class=HTMLResponse)
def changelog(request: Request, user=Depends(get_current_user)):
    text = CHANGELOG_PATH.read_text(encoding="utf-8") if CHANGELOG_PATH.exists() else "# Changelog\n\nSem entradas ainda."
    return templates.TemplateResponse(
        request, "changelog.html", {"user": user, "body_html": md.markdown(text)}
    )
