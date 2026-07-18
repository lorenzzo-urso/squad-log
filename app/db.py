import logging
import sqlite3

from fastapi import Depends

from app.security import hash_password
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'membro', 'leitor')),
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
    published_at TEXT NOT NULL DEFAULT (date('now')),
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
    type TEXT NOT NULL,
    description TEXT,
    link TEXT,
    consumed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_used_at TEXT
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


def get_connection(settings: Settings) -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db(settings: Settings = Depends(get_settings)):
    conn = get_connection(settings)
    try:
        yield conn
    finally:
        conn.close()


def init_db(settings: Settings) -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    conn = get_connection(settings)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        _migrate_card_tags(conn)
        _migrate_learning_types(conn)
        _migrate_post_published_at(conn)
        _migrate_user_roles(conn)
        _seed_admin(conn, settings)
        _seed_default_tags(conn)
    finally:
        conn.close()
    logger.info("db initialized at %s", settings.db_path)


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


def _migrate_learning_types(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'learning_items'"
    ).fetchone()
    if not row or "CHECK" not in row["sql"]:
        return
    conn.executescript(
        """
        ALTER TABLE learning_items RENAME TO learning_items_old;
        CREATE TABLE learning_items (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            link TEXT,
            consumed_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO learning_items SELECT * FROM learning_items_old;
        DROP TABLE learning_items_old;
        """
    )
    conn.commit()


def _migrate_post_published_at(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(posts)")}
    if "published_at" in columns:
        return
    conn.execute("ALTER TABLE posts ADD COLUMN published_at TEXT")
    conn.execute("UPDATE posts SET published_at = substr(created_at, 1, 10) WHERE published_at IS NULL")
    conn.commit()


def _migrate_user_roles(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    ).fetchone()
    if not row or "'leitor'" in row["sql"]:
        return
    conn.executescript(
        """
        ALTER TABLE users RENAME TO users_old;
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'membro', 'leitor')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO users SELECT * FROM users_old;
        DROP TABLE users_old;
        """
    )
    conn.commit()


def _seed_admin(conn: sqlite3.Connection, settings: Settings) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if row["n"] > 0:
        return
    if not settings.admin_email or not settings.admin_password:
        logger.warning("no ADMIN_EMAIL/ADMIN_PASSWORD set, skipping first-admin bootstrap")
        return
    password_hash, salt = hash_password(settings.admin_password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash, password_salt, role) "
        "VALUES (?, ?, ?, ?, 'admin')",
        ("Admin", settings.admin_email, password_hash, salt),
    )
    conn.commit()
    logger.info("bootstrap admin created email=%s", settings.admin_email)


def _seed_default_tags(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM tech_tags").fetchone()
    if row["n"] > 0:
        return
    conn.executemany(
        "INSERT INTO tech_tags (name) VALUES (?)",
        [("Dados",), ("IA",), ("Integração",), ("Slack",)],
    )
    conn.commit()
