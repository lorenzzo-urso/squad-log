import pytest

from conftest import LEITOR, MEMBRO, login

from app.routes import kb
from app.routes.kb import _parse_frontmatter, _safe_segment


def test_parse_frontmatter_splits_yaml_and_body():
    text = "---\ntitle: Teste\ntags: [a, b]\n---\nCorpo do doc."
    front, body = _parse_frontmatter(text)
    assert front == {"title": "Teste", "tags": ["a", "b"]}
    assert body == "Corpo do doc."


def test_parse_frontmatter_missing_returns_empty_dict():
    front, body = _parse_frontmatter("Só corpo, sem front-matter.")
    assert front == {}
    assert body == "Só corpo, sem front-matter."


def test_safe_segment_rejects_path_traversal():
    assert not _safe_segment("..")
    assert not _safe_segment("../etc")
    assert not _safe_segment("a/b")
    assert not _safe_segment("a\\b")
    assert not _safe_segment("_index")
    assert not _safe_segment("")


def test_safe_segment_accepts_normal_slug():
    assert _safe_segment("visao-geral-migracao")
    assert _safe_segment("etl-ssis")


@pytest.fixture
def kb_content(tmp_path, monkeypatch):
    public = tmp_path / "publico"
    private = tmp_path / "privado" / "area-teste"
    public.mkdir(parents=True)
    private.mkdir(parents=True)

    (public / "tutorial-exemplo.md").write_text(
        "---\ntitle: Tutorial de teste\ndescription: um tutorial\ntags: [rede]\n---\n"
        "Conteúdo público com <script>alert(1)</script> **negrito**.",
        encoding="utf-8",
    )
    (private / "_index.md").write_text(
        "---\ntitle: Área de Teste\ndescription: visão geral\n---\nIntro da área.",
        encoding="utf-8",
    )
    (private / "doc-privado.md").write_text(
        "---\ntitle: Doc privado\ndescription: interno\n---\nConteúdo interno.",
        encoding="utf-8",
    )

    monkeypatch.setattr(kb, "PUBLIC_DIR", public)
    monkeypatch.setattr(kb, "PRIVATE_DIR", tmp_path / "privado")
    return tmp_path


def test_tutoriais_list_is_public_without_login(client, kb_content):
    response = client.get("/tutoriais")
    assert response.status_code == 200
    assert "Tutorial de teste" in response.text


def test_tutorial_detail_renders_sanitized_body(client, kb_content):
    response = client.get("/tutoriais/tutorial-exemplo")
    assert response.status_code == 200
    assert "<strong>negrito</strong>" in response.text
    assert "<script>alert(1)</script>" not in response.text


def test_tutorial_detail_rejects_path_traversal(client, kb_content):
    response = client.get("/tutoriais/..%2f..%2fapp%2fmain")
    assert response.status_code == 404


def test_tutorial_detail_missing_slug_404s(client, kb_content):
    response = client.get("/tutoriais/nao-existe")
    assert response.status_code == 404


def test_kb_requires_login(client, kb_content):
    response = client.get("/kb")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_kb_lists_areas_when_logged_in(client, kb_content):
    login(client, MEMBRO)
    response = client.get("/kb")
    assert response.status_code == 200
    assert "Área de Teste" in response.text


def test_kb_area_lists_docs(client, kb_content):
    login(client, MEMBRO)
    response = client.get("/kb/area-teste")
    assert response.status_code == 200
    assert "Doc privado" in response.text


def test_kb_unknown_area_404s(client, kb_content):
    login(client, MEMBRO)
    response = client.get("/kb/nao-existe")
    assert response.status_code == 404


def test_kb_doc_detail_renders(client, kb_content):
    login(client, MEMBRO)
    response = client.get("/kb/area-teste/doc-privado")
    assert response.status_code == 200
    assert "Conteúdo interno" in response.text


def test_private_doc_never_reachable_from_public_route(client, kb_content):
    response = client.get("/tutoriais/doc-privado")
    assert response.status_code == 404


def test_docs_hub_is_public_and_lists_counts(client, kb_content):
    response = client.get("/central-de-docs")
    assert response.status_code == 200
    assert "1 tutoriais" in response.text or "tutoriais" in response.text.lower()


def test_docs_hub_recentes_excludes_private_docs_when_anonymous(client, kb_content):
    response = client.get("/central-de-docs")
    assert "Doc privado" not in response.text


def test_docs_hub_recentes_includes_private_docs_when_logged_in(client, kb_content):
    login(client, MEMBRO)
    response = client.get("/central-de-docs")
    assert "Doc privado" in response.text


def test_doc_toc_extracted_from_h2_headings(client, kb_content):
    login(client, MEMBRO)
    (kb_content / "privado" / "area-teste" / "doc-com-secoes.md").write_text(
        "---\ntitle: Doc com seções\ndescription: x\n---\n## Primeira seção\ntexto\n## Segunda seção\ntexto",
        encoding="utf-8",
    )
    response = client.get("/kb/area-teste/doc-com-secoes")
    assert response.status_code == 200
    assert 'id="primeira-secao"' in response.text
    assert 'href="#primeira-secao"' in response.text
    assert 'href="#segunda-secao"' in response.text


def test_kb_doc_sidebar_lists_sibling_docs(client, kb_content):
    login(client, MEMBRO)
    response = client.get("/kb/area-teste/doc-privado")
    assert '/kb/area-teste/doc-privado"' in response.text  # itself, in the sidebar


def test_leitor_can_read_kb(client, kb_content):
    login(client, LEITOR)
    assert client.get("/tutoriais").status_code == 200
    assert client.get("/kb").status_code == 200
    assert client.get("/kb/area-teste").status_code == 200
