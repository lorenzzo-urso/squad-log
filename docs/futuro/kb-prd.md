> Arquivado em 2026-07-17, movido de `Downloads/`. Iniciativa futura — "Base de conhecimento e
> demais módulos do 'cockpit'" já estava reservada como fora de escopo desta reconstrução (ver
> [`../PRD.md`](../PRD.md), seção 3).
>
> **Atualização 2026-07-17, mesmo dia**: Lorenzzo decidiu construir o P0 antes do módulo 8
> (Memorando) terminar — trazido de propósito, planejado antes de um dia difícil, não impulso.
> P0 implementado nesta mesma sessão: ver seção "Status de implementação" no fim deste arquivo.

# PRD — Base de Conhecimento (KB) do squad-log

**Status:** rascunho, pós-ideação — nada construído ainda.
**Autor:** Lorenzzo Urso (com Claude)
**Data:** 2026-07-17

## Problem Statement

O trabalho técnico do squad — processos, decisões de arquitetura, "como isso foi construído e por quê" — hoje só existe na cabeça de quem fez, espalhado em cards do Kanban (curto, sem contexto) ou implícito no código. Não existe um lugar dedicado pra documentação densa e duradoura, separado do registro de atividade datado que a Timeline já cobre bem. Isso tem dois custos: (1) conhecimento técnico se perde quando ninguém escreve, e reconstruir leva tempo toda vez que precisa; (2) não existe um jeito simples de compartilhar "como fazer coisas comuns" com quem não é do squad (outras áreas, novos gestores), sem misturar isso com o registro interno de entregas.

## Goals

1. Squad tem um lugar único pra documentação técnica viva (arquitetura, processos, decisões) — não um registro de eventos passados, mas conteúdo que se atualiza conforme o sistema muda.
2. Qualquer pessoa da rede interna consegue achar e seguir um tutorial simples sem precisar de login ou perguntar pro squad.
3. Escrever um doc novo não exige decisão editorial nenhuma além de "que área isso pertence" — o atrito de contribuir cai a quase zero.
4. Nenhuma informação privada vaza pro lado público por erro de configuração — a separação é estrutural, não uma checkbox que alguém esquece de marcar.
5. A KB cresce sem virar um cemitério de arquivos — em 6+ meses ainda dá pra achar as coisas.

## Non-Goals

- **Não fica pública na internet.** Tudo dentro da rede da empresa, mesma decisão já tomada pro MCP — não é escopo desta versão nem de versões futuras sem decisão explícita nova.
- **Não fica em banco de dados.** Conteúdo é markdown versionado em git, de propósito (histórico de diffs, edição fora da web, e é o que o squad já falou querer). Timeline e Changelog continuam em SQLite — são naturezas diferentes (evento datado vs. documento vivo).
- **Não inclui o agente de revisão automática de staleness.** A ideia foi validada em conversa mas fica pra uma fase futura (ver P2) — v1 não depende disso pra ser útil.
- **Não inclui reescrita autônoma de conteúdo por IA em nenhuma hipótese desta fase.** Mesmo quando o agente de revisão existir, ele propõe, não aplica sozinho — fora de escopo mudar isso agora.
- **Não inclui editor web tipo CMS pro público em v1.** Escrita é via arquivo/git (o mesmo fluxo que já usamos nesta conversa) — um formulário web pra não-técnicos escreverem tutoriais é candidato a v2, não bloqueia o lançamento.

## User Stories

**Squad member (autor)**
- Como membro do squad, quero criar um doc técnico numa área existente só criando um arquivo `.md` numa pasta, pra não ter fricção nenhuma pra registrar conhecimento assim que ele existe.
- Como membro do squad, quero que a área certa já esteja óbvia (mapeada pro que a gente constrói), pra não perder tempo decidindo taxonomia toda vez que escrevo algo.
- Como membro do squad, quero adicionar imagens (diagramas, prints) num doc do jeito que já faço nos registros da Timeline, sem aprender um mecanismo novo.

**Squad member (leitor, privado)**
- Como membro do squad, quero abrir a área "ETL/SSIS" e ver de cara o que existe documentado ali, pra não precisar perguntar pra outra pessoa algo que já foi escrito.
- Como membro do squad, quero saber se um doc pode estar desatualizado (data da última revisão visível), pra não confiar cegamente em algo que já mudou.

**Pessoa da rede interna (leitor, público)**
- Como pessoa de outra área da empresa, quero achar um tutorial simples sem precisar de login, pra resolver algo comum sem depender do squad.
- Como pessoa de outra área, quero filtrar tutoriais por categoria/tag, pra achar rápido o que se aplica a mim.

**Admin**
- Como admin, quero ter certeza de que um doc marcado como privado nunca aparece pra quem não está logado, mesmo se eu errar alguma configuração — a garantia precisa vir da estrutura, não de mim lembrar de marcar certo.

## Requirements

### Must-Have (P0)
- **Estrutura de pastas versionada em git**: `kb/publico/*.md` e `kb/privado/<area>/*.md`, com `_index.md` como overview de cada área. *Critério de aceite:* a visibilidade de um doc é 100% determinada pela pasta onde ele está — não existe campo `visibility` que possa divergir da pasta.
- **Front-matter YAML** em todo doc: `title`, `description`, `category`/`tags`, `image`, `date`, `author`; docs privados também levam `revisado_em`. *Critério:* uma página de listagem consegue montar título+resumo+imagem+data sem precisar abrir e interpretar o corpo do markdown.
- **Rota `/tutoriais` (pública)**: lista os docs de `kb/publico/`, sem exigir login — mesma regra de acesso que Timeline/Kanban hoje (`get_current_user` opcional). Lista plana com filtro por tag/categoria e busca por texto. *Critério:* acessar `/tutoriais` deslogado mostra o conteúdo normalmente; nenhum doc de `kb/privado/` aparece ali em nenhuma circunstância.
- **Rota `/kb` (privada)**: exige login (`require_user`, mesma IAM de hoje). Navegação por área, com a página de cada área listando seus docs a partir do `_index.md`. *Critério:* acessar `/kb` deslogado redireciona pro login, igual já acontece com `/kanban/new`.
- **Renderização de doc individual**: markdown → HTML reaproveitando a mesma lib (`markdown`) já usada nos posts da Timeline, com o front-matter usado só pro cabeçalho da página (título, data, autor), não como parte do corpo visível.
- **Imagens**: reaproveitar o mecanismo de upload que já existe (`_save_cover`/`/posts/upload-image`) — thumbnail (`image:` no front-matter) e imagens inline no corpo.
- **Guardrail de profundidade**: documentar (não necessariamente impor via código em v1) o limite de 3-4 níveis por área, pra não virar um emaranhado de subpastas.

### Nice-to-Have (P1)
- **Cross-link área ↔ Kanban/Timeline**: overview de cada área lista cards do Kanban e posts da Timeline com a mesma `tech_tag`. Depende de adicionar `tech_tags` aos posts (hoje só os cards têm) — é trabalho extra, não bloqueia v1.
- **Índice do `/kb` no modelo cookbook**: destaque dos docs mais recentes + tabela filtrável por data/tags/autor, em vez de só uma lista simples por área.
- **Indicador visual de staleness**: badge ou aviso quando `revisado_em` está velho demais (limiar a definir), mesmo sem o agente automático — só olhando a data.
- **Formulário web pra `/tutoriais`**: pessoas não-técnicas conseguirem publicar um tutorial simples sem tocar em git.

### Future Considerations (P2)
- **Agente de revisão de staleness**: job (provavelmente agendado) que compara `revisado_em` de cada doc contra sinais de atividade (git log das áreas de código relacionadas, mudanças de status no Kanban, novos posts na Timeline com a mesma tag) e sinaliza divergência — nunca reescreve sozinho, só propõe.
- **Geração automática de docs "coleção total"**: páginas que são snapshot mecânico do sistema (rotas, schema, tools do MCP) regeneradas direto do código — seguro de automatizar 100%, ao contrário do agente de revisão acima, porque a fonte de verdade é o próprio código.
- **Architecture Center** como área formal dentro de `kb/privado/arquitetura/`, com os diagramas de sistema (ex. o C4 do Loredraw) como documento-âncora, não só capa de post.

## Success Metrics

Como é uma ferramenta interna de squad pequeno (≤4 pessoas), os indicadores são de adoção/saúde do conteúdo, não os de produto SaaS:

- **Cobertura**: nº de áreas com `_index.md` preenchido (não vazio) — meta: todas as áreas ativas do Kanban têm uma overview em 30 dias após o lançamento.
- **Uso público**: nº de acessos a `/tutoriais` por pessoas fora do squad (via log de acesso simples) — indicador de que a visibilidade pro resto da empresa (objetivo original da squad-log) está funcionando também pro lado de conhecimento, não só de entregas.
- **Frescor**: % de docs privados com `revisado_em` dentro dos últimos 90 dias — mesmo sem o agente automático (P2), esse número já diz se a KB está viva ou parada.
- **Fricção de contribuição**: tempo entre "algo foi construído" (card movido pra "Concluído" no Kanban) e "doc relacionado existe ou foi atualizado" — qualitativo por enquanto, sem instrumentação formal em v1.

## Open Questions

- ~~**[squad]** A taxonomia de áreas nasce das `tech_tags` que já existem no Kanban, ou o squad quer revisar/expandir essa lista antes de estruturar `kb/privado/`?~~ **Decidido por Lorenzzo em 2026-07-17**: direto das `tech_tags` existentes.
- ~~**[squad]** Pessoas fora do squad podem só ler `/tutoriais`, ou eventualmente também sugerir/contribuir?~~ **Decidido por Lorenzzo em 2026-07-17**: só leitura. Mecanismo de contribuição fica sem desenhar até alguém de fora pedir de verdade.
- **[squad]** Existe um dono por área (quem resolve divergência de conteúdo daquela área), ou fica implícito por "quem escreveu por último"?
- **[engenharia]** `python-frontmatter` ou parsing manual de YAML — depende do que já está nas dependências do projeto; checar antes de decidir. — **Resolvido em 2026-07-17**: `python-frontmatter` é wrapper fino demais pra virar dependência nova. Usar `pyyaml` (essa sim justificada, ninguém reimplementa parser de YAML) + split manual em `---`, mesmo espírito das outras decisões de dependência mínima deste projeto.

## Timeline Considerations

- Sem prazo externo — é iniciativa interna, sem compromisso contratual.
- Depende logicamente de nada bloqueante: toda a infra de auth, upload de imagem e renderização de markdown já existe no projeto e será reaproveitada, não construída do zero.
- Fasear é natural aqui: P0 entrega valor sozinho (repositório de docs navegável, público e privado) mesmo sem cross-link com Kanban/Timeline ou o agente de revisão — esses dois podem vir em ondas separadas sem redesenhar nada do P0.

---

## Anexo — ideação sobre o agente de revisão de staleness (P2)

Discussão original com outro Claude sobre como o "agente de revisão" (P2) funcionaria, preservada
aqui porque documenta raciocínio real de design, não só a conclusão. Resumo do que ficou decidido:

- **Separar "detectar" de "reescrever"**: ler + comparar é seguro de automatizar (só sinaliza,
  nunca edita). Reescrever é edição de conteúdo que vira fonte de verdade — precisa de aprovação
  humana antes de virar commit. Um agente reescrevendo sozinho corre o risco de "corrigir" com
  algo plausível mas errado, e ninguém percebe porque confia no doc.
- **Um mecanismo compartilhado, não um agente por área** — a mesma lógica rodando uma vez por
  pasta (`kb/privado/etl-ssis/`, `kb/privado/integracoes/`, etc.), não N agentes diferentes pra
  manter.
- **Comparar contra o quê depende do tipo de doc**: docs que descrevem código dá pra comparar
  contra `git log` da área desde a última revisão. Docs de processo (sem código pra diffar) usam
  sinal de proxy — atividade tácita (cards mudando de status, posts novos com a mesma tag).
  Expõe uma lacuna real: hoje só o Kanban tem `tech_tags`, os posts da Timeline não têm nenhuma —
  se "posts relacionados mudaram" vira sinal, os posts precisam ganhar tag também.
- **Docs "coleção total" (P2, geração automática) mudam o cálculo de risco na direção oposta do
  que parece à primeira vista**: quando o artigo é regenerado direto do código (rotas, schema,
  tools), a fonte de verdade é diretamente inspecionável — não é "revisão com julgamento", é
  mais parecido com gerar OpenAPI a partir da API. Esse tipo de doc é seguro de regenerar 100%
  sempre, sem gate. O ajuste fino: um artigo desses geralmente mistura duas camadas — mecânica
  (o que existe hoje, sempre regenerável, zero risco) e narrativa (por que existe, decisões,
  trade-offs — aí volta o risco de inventar uma razão plausível que não é a real). A resposta
  robusta é separar as duas camadas dentro do mesmo doc, não tratar o doc inteiro como uma coisa
  só.
- Output do agente de revisão reaproveita superfícies que já existem (post no Changelog, item no
  Aprendizado) em vez de inventar um canal de notificação novo.

## Status de implementação

**P0 construído em 2026-07-17.** Não é readoção (não existia código antes) — construção nova,
mesmo rigor de teste e validação dos módulos da reconstrução.

- `kb/publico/*.md` e `kb/privado/<area>/*.md`, versionados em git — `kb/publico/` já tem um
  tutorial de exemplo, `kb/privado/etl-ssis/` tem `_index.md` + um doc, ambos reais, não
  placeholder vazio.
- `app/routes/kb.py`: parsing de front-matter (`pyyaml`, sem `python-frontmatter` — decisão já
  registrada acima), 4 rotas (`/tutoriais`, `/tutoriais/{slug}`, `/kb`, `/kb/{area}`,
  `/kb/{area}/{slug}`), reaproveitando `render_post_body` (o sanitizador `bleach` do módulo 2 da
  reconstrução) pra renderizar o corpo — mesma fronteira de confiança, mesma proteção.
- **Guarda contra path traversal**: `area`/`slug` vêm da URL direto pra um caminho de arquivo —
  `_safe_segment()` rejeita `..`, `/`, `\`, string vazia e `_index` antes de tocar no
  filesystem. Testado especificamente (`test_tutorial_detail_rejects_path_traversal`).
- **Visibilidade estrutural, não campo**: rota pública só lê `kb/publico/`, rota privada só lê
  `kb/privado/`, sem jeito de um doc de uma pasta aparecer pela rota da outra — testado
  (`test_private_doc_never_reachable_from_public_route`).
- Templates novos (`kb_tutoriais.html`, `kb_doc.html`, `kb_areas.html`, `kb_area.html`)
  reaproveitando componentes visuais já existentes (`post-card`, `stat-tile`, `tag`) — nenhum
  CSS novo.
- Navegação: "Tutoriais" sempre visível (leitura aberta), "KB" só logado — mesmo padrão de
  "Meu radar".

**Testes**: `tests/test_kb.py`, 15 novos (front-matter, path traversal, separação
público/privado, papel `leitor`, renderização sanitizada) — 74/74 no total do projeto.

**Validação**: rodei o servidor real e confirmei fim a fim via `curl` com sessão de cookie de
verdade (login real, não mock) — página pública, listagem de área privada e doc privado, todos
renderizando conteúdo real, não só passando teste isolado. A ferramenta de navegador ficou
instável durante essa sessão (timeout em screenshot, aba nova não carregando) — não bloqueou a
validação porque o `curl` contra o mesmo servidor real cobre a mesma coisa (requisição HTTP de
verdade, sessão de verdade), só client diferente. Vale confirmar visualmente da próxima vez que
a ferramenta de navegador estiver estável.

**Ainda não implementado**: formulário web (não é P0), P1 e P2 inteiros, `kb/privado/` só tem
uma área de exemplo (o squad ainda não migrou conhecimento real pra lá).

## Reskin visual — "Central de Docs" (2026-07-18)

Lorenzzo trouxe um mockup feito no Claude Design (`claude.ai/design`, projeto "Estética Palantir
para aplicação"), importado via `DesignSync` — 7 telas num único `.dc.html`. Implementado só o
que já existia de verdade (recomendação registrada e confirmada por ele): página hub nova
(`/central-de-docs`) + reskin visual de Tutoriais, KB (áreas) e página de doc individual.
**Fora de escopo, de propósito**: "Pesquisa & Relatórios" (tela nova do mockup, sem backend, com
dado fabricado de exemplo) — fica como ideia registrada, mesma lógica de "não entra de carona".

- **Visual "blueprint"**: cards com cantos técnicos (`.blueprint` + `<i class="corner">`), fundo
  de grade na seção hero, chips de filtro. Reaproveita as variáveis CSS que o site já tinha
  (`--color-accent-100..900` etc.) — não é framework novo, é CSS puro em cima do que já existe.
- **Paleta escura própria, escopada** (`.docs-app[data-theme="dark"]`, na prática
  `:root:not([data-theme="light"]) .docs-app`): só a seção Docs ganha a paleta azul fria do
  mockup no modo escuro — Timeline/Kanban/Roadmap mantêm a paleta terracota "Classical" de
  sempre. No modo claro, Docs usa a mesma paleta do resto do site (o mockup não define override
  de claro, só de escuro).
- **Índice (TOC) automático**: `_inject_heading_ids()` extrai `<h2>` do HTML já sanitizado pelo
  `bleach` (não antes — a lista de atributos permitidos do bleach não inclui `id`, de propósito)
  e gera slug. **Bug achado e corrigido nesse processo**: slug não tratava acento — "seção"
  virava "se-o" (perdia letras), não "secao". Corrigido normalizando pra ASCII antes de
  limpar o slug.
- **Barra lateral** na página de doc privado: lista os outros docs da mesma área (só quando a
  página tem `siblings` — tutorial público não tem, KB privado tem).
- **Bug de rota achado durante o teste, antes de ir pro ar**: a Central ia nascer em `/docs` —
  colide com a documentação automática do Swagger UI que o FastAPI já serve nesse caminho.
  Renomeada pra `/central-de-docs` antes de qualquer deploy.
- **Bug de deploy achado depois do primeiro rebuild**: o `Dockerfile` nunca copiava `kb/` pra
  dentro da imagem — o módulo 5 (Base de Conhecimento) tecnicamente nunca tinha ido ao ar
  corretamente no container real do Lorenzzo até este momento, mesmo já estando "concluído" no
  código. Corrigido (`COPY kb ./kb`), rebuild, conteúdo confirmado presente no container.

Validação: 80/80 testes (6 novos: hub público/privado, extração de TOC com acento, barra
lateral). Visual confirmado por captura de tela (claro e escuro) num servidor isolado antes de
publicar; depois publicado no container real do Lorenzzo com `docker compose build && up -d` —
as duas contas de usuário sobreviveram ao rebuild, confirmado direto no banco.
