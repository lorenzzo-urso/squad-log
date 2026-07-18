from conftest import ADMIN, LEITOR, MEMBRO, login

ITEM_FORM = {
    "title": "Curso de teste",
    "type": "curso",
    "description": "descrição",
    "link": "https://example.com/curso",
    "consumed_at": "2026-07-17",
}


def test_create_item_requires_valid_type(client):
    login(client, MEMBRO)
    response = client.post("/aprendizado", data={**ITEM_FORM, "type": "bogus"})
    assert response.status_code == 400


def test_create_item_rejects_javascript_url_link(client):
    login(client, MEMBRO)
    response = client.post("/aprendizado", data={**ITEM_FORM, "link": "javascript:alert(1)"})
    assert response.status_code == 400


def test_create_item_accepts_http_link(client):
    login(client, MEMBRO)
    response = client.post("/aprendizado", data=ITEM_FORM)
    assert response.status_code == 303


def test_create_item_accepts_empty_link(client):
    login(client, MEMBRO)
    response = client.post("/aprendizado", data={**ITEM_FORM, "link": ""})
    assert response.status_code == 303


def test_edit_item_also_rejects_javascript_url_link(client):
    login(client, MEMBRO)
    client.post("/aprendizado", data=ITEM_FORM)
    response = client.post(
        "/aprendizado/1/edit", data={**ITEM_FORM, "link": "javascript:alert(1)"}
    )
    assert response.status_code == 400


def test_capture_api_rejects_javascript_url_link(client):
    login(client, MEMBRO)
    response = client.post(
        "/api/learning",
        json={
            "title": "t",
            "type": "artigo",
            "link": "javascript:alert(1)",
            "consumed_at": "2026-07-17",
        },
    )
    assert response.status_code == 400


def test_item_appears_in_own_profile(client):
    login(client, MEMBRO)
    client.post("/aprendizado", data=ITEM_FORM)
    profile = client.get("/aprendizado")
    assert ITEM_FORM["title"] in profile.text


def test_only_owner_or_admin_can_edit(client):
    login(client, MEMBRO)
    client.post("/aprendizado", data=ITEM_FORM)
    client.post("/logout")

    login(client, ADMIN)
    created_by_admin = client.post("/aprendizado", data={**ITEM_FORM, "title": "Item do admin"})
    assert created_by_admin.status_code == 303
    client.post("/logout")

    login(client, MEMBRO)
    # membro trying to edit the admin's item (id=2) must be rejected
    response = client.post(
        "/aprendizado/2/edit", data={**ITEM_FORM, "title": "Hackeado"}
    )
    assert response.status_code == 403


def test_leitor_can_read_but_not_capture(client):
    login(client, LEITOR)
    profile = client.get("/aprendizado")
    assert profile.status_code == 200

    response = client.post("/aprendizado", data=ITEM_FORM)
    assert response.status_code == 403
