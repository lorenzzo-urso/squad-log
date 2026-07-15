"""MCP server for squad-log: read/write access to posts (Registros) and
Kanban cards for an AI agent, over the app's existing JSON API.

Deliberately has no delete tool -- an agent can list, create and edit, but
never remove a record. Deleting stays a human-only action in the web UI.
"""
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("SQUADLOG_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.environ.get("SQUADLOG_TOKEN")

if not TOKEN:
    print("SQUADLOG_TOKEN must be set (gere um em /tokens no squad-log)", file=sys.stderr)
    sys.exit(1)

client = httpx.Client(
    base_url=BASE_URL,
    timeout=15.0,
    follow_redirects=True,
    headers={"Authorization": f"Bearer {TOKEN}"},
)

mcp = FastMCP("squad-log")


@mcp.tool()
def list_posts() -> list[dict]:
    """Lista os registros (posts) publicados na Timeline do squad-log."""
    r = client.get("/api/posts")
    r.raise_for_status()
    return r.json()


@mcp.tool()
def create_post(title: str, summary: str, body: str, coauthor_ids: list[int] = []) -> dict:
    """Cria um novo registro na Timeline. body é markdown. coauthor_ids são ids de usuários."""
    r = client.post(
        "/api/posts",
        json={"title": title, "summary": summary, "body": body, "coauthor_ids": coauthor_ids},
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def update_post(
    post_id: int, title: str, summary: str, body: str, coauthor_ids: list[int] = []
) -> dict:
    """Atualiza um registro existente na Timeline. Requer a conta configurada ser admin."""
    r = client.post(
        f"/api/posts/{post_id}",
        json={"title": title, "summary": summary, "body": body, "coauthor_ids": coauthor_ids},
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def list_cards() -> list[dict]:
    """Lista os cards do Kanban (Ideia / Em andamento / Concluído), com tags e responsáveis."""
    r = client.get("/api/kanban/cards")
    r.raise_for_status()
    return r.json()


@mcp.tool()
def create_card(
    title: str,
    tag_ids: list[int],
    description: str = "",
    responsible_ids: list[int] = [],
    status: str = "idea",
) -> dict:
    """Cria um card no Kanban. status: idea, doing ou done. tag_ids precisa ter ao menos 1 item."""
    r = client.post(
        "/api/kanban/cards",
        json={
            "title": title,
            "description": description,
            "tag_ids": tag_ids,
            "responsible_ids": responsible_ids,
            "status": status,
        },
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def update_card(
    card_id: int,
    title: str | None = None,
    description: str | None = None,
    tag_ids: list[int] | None = None,
    responsible_ids: list[int] | None = None,
    status: str | None = None,
) -> dict:
    """Atualiza um card existente. Só envia os campos que quer mudar (o resto fica como está).
    status: idea, doing ou done."""
    payload = {
        k: v
        for k, v in {
            "title": title,
            "description": description,
            "tag_ids": tag_ids,
            "responsible_ids": responsible_ids,
            "status": status,
        }.items()
        if v is not None
    }
    r = client.post(f"/api/kanban/cards/{card_id}", json=payload)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    mcp.run()
