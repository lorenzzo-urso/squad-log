from urllib.parse import unquote

from conftest import ADMIN, LEITOR, MEMBRO, login

CARD_FORM = {"title": "Card de teste", "description": "descrição", "tag_ids": ["1"]}


def test_create_card_requires_at_least_one_tag(client):
    login(client, MEMBRO)
    response = client.post("/kanban/cards", data={"title": "sem tag", "description": ""})
    assert response.status_code == 400


def test_create_card_appears_on_board(client):
    login(client, MEMBRO)
    created = client.post("/kanban/cards", data=CARD_FORM)
    assert created.status_code == 303

    board = client.get("/kanban")
    assert CARD_FORM["title"] in board.text


def test_edit_card(client):
    login(client, MEMBRO)
    client.post("/kanban/cards", data=CARD_FORM)
    cards = client.get("/api/kanban/cards").json()
    card_id = cards[0]["id"]

    response = client.post(
        f"/kanban/cards/{card_id}/edit",
        data={"title": "Título editado", "description": "novo", "tag_ids": ["1"]},
    )
    assert response.status_code == 303

    board = client.get("/kanban")
    assert "Título editado" in board.text


def test_delete_card(client):
    login(client, MEMBRO)
    client.post("/kanban/cards", data=CARD_FORM)
    cards = client.get("/api/kanban/cards").json()
    card_id = cards[0]["id"]

    response = client.post(f"/kanban/cards/{card_id}/delete")
    assert response.status_code == 303
    assert client.get("/api/kanban/cards").json() == []


def test_reorder_moves_card_to_another_column(client):
    login(client, MEMBRO)
    client.post("/kanban/cards", data=CARD_FORM)
    card_id = client.get("/api/kanban/cards").json()[0]["id"]

    response = client.post(
        "/kanban/reorder", json={"status": "doing", "order": [card_id]}
    )
    assert response.status_code == 200

    card = client.get("/api/kanban/cards").json()[0]
    assert card["status"] == "doing"


def test_publish_redirects_to_post_form_with_card_content(client):
    login(client, MEMBRO)
    client.post("/kanban/cards", data=CARD_FORM)
    card_id = client.get("/api/kanban/cards").json()[0]["id"]

    response = client.post(f"/kanban/cards/{card_id}/publish")
    assert response.status_code == 303
    location = response.headers["location"]
    assert unquote(location) == f"/posts/new?title={CARD_FORM['title']}&body={CARD_FORM['description']}"


def test_filter_by_person_and_tag(client):
    login(client, MEMBRO)
    client.post("/kanban/cards", data=CARD_FORM)

    by_tag = client.get("/kanban?tag=1")
    assert CARD_FORM["title"] in by_tag.text

    by_other_tag = client.get("/kanban?tag=2")
    assert CARD_FORM["title"] not in by_other_tag.text


def test_person_filter_excludes_users_with_no_cards(client):
    login(client, ADMIN)
    # admin creates the card but assigns it to membro, not to themselves —
    # admin should never show up as a filter option with zero cards of their own
    client.post(
        "/kanban/cards",
        data={**CARD_FORM, "responsible_ids": ["2"]},  # membro seeded as id 2
    )
    board = client.get("/kanban")
    person_select = board.text.split('name="person"')[1].split("</select>")[0]
    assert 'value="2"' in person_select  # membro, has a card
    assert 'value="1"' not in person_select  # admin, has none


def test_leitor_can_read_board_but_not_write(client):
    login(client, LEITOR)
    board = client.get("/kanban")
    assert board.status_code == 200

    response = client.post("/kanban/cards", data=CARD_FORM)
    assert response.status_code == 403

    response = client.post("/kanban/reorder", json={"status": "doing", "order": []})
    assert response.status_code == 403
