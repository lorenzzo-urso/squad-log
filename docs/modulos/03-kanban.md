# Módulo 3 — Kanban

Backlog operacional interno do squad. Board único, filtrado por pessoa e por
produto/tecnologia — sem múltiplos boards, conforme a PRD original.

## Estado em 2026-07-17 (antes desta reconstrução)

- Nenhum log em criar/editar/apagar/mover card ou publicar card como entrega.
- Zero teste.
- Sem bug de segurança encontrado (diferente do módulo 2) — código já estava correto.

## O que foi verificado, não mudado

- **`card_publish` passa título/descrição do card via query string** para pré-preencher o
  formulário de nova entrega (`/posts/new?title=...&body=...`). Conferido: o template usa
  `{{ post.title }}`/`{{ post.body }}` sem `| safe`, autoescape do Jinja2 protege contra XSS
  mesmo vindo de query string — não é vulnerabilidade. Risco aceito, não corrigido: descrição
  muito longa pode estourar limite de tamanho de URL do navegador. Sem gatilho concreto até
  agora para justificar trocar por um mecanismo de sessão/flash — fica documentado, não
  construído.
- **`kanban_reorder` só atualiza a coluna de destino do drag**, não a de origem — conferido em
  `board.js`: o evento `drop` lê os cards que já estão na coluna após o drag (o card arrastado já
  foi movido no DOM pelo `dragover`) e manda só essa lista. A coluna de origem fica com posição
  "furada" (ex.: 0, 2, 3), mas `ORDER BY position ASC` continua correto — não é bug visível, é
  comportamento aceitável do design atual.
- **Delete de card é `require_writer` (qualquer membro), não `require_admin`** — confirmado que
  bate com a PRD original (Kanban tem paridade total entre membros; só a Timeline restringe
  edição/exclusão a admin). Mantido como está.

## O que mudou

- Log de auditoria em criar, editar, apagar e publicar-como-entrega. **De propósito, não
  logado**: `kanban_reorder` — dispara a cada micro-interação de arrastar, logar cada uma
  afogaria o log por um sinal de baixo valor.

## Testes (`tests/test_kanban.py`, 8 novos)

- Criar card sem tag falha (400); com tag aparece no board.
- Editar e apagar card.
- Reordenar move card entre colunas corretamente.
- Publicar como entrega redireciona com título/corpo corretos (URL-encoded).
- Filtro por pessoa e por tag.
- Papel `leitor`: lê o board, não cria/edita/reordena (403).

## Validação

- `pytest`: 36/36 passando.
- Fim a fim no navegador: card criado pelo formulário real aparece no board com tag e
  responsável corretos; movido pra "Concluído" via API; "publicar como entrega" redireciona pro
  formulário de novo registro com título e corpo pré-preenchidos — confirmado direto no DOM
  (`input[name="title"].value`), não só pela URL do redirect.
- Dado real: não aplicável, mesma situação dos módulos anteriores.

## Status

Concluído em 2026-07-17.
