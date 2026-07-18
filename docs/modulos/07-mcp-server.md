# Módulo 7 — Servidor MCP

Processo separado (`mcp_server/`, venv próprio por pessoa) que expõe Registros, Kanban e
Aprendizado como tools MCP pra um agente de IA, sobre a API JSON que os módulos anteriores já
protegem. Sem tool de apagar, de propósito — decisão de design já correta, mantida.

## Estado em 2026-07-17 (antes desta reconstrução)

- `r.raise_for_status()` em toda tool — levanta `httpx.HTTPStatusError` genérico ("403
  Forbidden") sem o `detail` que o backend manda no corpo da resposta. O agente via só o código
  de status, não o motivo real (ex.: "conta leitor não pode escrever", "selecione ao menos uma
  tag").
- Zero teste, e nenhuma infraestrutura de teste existia pra esse processo (venv separado do app
  principal, propositalmente — cada pessoa instala o próprio).

## O que mudou

- `_unwrap()` novo: extrai `detail` do corpo JSON da resposta quando existe, cai pro código de
  status como último recurso. Troca `r.raise_for_status(); return r.json()` por `return
  _unwrap(r)` em todas as 8 tools — mesma mensagem de erro do backend chega até o agente agora,
  não só o código HTTP.
- `mcp_server/requirements-dev.txt` (novo, mesmo padrão do app principal) + `test_server.py` — a
  primeira infraestrutura de teste que esse processo já teve.

## O que foi verificado, não mudado

- Decisão de não ter tool de apagar — já documentada e correta, mantida.
- Autenticação via token pessoal, nunca senha — já correta.
- Nenhuma vulnerabilidade nova: as tools só repassam pra API JSON que os módulos 2, 3 e 5 já
  protegem (sanitização, validação de link, papel leitor). Esse módulo não introduz superfície
  de ataque própria — é um cliente HTTP fino.

## Testes (`mcp_server/test_server.py`, 5 novos)

Usando `httpx.MockTransport` — sem precisar de um squad-log real rodando pra testar a lógica do
próprio servidor MCP:
- Leitura devolve o JSON esperado.
- Erro com `detail` no corpo chega até quem chamou a tool.
- Erro sem corpo JSON cai pro código de status como mensagem.
- `update_card` manda só os campos que foram passados (não sobrescreve o resto com `null`).
- `create_learning_item` monta o payload certo.

## Validação

- `pytest` (mcp_server, venv próprio): 5/5 passando.
- `pytest` (app principal): 59/59 passando, nada quebrou.
- **Fim a fim contra servidor real, não mock**: subi o squad-log de verdade, criei uma conta
  `leitor` e uma `membro` pelo painel, gerei token de API real pra cada uma via `/tokens`, e
  rodei as tools do `server.py` (não um teste, o módulo de verdade) contra o servidor:
  - Token de leitor: `list_posts` funciona, `create_post` falha com a mensagem real do backend
    ("Conta leitor não pode criar ou editar") em vez de "403 Forbidden" genérico — a correção
    deste módulo, provada, mais o papel `leitor` do módulo 1, os dois trabalhando juntos.
  - Token de membro: `create_post`, `create_card` e `create_learning_item` funcionam de ponta a
    ponta, cada um atribuído à conta certa.

## Status

Concluído em 2026-07-17.
