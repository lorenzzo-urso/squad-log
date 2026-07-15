---
name: squad-log
description: Cria e atualiza Registros (Timeline), cards do Kanban e itens do Aprendizado no squad-log via MCP, seguindo as convenções do projeto (status, tags, tipos). Use quando o usuário pedir pra registrar algo, resumir a conversa e postar, mover/criar um card no Kanban, ou adicionar algo ao Aprendizado.
---

# squad-log

Ajuda a operar o squad-log (Timeline, Kanban, Aprendizado) durante a conversa,
usando as tools MCP `mcp__squad-log__*` já conectadas — sem precisar abrir o
navegador nem reexplicar as convenções do projeto toda vez.

Se essas tools não aparecerem disponíveis, o MCP "squad-log" não está
conectado nessa sessão — veja `mcp_server/README.md` pra configurar.

**Nunca existe delete via MCP, de propósito.** Se o usuário pedir pra apagar
algo, explique que isso só é feito na interface web.

## Registros (Timeline)

Tools: `list_posts`, `create_post`, `update_post`.

- `title`: curto e direto. `summary`: 1-2 frases. `body`: markdown.
- `update_post` só funciona se o dono do token for admin — se der 403, avise
  o usuário que precisa de conta admin pra editar um registro já publicado.
- Exemplo de uso: "resuma essa conversa e crie o registro" → sintetize a
  conversa em título + resumo + corpo markdown e chame `create_post`.

## Kanban

Tools: `list_cards`, `create_card`, `update_card`.

- `status`: `idea` (Ideia), `doing` (Em andamento), `done` (Concluído).
- `create_card` exige `tag_ids` com pelo menos 1 item. Não existe tool pra
  listar tags separadamente — descubra as tags válidas chamando `list_cards`
  e olhando o campo `tags` (id + nome) dos cards existentes. Se a tag que
  precisa não existir ainda, avise que só admin cria tags novas (em `/admin`).
- Pra mover ou editar um card existente: chame `list_cards` primeiro, ache o
  card pelo título, e só então chame `update_card` com o `card_id` certo —
  só envie os campos que estão mudando.

## Aprendizado

Tools: `list_learning_items`, `create_learning_item`.

- `type`: `curso`, `palestra`, `livro`, `artigo`, `noticia`, `video`,
  `treinamento`, `projeto` ou `outro`.
- `consumed_at`: data no formato `YYYY-MM-DD`.
- O dono do item é sempre quem gerou o token do MCP — não dá pra atribuir a
  outra pessoa por essa via (mesma regra da extensão de captura).
