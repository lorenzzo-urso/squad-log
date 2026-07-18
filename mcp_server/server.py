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


def _unwrap(response: httpx.Response) -> dict | list:
    """r.raise_for_status() alone only gives a generic '403 Forbidden' —
    squad-log's API puts the actual reason in the JSON body (e.g. "Conta
    leitor não pode criar ou editar", "Selecione ao menos uma tag"). Surface
    that instead, so the agent (and the person reading its output) knows
    why, not just that something failed."""
    if response.is_success:
        return response.json()
    detail = None
    try:
        detail = response.json().get("detail")
    except Exception:
        pass
    raise RuntimeError(detail or f"squad-log respondeu {response.status_code}")


@mcp.tool()
def list_posts() -> list[dict]:
    """Lista os registros (posts) publicados na Timeline do squad-log."""
    return _unwrap(client.get("/api/posts"))


@mcp.tool()
def create_post(title: str, summary: str, body: str, coauthor_ids: list[int] = []) -> dict:
    """Cria um novo registro na Timeline. body é markdown. coauthor_ids são ids de usuários."""
    return _unwrap(
        client.post(
            "/api/posts",
            json={"title": title, "summary": summary, "body": body, "coauthor_ids": coauthor_ids},
        )
    )


@mcp.tool()
def update_post(
    post_id: int, title: str, summary: str, body: str, coauthor_ids: list[int] = []
) -> dict:
    """Atualiza um registro existente na Timeline. Requer a conta configurada ser admin."""
    return _unwrap(
        client.post(
            f"/api/posts/{post_id}",
            json={"title": title, "summary": summary, "body": body, "coauthor_ids": coauthor_ids},
        )
    )


@mcp.tool()
def list_cards() -> list[dict]:
    """Lista os cards do Kanban (Ideia / Em andamento / Concluído), com tags e responsáveis."""
    return _unwrap(client.get("/api/kanban/cards"))


@mcp.tool()
def create_card(
    title: str,
    tag_ids: list[int],
    description: str = "",
    responsible_ids: list[int] = [],
    status: str = "idea",
) -> dict:
    """Cria um card no Kanban. status: idea, doing ou done. tag_ids precisa ter ao menos 1 item."""
    return _unwrap(
        client.post(
            "/api/kanban/cards",
            json={
                "title": title,
                "description": description,
                "tag_ids": tag_ids,
                "responsible_ids": responsible_ids,
                "status": status,
            },
        )
    )


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
    return _unwrap(client.post(f"/api/kanban/cards/{card_id}", json=payload))


@mcp.tool()
def list_learning_items() -> list[dict]:
    """Lista os itens do Aprendizado (cursos, palestras, livros, artigos etc.) de todo o squad."""
    return _unwrap(client.get("/api/learning"))


@mcp.tool()
def create_learning_item(
    title: str, type: str, consumed_at: str, description: str = "", link: str = ""
) -> dict:
    """Adiciona um item ao Aprendizado, pra quem estiver dono do token configurado.
    type: curso, palestra, livro, artigo, noticia, video, treinamento, projeto ou outro.
    consumed_at: data no formato YYYY-MM-DD."""
    return _unwrap(
        client.post(
            "/api/learning",
            json={
                "title": title,
                "type": type,
                "description": description,
                "link": link,
                "consumed_at": consumed_at,
            },
        )
    )


if __name__ == "__main__":
    mcp.run()
