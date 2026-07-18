from conftest import ADMIN, MEMBRO, login

POST_FORM = {
    "title": "Post de teste",
    "summary": "resumo",
    "body": "corpo",
    "published_at": "2026-07-16",
}


def test_timeline_is_public_without_login(client):
    response = client.get("/timeline")
    assert response.status_code == 200


def test_anonymous_cannot_create_post(client):
    response = client.post("/posts", data=POST_FORM)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_membro_can_publish_but_not_edit_own_post(client):
    login(client, MEMBRO)
    created = client.post("/posts", data=POST_FORM)
    post_id = created.headers["location"].rsplit("/", 1)[-1]

    edit_page = client.get(f"/posts/{post_id}/edit")
    assert edit_page.status_code == 403

    delete = client.post(f"/posts/{post_id}/delete")
    assert delete.status_code == 403


def test_admin_can_edit_a_post_created_by_membro(client):
    login(client, MEMBRO)
    created = client.post("/posts", data=POST_FORM)
    post_id = created.headers["location"].rsplit("/", 1)[-1]
    client.post("/logout")

    login(client, ADMIN)
    edit_page = client.get(f"/posts/{post_id}/edit")
    assert edit_page.status_code == 200


def test_membro_cannot_reach_admin_panel(client):
    login(client, MEMBRO)
    response = client.get("/admin")
    assert response.status_code == 403
