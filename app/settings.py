import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    uploads_dir: Path
    admin_email: str | None
    admin_password: str | None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        db_path=Path(os.environ.get("DB_PATH", "data/db/app.db")),
        uploads_dir=Path(os.environ.get("UPLOADS_DIR", "data/uploads")),
        admin_email=os.environ.get("ADMIN_EMAIL"),
        admin_password=os.environ.get("ADMIN_PASSWORD"),
    )
