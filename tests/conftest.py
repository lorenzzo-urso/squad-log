import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db as db_module
from app.security import hash_password
from app.settings import Settings, get_settings

ADMIN = {"email": "admin@squad.test", "password": "admin-pass-123"}
MEMBRO = {"email": "membro@squad.test", "password": "membro-pass-123"}
LEITOR = {"email": "leitor@squad.test", "password": "leitor-pass-123"}


@pytest.fixture
def client(tmp_path):
    test_settings = Settings(
        db_path=tmp_path / "test.db",
        uploads_dir=tmp_path / "uploads",
        admin_email=None,
        admin_password=None,
    )
    db_module.init_db(test_settings)

    conn = db_module.get_connection(test_settings)
    for role, creds in (("admin", ADMIN), ("membro", MEMBRO), ("leitor", LEITOR)):
        password_hash, salt = hash_password(creds["password"])
        conn.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) "
            "VALUES (?, ?, ?, ?, ?)",
            (role, creds["email"], password_hash, salt, role),
        )
    conn.commit()
    conn.close()

    from app.main import app

    # dependency_overrides is FastAPI's built-in way to swap a Depends() for
    # tests — replaces get_settings() everywhere it's injected (including
    # nested, e.g. inside get_db), no module-attribute patching needed.
    app.dependency_overrides[get_settings] = lambda: test_settings
    try:
        # No `with` block here on purpose: entering TestClient as a context
        # manager fires the app's lifespan, which calls init_db() with the
        # *real* default settings (dependency_overrides only intercepts
        # per-request Depends resolution, not a direct call inside lifespan).
        # We already initialized the test db above — skipping the context
        # manager avoids a stray real data/db/app.db getting touched.
        yield TestClient(app, follow_redirects=False)
    finally:
        app.dependency_overrides.clear()


def login(client: TestClient, creds: dict) -> None:
    response = client.post("/login", data=creds)
    assert response.status_code == 303, f"login failed: {response.text}"
