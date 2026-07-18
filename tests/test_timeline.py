import io

from conftest import MEMBRO, login

from app.routes.timeline import _group_archive, _quarter_label, render_post_body

POST_FORM = {
    "title": "Post de teste",
    "summary": "resumo",
    "body": "corpo",
    "published_at": "2026-07-17",
}


def test_render_post_body_strips_script_tags():
    html = render_post_body("Hello <script>alert('xss')</script> world")
    # bleach strips the *tag* but keeps its text as inert content — that's
    # correct: "alert('xss')" sitting on the page as plain text never runs.
    # What must be gone is the element that would have executed it.
    assert "<script" not in html
    assert "</script>" not in html


def test_render_post_body_strips_event_handler_attribute():
    html = render_post_body('<img src="x.png" onerror="alert(1)">')
    assert "onerror" not in html


def test_render_post_body_blocks_javascript_url():
    html = render_post_body("[click me](javascript:alert(1))")
    assert "javascript:" not in html


def test_render_post_body_keeps_normal_markdown():
    html = render_post_body("# Title\n\nSome **bold** text and a [link](https://example.com).")
    assert "<h1>" in html
    assert "<strong>bold</strong>" in html
    assert 'href="https://example.com"' in html


def test_quarter_label():
    assert _quarter_label(1) == "1º trimestre"
    assert _quarter_label(4) == "2º trimestre"
    assert _quarter_label(12) == "4º trimestre"


def test_group_archive_groups_by_year_and_quarter_newest_first():
    posts = [
        {"published_at": "2026-01-15", "title": "a"},
        {"published_at": "2026-04-01", "title": "b"},
        {"published_at": "2025-11-01", "title": "c"},
    ]
    archive = _group_archive(posts)
    assert [y["year"] for y in archive] == ["2026", "2025"]
    assert archive[0]["quarters"][0]["label"] == "2º trimestre"


def test_cover_upload_rejects_disallowed_extension(client):
    login(client, MEMBRO)
    files = {"cover": ("evil.svg", io.BytesIO(b"<svg onload=alert(1)></svg>"), "image/svg+xml")}
    response = client.post("/posts", data=POST_FORM, files=files)
    assert response.status_code == 400


def test_cover_upload_accepts_allowed_extension(client):
    login(client, MEMBRO)
    files = {"cover": ("photo.png", io.BytesIO(b"fake-png-bytes"), "image/png")}
    response = client.post("/posts", data=POST_FORM, files=files)
    assert response.status_code == 303


def test_post_appears_in_timeline_and_detail_renders_sanitized_body(client):
    login(client, MEMBRO)
    body = "Update real <script>alert(1)</script> com **negrito**."
    created = client.post("/posts", data={**POST_FORM, "body": body})
    post_id = created.headers["location"].rsplit("/", 1)[-1]

    listing = client.get("/timeline")
    assert POST_FORM["title"] in listing.text

    detail = client.get(f"/timeline/{post_id}")
    assert "<strong>negrito</strong>" in detail.text
    # The page's own theme-toggle <script> is legitimate and expected here —
    # only the attacker's tag+payload combination must be gone.
    assert "<script>alert(1)</script>" not in detail.text


def test_timeline_pagination_second_page(client):
    login(client, MEMBRO)
    # 8 posts: 1 becomes the featured post, 7 remain for the grid — with
    # PER_PAGE=6 that's the smallest count that forces a second page.
    for i in range(8):
        client.post("/posts", data={**POST_FORM, "title": f"Post {i}"})

    page1 = client.get("/timeline")
    assert "page=2" in page1.text

    page2 = client.get("/timeline?page=2")
    assert page2.status_code == 200
