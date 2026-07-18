# Índice de módulos — reconstrução do squad-log

Ordem definida pela dependência entre módulos (fundação primeiro) e pelo valor de cada um pra
missão (visibilidade e uso diário antes de agregações que dependem deles). Ver
[`../PRD.md`](../PRD.md) pro contexto da iniciativa.

Um módulo só vira "Concluído" depois de validado contra o dado real do banco atual — não só por
estar com teste passando.

| # | Módulo | Depende de | Status | Doc |
|---|--------|-----------|--------|-----|
| 1 | Fundação (auth, sessão, papéis, config/DB) | — | **Concluído** | `01-fundacao.md` |
| 2 | Timeline | 1 | **Concluído** | `02-timeline.md` |
| 3 | Kanban | 1 | **Concluído** | `03-kanban.md` |
| 4 | Roadmap | 1 | **Concluído** | `04-roadmap.md` |
| 5 | Aprendizado + Extensão de captura | 1 | **Concluído** | `05-aprendizado-extensao.md` |
| 6 | Dashboard + Radar | 2, 3, 4, 5 | **Concluído** | `06-dashboard-radar.md` |
| 7 | Servidor MCP | 2, 3, 5 | **Concluído** | `07-mcp-server.md` |
| 8 | Memorando / Sobre (novo) | todos acima | Não iniciado | `08-memorando.md` |

Cada `NN-modulo.md` é criado quando o módulo começa a ser trabalhado — não antes, pra não virar
documentação especulativa de algo ainda não revisitado de verdade. Cada um traz: propósito do
módulo, decisões e o porquê, contrato de dado, o que muda em relação à v1, e o critério de
"validado" específico daquele módulo.
