from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import UPLOADS_DIR, init_db
from app.routes import admin, auth, changelog, kanban, learning, roadmap, timeline

app = FastAPI(title="Timeline do Squad")

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Lets the LogBook browser extension (chrome-extension:// origin) call the
# capture API with the user's existing session cookie. Internal tool, low risk.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.middleware("http")
async def no_cache_static(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(timeline.router)
app.include_router(kanban.router)
app.include_router(roadmap.router)
app.include_router(admin.router)
app.include_router(changelog.router)
app.include_router(learning.router)
