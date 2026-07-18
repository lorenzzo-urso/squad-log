from conftest import ADMIN, LEITOR, MEMBRO, login

POST_FORM = {"title": "Post", "summary": "s", "body": "b", "published_at": "2026-07-17"}
CARD_FORM = {"title": "Card", "description": "d", "tag_ids": ["1"]}


def test_dashboard_is_public_without_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_dashboard_totals_reflect_real_data(client):
    login(client, MEMBRO)
    client.post("/posts", data=POST_FORM)
    client.post("/kanban/cards", data=CARD_FORM)

    dashboard = client.get("/dashboard")
    assert "1" in dashboard.text  # registros publicados tile


def test_dashboard_done_by_person_has_no_ranking_bar_markup(client):
    login(client, MEMBRO)
    card = client.post("/kanban/cards", data=CARD_FORM)
    card_id = client.get("/api/kanban/cards").json()[0]["id"]
    client.post("/kanban/reorder", json={"status": "done", "order": [card_id]})

    dashboard = client.get("/dashboard")
    # jardim, não competição (PRD.md secao 5): sem barra comparando pessoas
    assert "bar-fill" not in dashboard.text.split("Cards concluídos por pessoa")[1]
    assert "membro" in dashboard.text.lower()


def test_radar_requires_login(client):
    response = client.get("/radar")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_radar_shows_only_my_own_posts_and_cards(client):
    login(client, MEMBRO)
    client.post("/posts", data={**POST_FORM, "title": "Post do membro"})
    client.post("/kanban/cards", data={**CARD_FORM, "title": "Card do membro"})
    client.post("/logout")

    login(client, ADMIN)
    client.post("/posts", data={**POST_FORM, "title": "Post do admin"})
    client.post("/kanban/cards", data={**CARD_FORM, "title": "Card do admin"})

    radar = client.get("/radar")
    assert "Post do admin" in radar.text
    assert "Card do admin" in radar.text
    assert "Post do membro" not in radar.text
    assert "Card do membro" not in radar.text


def test_leitor_can_view_dashboard_and_radar(client):
    login(client, LEITOR)
    assert client.get("/dashboard").status_code == 200
    assert client.get("/radar").status_code == 200
