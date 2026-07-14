import os
import sqlite3
from pathlib import Path

from app.security import hash_password

DB_PATH = Path(os.environ.get("DB_PATH", "data/db/app.db"))
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "data/uploads"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'membro')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tech_tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    body TEXT NOT NULL,
    cover_path TEXT,
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS post_coauthors (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('idea', 'doing', 'done')),
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS card_responsibles (
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (card_id, user_id)
);

CREATE TABLE IF NOT EXISTS card_tags (
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    tech_tag_id INTEGER NOT NULL REFERENCES tech_tags(id),
    PRIMARY KEY (card_id, tech_tag_id)
);

CREATE TABLE IF NOT EXISTS learning_items (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('curso', 'palestra', 'livro', 'outro')),
    description TEXT,
    link TEXT,
    consumed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS roadmap_items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned', 'doing', 'shipped')),
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        _migrate_card_tags(conn)
        _seed_admin(conn)
        _seed_default_tags(conn)
    finally:
        conn.close()


def _migrate_card_tags(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(cards)")}
    if "tech_tag_id" not in columns:
        return
    conn.execute(
        "INSERT OR IGNORE INTO card_tags (card_id, tech_tag_id) "
        "SELECT id, tech_tag_id FROM cards WHERE tech_tag_id IS NOT NULL"
    )
    conn.execute("ALTER TABLE cards DROP COLUMN tech_tag_id")
    conn.commit()


def _seed_admin(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if row["n"] > 0:
        return
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        return
    password_hash, salt = hash_password(password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash, password_salt, role) "
        "VALUES (?, ?, ?, ?, 'admin')",
        ("Admin", email, password_hash, salt),
    )
    conn.commit()


def _seed_default_tags(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM tech_tags").fetchone()
    if row["n"] > 0:
        return
    conn.executemany(
        "INSERT INTO tech_tags (name) VALUES (?)",
        [("Dados",), ("IA",), ("Integração",), ("Slack",)],
    )
    conn.commit()
