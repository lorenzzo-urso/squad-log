# Módulo 4 — Roadmap

Board próprio, independente do Kanban, comunica direção do setor — sem prazo, sem trimestre.

## Estado em 2026-07-17 (antes desta reconstrução)

- Nenhum log em criar/editar/apagar item.
- Zero teste.
- Módulo mais simples da reconstrução até agora: sem tags, sem responsáveis, sem API JSON pro
  MCP (o servidor MCP não toca Roadmap — só Timeline, Kanban e Aprendizado).

## O que foi verificado, não mudado

- Template usa `{{ item.description }}` sem `| safe` — autoescape do Jinja2 protege, sem risco
  de XSS. Sem bug de segurança encontrado, igual ao módulo 3.
- Lógica de posição em `item_edit_submit`: mantém a posição atual se o status não mudou, vai pro
  fim da coluna nova se mudou — já estava correta, ganhou teste.

## O que mudou

- Log de auditoria em criar, editar e apagar item.

## Testes (`tests/test_roadmap.py`, 8 novos)

- Status inválido rejeitado na criação e no reorder (400).
- Item criado aparece no board.
- Edição mantém posição quando o status não muda; ganha posição nova no fim da coluna quando
  muda.
- Apagar item.
- Reordenar move item entre colunas.
- Papel `leitor`: lê o board, não cria (403).

## Validação

- `pytest`: 44/44 passando.
- Fim a fim no navegador: item criado pelo formulário real aparece na coluna "Planejado" com
  título e descrição corretos; log de auditoria confirmado no console do servidor
  (`roadmap item created id=1 by user_id=1`).
- Dado real: não aplicável, mesma situação dos módulos anteriores.

## Status

Concluído em 2026-07-17.
