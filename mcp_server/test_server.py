import os

os.environ.setdefault("SQUADLOG_TOKEN", "test-token")

import httpx
import pytest

import server


def _client_with(handler):
    return httpx.Client(base_url="http://squad-log.test", transport=httpx.MockTransport(handler))


def test_list_posts_returns_json(monkeypatch):
    def handler(request):
        assert request.url.path == "/api/posts"
        return httpx.Response(200, json=[{"id": 1, "title": "x"}])

    monkeypatch.setattr(server, "client", _client_with(handler))
    assert server.list_posts() == [{"id": 1, "title": "x"}]


def test_error_surfaces_backend_detail_message(monkeypatch):
    def handler(request):
        return httpx.Response(403, json={"detail": "Conta leitor não pode criar ou editar"})

    monkeypatch.setattr(server, "client", _client_with(handler))
    with pytest.raises(RuntimeError, match="Conta leitor não pode criar ou editar"):
        server.create_post(title="t", summary="s", body="b")


def test_error_without_json_body_falls_back_to_status_code(monkeypatch):
    def handler(request):
        return httpx.Response(500, text="internal error, not json")

    monkeypatch.setattr(server, "client", _client_with(handler))
    with pytest.raises(RuntimeError, match="500"):
        server.create_card(title="t", tag_ids=[1])


def test_update_card_only_sends_fields_that_were_set(monkeypatch):
    captured = {}

    def handler(request):
        import json

        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": 1})

    monkeypatch.setattr(server, "client", _client_with(handler))
    server.update_card(card_id=1, status="done")

    assert captured["body"] == {"status": "done"}


def test_create_learning_item_sends_expected_payload(monkeypatch):
    captured = {}

    def handler(request):
        import json

        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True, "id": 1})

    monkeypatch.setattr(server, "client", _client_with(handler))
    server.create_learning_item(title="Curso", type="curso", consumed_at="2026-07-17")

    assert captured["body"]["title"] == "Curso"
    assert captured["body"]["type"] == "curso"
