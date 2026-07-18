import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders

from app.db import init_db
from app.routes import admin, auth, changelog, dashboard, kanban, kb, learning, radar, roadmap, timeline, tokens
from app.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings)
    yield


app = FastAPI(title="Timeline do Squad", lifespan=lifespan)

# Lets the LogBook browser extension (chrome-extension:// origin) call the
# capture API with the user's existing session cookie. Internal tool, low risk.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno"})


class NoCacheStaticMiddleware:
    """Plain ASGI middleware, not BaseHTTPMiddleware — the latter runs the
    downstream app in a separate task and, with this Starlette version,
    exceptions raised inside it skip registered exception_handlers instead
    of reaching them. Confirmed by test_fundacao.py's 500-handling test."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/static/"):
            await self.app(scope, receive, send)
            return

        async def send_with_no_cache(message):
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Cache-Control"] = "no-cache"
            await send(message)

        await self.app(scope, receive, send_with_no_cache)


app.add_middleware(NoCacheStaticMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")

app.include_router(auth.router)
app.include_router(timeline.router)
app.include_router(kanban.router)
app.include_router(roadmap.router)
app.include_router(admin.router)
app.include_router(changelog.router)
app.include_router(learning.router)
app.include_router(dashboard.router)
app.include_router(radar.router)
app.include_router(tokens.router)
app.include_router(kb.router)
