from pathlib import Path

from conftest import ADMIN, LEITOR, MEMBRO, login
from fastapi.testclient import TestClient

from app.security import generate_api_token, hash_api_token, hash_password, verify_password
from app.settings import get_settings


def test_get_settings_reads_env(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DB_PATH", "somewhere/test.db")
    monkeypatch.setenv("ADMIN_EMAIL", "a@b.com")
    settings = get_settings()
    get_settings.cache_clear()
    assert settings.db_path == Path("somewhere/test.db")
    assert settings.admin_email == "a@b.com"


def test_get_settings_defaults(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("DB_PATH", raising=False)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    settings = get_settings()
    get_settings.cache_clear()
    assert settings.db_path == Path("data/db/app.db")
    assert settings.admin_email is None


def test_password_hash_roundtrip():
    password_hash, salt = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", password_hash, salt)
    assert not verify_password("wrong password", password_hash, salt)


def test_password_hash_uses_random_salt():
    hash_a, salt_a = hash_password("same-password")
    hash_b, salt_b = hash_password("same-password")
    assert salt_a != salt_b
    assert hash_a != hash_b


def test_api_token_format_and_hash():
    token = generate_api_token()
    assert token.startswith("sqlg_")
    assert hash_api_token(token) == hash_api_token(token)
    assert hash_api_token(token) != token


def test_login_with_wrong_password_returns_401(client):
    response = client.post("/login", data={"email": ADMIN["email"], "password": "wrong"})
    assert response.status_code == 401


def test_logout_clears_session(client):
    login(client, MEMBRO)
    client.post("/logout")
    response = client.get("/admin")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_leitor_can_read_but_not_create_post(client):
    login(client, LEITOR)

    listing = client.get("/timeline")
    assert listing.status_code == 200

    response = client.post(
        "/posts",
        data={"title": "t", "summary": "s", "body": "b", "published_at": "2026-07-17"},
    )
    assert response.status_code == 403


def test_leitor_can_read_but_not_create_kanban_card(client):
    login(client, LEITOR)

    board = client.get("/kanban")
    assert board.status_code == 200

    response = client.post(
        "/kanban/cards",
        data={"title": "t", "tag_ids": ["1"], "status": "idea"},
    )
    assert response.status_code == 403


def test_leitor_can_call_whoami(client):
    login(client, LEITOR)
    response = client.get("/api/whoami")
    assert response.status_code == 200
    assert response.json()["name"] == "leitor"


def test_leitor_accounts_do_not_count_toward_the_write_seat_limit(client):
    login(client, ADMIN)
    # ADMIN + MEMBRO already seeded by the fixture = 2 write seats used.
    # MAX_USERS is 4, so 2 more admin/membro accounts should fit...
    for i in range(2):
        response = client.post(
            "/admin/users",
            data={
                "name": f"extra{i}",
                "email": f"extra{i}@squad.test",
                "password": "x" * 12,
                "role": "membro",
            },
        )
        assert response.status_code == 303
    # ...at which point a 5th write account is rejected...
    response = client.post(
        "/admin/users",
        data={
            "name": "one-too-many",
            "email": "toomany@squad.test",
            "password": "x" * 12,
            "role": "membro",
        },
    )
    assert response.status_code == 400
    # ...but a leitor account still goes through, since it isn't a write seat.
    response = client.post(
        "/admin/users",
        data={
            "name": "extra-leitor",
            "email": "extra-leitor@squad.test",
            "password": "x" * 12,
            "role": "leitor",
        },
    )
    assert response.status_code == 303


def test_migrate_user_roles_preserves_existing_users_and_allows_leitor(tmp_path):
    # The `client` fixture always creates a *fresh* db with the current
    # schema, so it never actually exercises the migration path a real,
    # already-deployed database would hit. Build an old-shape table by hand.
    import sqlite3

    from app.db import _migrate_user_roles
    from app.settings import Settings

    settings = Settings(
        db_path=tmp_path / "old.db", uploads_dir=tmp_path / "uploads", admin_email=None, admin_password=None
    )
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'membro')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.execute(
        "INSERT INTO users (name, email, password_hash, password_salt, role) "
        "VALUES ('Old Admin', 'old@squad.test', 'h', 's', 'admin')"
    )
    conn.commit()

    _migrate_user_roles(conn)

    preserved = conn.execute("SELECT * FROM users WHERE email = 'old@squad.test'").fetchone()
    assert preserved is not None
    assert preserved["role"] == "admin"

    conn.execute(
        "INSERT INTO users (name, email, password_hash, password_salt, role) "
        "VALUES ('New Reader', 'reader@squad.test', 'h', 's', 'leitor')"
    )
    conn.commit()  # would raise sqlite3.IntegrityError against the old CHECK
    conn.close()


def test_unhandled_exception_returns_generic_500_not_a_stack_trace(client, monkeypatch):
    import app.routes.timeline as timeline_routes
    from app.main import app as fastapi_app

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(timeline_routes, "_all_users", boom)

    # `client` (raise_server_exceptions=True, the default) is what every
    # other test uses so a *surprise* exception fails the test loudly. Here
    # the exception is the point — we need a client that lets our handler's
    # response through instead of re-raising after it.
    error_client = TestClient(fastapi_app, follow_redirects=False, raise_server_exceptions=False)
    login(error_client, MEMBRO)

    response = error_client.get("/posts/new")

    assert response.status_code == 500
    assert response.json() == {"detail": "Erro interno"}
