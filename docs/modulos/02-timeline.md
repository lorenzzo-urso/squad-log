# Módulo 2 — Timeline

Prova de entrega pro squad — a superfície mais pública, lida por qualquer pessoa na rede interna
sem login. Maior peso da missão do produto está aqui.

## Estado em 2026-07-17 (antes desta reconstrução)

- `post["body_html"] = md.markdown(post["body"])`, renderizado no template com `{{ ... | safe }}`
  — desliga o escape automático do Jinja2. `markdown` deixa HTML embutido passar direto por
  padrão.
- Upload de capa validava só tamanho (5MB), não tipo de arquivo — qualquer extensão era aceita e
  servida de volta pelo `StaticFiles`.
- Paginação, agrupamento de arquivo por ano/trimestre e busca funcionando, mas sem nenhum teste.
- Nenhum log em criar/editar/apagar post.

## O que mudou, e por quê

- **Sanitização do corpo renderizado** (`render_post_body`, novo em `app/routes/timeline.py`):
  `md.markdown()` seguido de `bleach.clean()` com lista branca de tags que markdown puro já
  produz (`p`, `strong`, `em`, listas, `blockquote`, `code`/`pre`, `h1`–`h6`, `a`, `img`, `hr`) e
  atributos (`href`/`title` em link, `src`/`alt`/`title` em imagem). `bleach` também filtra
  protocolo de URL — `javascript:` nunca passa. **Risco real, não hipotético**: qualquer uma das
  ≤4 contas autenticadas podia injetar script executando no navegador de qualquer leitor anônimo,
  incluindo o gestor que é o público-alvo da ferramenta.
- **Lista de extensão permitida no upload de capa** (`ALLOWED_COVER_EXTENSIONS`): jpg, jpeg, png,
  gif, webp. Bloqueia `.svg`/`.html` disfarçados de imagem, que o `StaticFiles` serviria de volta
  como conteúdo executável.
- **Log de auditoria** em criar/editar/apagar post, mesmo padrão do módulo 1.

## O que não mudou (decisão consciente)

- Busca em Python simples (substring sobre título/resumo/corpo em memória) — volume de posts de
  um squad de 2 pessoas não justifica SQLite FTS5 agora.
- Agrupamento de arquivo por ano/trimestre — lógica já correta, só ganhou teste.
- **Fila de aprovação (ideia levantada, não incluída)**: cogitada durante o debate deste módulo,
  mas decidida como escopo separado — não é a correção do bug de XSS (sanitização já resolve
  isso) e tem tensão real com o princípio de "jardim, não competição" da seção 5 da PRD, já que
  seria um gate de admin sobre o post do colega. Fica como ideia registrada, não implementada,
  até (se) motivo concreto aparecer.

## Testes (`tests/test_timeline.py`, 12 novos)

- `render_post_body`: remove `<script>`, remove atributo de evento (`onerror`), bloqueia URL
  `javascript:`, preserva markdown normal (heading, negrito, link).
- `_quarter_label` e `_group_archive`: rótulo e agrupamento ano→trimestre, ordem decrescente.
- Upload de capa: rejeita `.svg`, aceita `.png`.
- Post criado aparece na listagem e no detalhe com corpo sanitizado (fim a fim, via HTTP).
- Paginação: 8 posts força segunda página, link `page=2` presente.

## Validação

- `pytest`: 23/23 passando (13 do módulo 1 + 10 novos, mais os já existentes de permissão).
- Fim a fim no navegador: post criado via editor real (EasyMDE) com payload
  `<script>alert('xss')</script>` + `**negrito**` no corpo — banco guarda o texto bruto (correto,
  sanitização é na renderização, não na escrita), página renderizada mostra `<strong>negrito</strong>`
  e o script vira texto inerte, sem tag, sem execução (console limpo, nenhum alerta disparado).
  Confirmado também direto no HTML servido (`curl`).
- Dado real: não aplicável, mesma situação do módulo 1 (ambiente sem uso real ainda).

## Status

Concluído em 2026-07-17.
