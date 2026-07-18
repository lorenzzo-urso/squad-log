# Módulo 6 — Dashboard + Radar

Visões agregadas somente-leitura sobre os módulos anteriores. Dashboard é visão geral do squad
(pública); Radar é o painel pessoal de quem está logado ("meus registros, meus cards").

## Estado em 2026-07-17 (antes desta reconstrução)

- Nenhuma escrita em nenhum dos dois — não há o que auditar por log aqui, diferente de todo
  módulo anterior.
- Zero teste.
- **"Cards concluídos por pessoa" no Dashboard violava o princípio da seção 5 da PRD** ("jardim,
  não competição") que a própria reconstrução já tinha registrado como pendência pra esse
  módulo: pessoas lado a lado em barras (`bar-fill`), ordenadas por quantidade decrescente —
  exatamente o formato de placar que o princípio pede pra evitar.

## O que mudou

- **`done_by_person` reordenado por nome, não por contagem** (`ORDER BY users.name ASC`), e o
  template trocou `bar-list`/`bar-fill` por um grid de `stat-tile` — o mesmo componente visual
  dos números de resumo no topo da página. Cada pessoa vira um bloco com seu número, sem barra
  comparando magnitude com a de ninguém. `max_done` (usado só pra calcular largura de barra)
  saiu do código, não tinha mais função.
- Nenhuma outra mudança de dado ou lógica — o resto do Dashboard (registros por mês, totais) e
  todo o Radar já estavam corretos e não tocam em comparação entre pessoas (Radar é
  inerentemente pessoal, só mostra o que é de quem está logado).

## O que foi verificado, não mudado

- Nenhuma query usa dado vindo de request interpolado direto em SQL — sem risco de injeção.
- Radar filtra por `user["id"]` vindo da sessão autenticada, nunca de parâmetro de request —
  ninguém vê radar de outra pessoa.

## Testes (`tests/test_dashboard_radar.py`, 6 novos)

- Dashboard acessível sem login; totais refletem dado real.
- "Cards concluídos por pessoa" não tem mais `bar-fill` no HTML — trava por teste, não só por
  convenção.
- Radar exige login; mostra só posts/cards de quem está logado, não vaza dado de outra pessoa.
- Papel `leitor` consegue ver os dois.

## Validação

- `pytest`: 59/59 passando.
- Fim a fim no navegador: dashboard com dado real (1 post, 1 card concluído) renderiza os totais
  certos e "Cards concluídos por pessoa" aparece como bloco único, mesmo estilo visual dos
  cartões de resumo do topo — confirmado por captura de tela, não só por leitura de HTML.
- Dado real: não aplicável, mesma situação dos módulos anteriores.

## Status

Concluído em 2026-07-17.
