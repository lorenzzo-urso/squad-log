# PRD — Reconstrução do Squad-log

> Este documento não substitui o [`PRD.md`](../PRD.md) original — ele descreve o produto que já
> existe e continua valendo como registro do que foi decidido na v1. Este aqui é o PRD da
> **iniciativa de reconstrução**: por que ela existe, o que muda, o que não muda, e como saber
> que terminou.

## 1. Problema

O squad-log v1 nasceu em três dias de construção rápida, orientado a iterar e resolver depois.
Funciona, cumpre a missão original (tornar um squad de 2 pessoas visível pra fora), e uma
auditoria de código mostrou decisões de segurança e arquitetura corretas — mas nasceu sem três
hábitos: testes automatizados, logging estruturado, tratamento de erro nas rotas. Além disso,
quem construiu não tem, hoje, confiança de que entende profundamente cada decisão tomada durante
essa construção rápida — o que pesa mais do que o código em si pesa.

Separado disso, mas relacionado: o squad quer, aos poucos, transformar o squad-log de "site de
visibilidade pra fora" em central de trabalho do próprio squad (módulos logados, redução de
dependência de ferramentas externas). Essa ambição é grande demais pra ser um efeito colateral
desta reconstrução — ela é nomeada aqui como direção futura, não como escopo desta iniciativa.

## 2. Objetivo desta iniciativa

Reconstruir o squad-log módulo a módulo, sobre a arquitetura e stack já validadas, até que cada
módulo tenha: teste automatizado cobrindo seu comportamento crítico, logging estruturado,
tratamento de erro nas rotas, documentação da decisão (o quê e por quê) e — critério final, o
que mais importa — compreensão real de quem construiu, ao ponto de conseguir explicar e defender
qualquer parte dele sem "ah, isso foi a IA que fez".

Não é reescrita do zero: é readoção com rigor, preservando 100% dos dados reais já existentes
(posts, cards, itens de roadmap, usuários). *(Nota: esta frase inicialmente suavizou, sem checar
antes, a escolha de "recomeço literal" que Lorenzzo tinha feito no grill. Reapresentado e
confirmado explicitamente por ele em 2026-07-17 — fica como readoção com rigor, não recomeço
literal, para todos os módulos.)*

## 3. Não-objetivos (fora de escopo desta iniciativa)

- **Troca de stack.** Python + FastAPI + SQLite + Jinja2/HTMX continuam. Nenhum módulo dela
  falhou tecnicamente — a dúvida que motivou a discussão era de maturidade percebida, não de
  limitação real, e foi resolvida em conversa (ver decisão registrada abaixo).
- **Virar SPA (React ou similar) no site público.** Único cenário em que um framework de
  cliente mais rico entra é uma "ilha" de interatividade dentro de um módulo específico que
  realmente esbarrar no teto do HTMX — decisão por módulo, não decisão geral, e não antecipada
  aqui.
- **Vault de senha próprio.** Decidido não construir — se/quando o squad quiser gerenciador de
  senha compartilhado, integra-se uma ferramenta madura já existente (ex. Vaultwarden), não se
  reimplementa.
- **Base de conhecimento e demais módulos do "cockpit" ainda não construídos.** Ficam como
  iniciativa futura, com PRD próprio, depois que esta reconstrução terminar. PRD da base de
  conhecimento já rascunhada e arquivada em
  [`futuro/kb-prd.md`](futuro/kb-prd.md) (2026-07-17) — nada implementado ainda.
  - **Item futuro registrado (2026-07-17)**: uma aba de status dentro do squad-log — monitorar
    os vários MCPs que o setor cuida, ver se estão de pé, log de erro, notificação, e
    possivelmente ferramenta de reiniciar automaticamente. Motivo de ficar fora de escopo agora:
    não é ajuste de log, é produto novo. Decisão explícita de Lorenzzo: **não adotar a stack de
    observabilidade já existente nessa máquina** (`observabilidade_*` — Grafana, Loki,
    Prometheus, Tempo, Alloy, achada via `docker volume ls`, projeto/origem desconhecida) —
    construir o próprio, alinhado com a visão de "isso vira nosso OS". Quando esse módulo entrar
    em pauta de verdade, "reiniciar processo automaticamente" merece debate próprio antes de
    codar — é categoria de risco diferente de só ler log.
- **Deploy em servidor / produção.** Hoje roda só em Docker local. Enquanto durar esta
  reconstrução, não há pressão de indisponibilidade — não existe usuário externo dependendo do
  uptime.

## 4. O que não muda

- Missão do produto (visibilidade do squad, Kanban interno, Roadmap) — ver PRD original, seção 1
  e 2, que continua válida.
- Modelo de acesso (leitura aberta na rede interna sem login, escrita restrita a até 4 contas).
- Schema de dado, exceto onde um módulo específico justificar mudança — e nesse caso, migração
  documentada no doc daquele módulo, não um "drop and recreate".

## 5. Voz e princípios de comunicação

O dado que o squad-log expõe eventualmente serve a um propósito avaliativo — é a própria missão
do produto (gestor de fora avalia entrega real). Isso não muda. O que a reconstrução adota como
princípio é separar isso da **experiência de usar a ferramenta entre os dois membros do squad**:
o dado pode ser avaliado por fora, mas a ferramenta, por dentro, não fala como um placar.

Na prática, isso significa:

- Nenhuma comparação lado a lado entre pessoas em nenhuma tela (ex.: Dashboard não mostra "cards
  concluídos por pessoa" como barras competindo entre si — número por pessoa pode existir, ranking
  ou comparação direta, não).
- Copy (textos de botão, mensagem de erro, estado vazio) escrita como convite, não como cobrança —
  revisar isso quando cada módulo chegar sua vez de reconstrução, apoiado pela skill `ux-copy`
  quando fizer sentido.
- Linguagem de crescimento em vez de linguagem de desempenho onde a escolha de palavra é livre
  (ex.: módulo de Aprendizado já tem esse tom por natureza — manter; Kanban e Timeline merecem a
  mesma atenção).

Não é sobre esconder dado. É sobre a ferramenta ser jardim por dentro, ainda que a colheita seja
vista por fora.

## 6. Como o trabalho acontece

Módulo a módulo, sem prazo fixo. Para cada módulo:

1. Ler e entender o código atual daquele módulo por completo.
2. Levantar e debater as decisões — o que fica, o que muda, por quê (registrado no doc do
   módulo).
3. Reconstruir com teste, log e tratamento de erro.
4. Validar contra o dado real do banco atual (não dado fake) — visualmente e via teste.
5. Só então o módulo entra como "concluído" no índice.

Backup do banco atual (`backup.bat`) antes de começar qualquer módulo que toque em schema.

## 7. Módulos e ordem

Ver [`modulos/00-indice.md`](modulos/00-indice.md) para a lista completa, ordem de execução e
status de cada um.

## 8. Critério de "pronto" desta iniciativa

- [ ] Todos os módulos listados no índice estão com status "concluído".
- [ ] Todo dado real do banco atual (na data de início desta iniciativa) foi validado presente
      e correto após a reconstrução de cada módulo correspondente.
- [ ] `pytest` cobre o comportamento crítico de cada módulo (não 100% de cobertura de linha —
      cobertura do que quebra caro se quebrar).
- [ ] Logging estruturado existe e captura erro de rota em produção (mesmo sem produção ainda,
      o mecanismo existe e foi testado).
- [ ] Quem construiu consegue, módulo por módulo, explicar a decisão sem abrir o código pra
      lembrar — critério subjetivo, mas é o que a iniciativa existe pra resolver.

## 9. Suposição mais arriscada

Que o ritmo "sem pressa, com carinho" não vire "sem prazo, então nunca termina". Sem servidor em
produção e sem colega pressionando por deadline, o risco real não é pressa — é a iniciativa
esfriar antes do módulo 3. Mitigação sugerida: fechar um módulo por sessão de trabalho, do início
ao "validado", em vez de abrir vários em paralelo.
