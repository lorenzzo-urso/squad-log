from conftest import LEITOR, MEMBRO, login

ITEM_FORM = {"title": "Item de teste", "description": "descrição", "status": "planned"}


def test_create_item_requires_valid_status(client):
    login(client, MEMBRO)
    response = client.post("/roadmap/items", data={**ITEM_FORM, "status": "bogus"})
    assert response.status_code == 400


def test_create_item_appears_on_board(client):
    login(client, MEMBRO)
    created = client.post("/roadmap/items", data=ITEM_FORM)
    assert created.status_code == 303

    board = client.get("/roadmap")
    assert ITEM_FORM["title"] in board.text


def test_edit_item_keeps_position_when_status_unchanged(client):
    login(client, MEMBRO)
    client.post("/roadmap/items", data=ITEM_FORM)
    client.post("/roadmap/items", data={**ITEM_FORM, "title": "Segundo"})

    response = client.post(
        "/roadmap/items/1/edit",
        data={"title": "Primeiro editado", "description": "novo", "status": "planned"},
    )
    assert response.status_code == 303

    board = client.get("/roadmap")
    assert "Primeiro editado" in board.text
    assert "Segundo" in board.text


def test_edit_item_moving_column_gets_new_position_at_end(client):
    login(client, MEMBRO)
    client.post("/roadmap/items", data=ITEM_FORM)

    response = client.post(
        "/roadmap/items/1/edit",
        data={"title": ITEM_FORM["title"], "description": "novo", "status": "doing"},
    )
    assert response.status_code == 303

    board = client.get("/roadmap")
    assert ITEM_FORM["title"] in board.text


def test_delete_item(client):
    login(client, MEMBRO)
    client.post("/roadmap/items", data=ITEM_FORM)

    response = client.post("/roadmap/items/1/delete")
    assert response.status_code == 303

    board = client.get("/roadmap")
    assert ITEM_FORM["title"] not in board.text


def test_reorder_moves_item_to_another_column(client):
    login(client, MEMBRO)
    client.post("/roadmap/items", data=ITEM_FORM)

    response = client.post("/roadmap/reorder", json={"status": "shipped", "order": [1]})
    assert response.status_code == 200

    board = client.get("/roadmap")
    assert ITEM_FORM["title"] in board.text


def test_reorder_rejects_invalid_status(client):
    login(client, MEMBRO)
    response = client.post("/roadmap/reorder", json={"status": "bogus", "order": []})
    assert response.status_code == 400


def test_leitor_can_read_but_not_write(client):
    login(client, LEITOR)
    board = client.get("/roadmap")
    assert board.status_code == 200

    response = client.post("/roadmap/items", data=ITEM_FORM)
    assert response.status_code == 403
