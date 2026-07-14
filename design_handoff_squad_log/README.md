# Handoff: squad-log — site completo (Timeline, Post, Kanban, Roadmap, Login)

## Overview
Redesign completo da aplicação **squad-log** (repo `Non-Systematic-Magic/squad-log`): timeline de registros do squad, página de post, kanban de backlog, roadmap do setor e login. A estrutura de páginas segue o blog do Excalidraw+ (referência do PRD); o visual segue o design system **Classical** — editorial, tipografia serifada, hairlines, cor aplicada como traço (nunca preenchimento) — com texturas de hachura/meio-tom (referência estética: mangá Frieren, tinta sobre papel).

## About the Design Files
Os arquivos deste pacote são **referências de design criadas em HTML** — protótipos que mostram aparência e comportamento pretendidos, não código de produção. A tarefa é **recriar estes designs no ambiente existente do codebase alvo**: FastAPI + Jinja2 + CSS estático (`app/templates/*.html` + `app/static/style.css`), sem SPA, conforme o PRD do repo. Substitua o conteúdo de `style.css` pelos tokens/estilos abaixo e reescreva os templates Jinja2 mantendo rotas, nomes de campos e fluxos já existentes (`base.html`, `timeline_list.html`, `post_detail.html`, `kanban.html`, `kanban_form.html`, `roadmap.html`, `login.html`). O drag & drop existente em `app/static/board.js` continua válido — só as classes CSS mudam de estilo, não de nome, se preferir.

- `Squad-log Site.dc.html` — protótipo interativo (todas as telas). Abra no navegador para navegar.
- `styles.css` — o stylesheet do design system Classical, fonte da verdade de todos os tokens. Pode ser adaptado quase inteiro para `app/static/style.css`.

## Fidelity
**High-fidelity (hifi).** Cores, tipografia, espaçamentos e estados são finais. Recriar pixel-perfect.

## Design Tokens (copiar para :root do style.css)
Fontes (Google Fonts): `Cormorant Garamond` (400;600) para headings, `Lora` (400;600) para corpo.
```css
--color-bg:#f3f2f2; --color-surface:#eae9e9; --color-text:#201f1d;
--color-accent:#b68235; --color-divider:color-mix(in srgb,#201f1d 16%,transparent);
/* ramp acento */ --color-accent-100:#fff3e4; --color-accent-200:#ffe3bf; --color-accent-400:#e1ad66; --color-accent-600:#a06f24; --color-accent-700:#7d5411; --color-accent-800:#5a3b0a;
/* ramp neutra */ --color-neutral-100:#f8f4f4; --color-neutral-300:#d7d3d3; --color-neutral-400:#bab6b6; --color-neutral-600:#7d7979; --color-neutral-700:#605d5d;
--font-heading:"Cormorant Garamond",serif; --font-body:"Lora",serif; --font-heading-weight:600;
--radius-md:4px; --shadow-sm:0 1px 2px color-mix(in srgb,#2d2b2b 14%,transparent); --shadow-md:0 3px 10px color-mix(in srgb,#2d2b2b 16%,transparent);
```
Texturas (usadas em capas placeholder, hero e rodapé):
```css
/* meio-tom (dots) */ background-image:radial-gradient(circle, color-mix(in srgb,var(--color-text) 16%,transparent) 1px, transparent 1.3px); background-size:7px 7px;
/* hachura */ background-image:repeating-linear-gradient(-45deg, color-mix(in srgb,var(--color-text) 12%,transparent) 0 1px, transparent 1px 6px);
/* hachura cruzada */ os dois repeating-linear-gradients (45deg e -45deg) sobrepostos;
```
Regras do sistema: botões são **contorno**, nunca preenchidos (primário: borda+texto `--color-accent`, hover `background:color-mix(in srgb,var(--color-accent) 12%,transparent)`); cards com borda `--color-divider` sobre fundo transparente; sombras discretas; texto acento em tamanho de parágrafo usa `--color-accent-700`; foco de teclado: `outline:2px solid var(--color-accent); outline-offset:2px`; links `color:var(--color-accent)`, `text-underline-offset:3px`. Números tabulares (`font-feature-settings:'tnum'`) em datas, contadores e numerais.

## Screens / Views

### 1. Navegação (base.html)
Sticky top, fundo `color-mix(in srgb,var(--color-bg) 92%,transparent)` + `backdrop-filter:blur(6px)`, borda inferior hairline, padding `13.8px 18.4px`, gap 18.4px.
- Brand: "squad-log" Cormorant 18px semibold + traço horizontal 22×1px na cor acento ao lado.
- Links (14px, Lora, sem sublinhado): Registros · Kanban · Roadmap. Ativo/hover: cor acento.
- Direita: link "github" com ícone (14px, `--color-neutral-700`) e:
  - deslogado: botão contorno "Entrar";
  - logado: nome do usuário (muted, 13px) + link "Sair".

### 2. Home / Timeline
- **Hero** centrado, padding 84px 40px 48px: kicker "DIÁRIO DE BORDO · VOL. I" (11px, letter-spacing .18em, uppercase, `--color-accent-700`); título "squad-log" Cormorant 64px peso 400, com a palavra "log" destacada por fundo `--color-accent-200` (padding 0 10px); parágrafo muted 15px, max-width 560px. Três "rabiscos" decorativos absolutos: retângulos pequenos com textura de dots/hachura, levemente rotacionados (−8°, 14°, 6°), um deles na cor acento.
- **Busca + filtro**: input (max-width 340px) "Buscar nos registros…" + controle segmentado Todos | Técnico | Processo | Retro (borda hairline, opção ativa com inset ring acento). Filtra o grid em tempo real; quando filtrando, o destaque some e a lista inclui todos os posts.
- **Post em destaque** (primeiro post, só sem filtro): card horizontal max-width 1180px, fundo `--color-neutral-100`, shadow-sm (hover: shadow-md). Esquerda 54%: capa (imagem do post; placeholder = textura hachura+dots com etiqueta "CAPA · ILUSTRAÇÃO DO REGISTRO" em caixinha bordada). Direita: meta (data · autor, 11px), título Cormorant 30px, resumo 14px justificado, link ghost "ler registro →".
- **Grid**: 3 colunas, gap 24px, 6 por página. Card: capa 170px (textura variando por post: dots/hachura/cruzada/linhas) com etiqueta "CAPA"; corpo padding 18–20px: meta, título Cormorant 20px, resumo 13px, rodapé com "ler registro →" (ghost) e tag do tipo (chip `--color-accent-100`/`--color-accent-800`).
- **Paginação** central: quadrados 32px; página atual com borda acento e numeral Cormorant; demais sublinhados; seta "→" acento.
- **Vazio**: "Nenhum registro encontrado para essa busca." (itálico, muted, centrado).

### 3. Post (post_detail.html)
Coluna única max-width 680px, padding 64px 32px 72px.
- "← todos os registros" (13px, neutral-700, hover acento).
- Kicker "REGISTRO Nº {n}" · título Cormorant 46px peso 400 · meta "Publicado em {data} · por {autor}" + chip do tipo · hairline.
- Corpo 16px/1.75 justificado. Figuras: moldura estilo "plate" — borda 6px `--color-surface` + outline 1px hairline, com figcaption 11px.
- Blockquote: borda esquerda 2px acento, Cormorant 22px itálico.
- H2 de seção: Cormorant 29px.
- Rodapé do artigo: hairline + botões "← todos os registros" (secondary) e "ver o roadmap →" (ghost).

### 4. Kanban (kanban.html)
Max-width 1180px, padding 56px 48px 72px.
- Toolbar: h1 "Kanban" Cormorant 44px peso 400 + legenda itálica "backlog operacional do squad" + spacer + selects "Todas as pessoas"/"Todas as tecnologias" (estilo .input) + botão "Novo card" (primary, só logado). Deslogado: linha "Leitura aberta a todos — entre para criar, arrastar e editar cards."
- Board: grid 3 colunas, gap 24px. Coluna: borda hairline, radius 4px, fundo `--color-neutral-100`, min-height 360px; cabeçalho com numeral romano I/II/III (Cormorant, acento), nome (Ideia / Em andamento / Concluído, Cormorant 19px) e contador "N cards" (11px muted, tnum).
- Card: fundo `--color-bg`, borda hairline, padding 13.8px, gap 9.2px; título Cormorant 16.5px semibold; descrição 12.5px muted (se houver); linha com chip da tecnologia + responsáveis (11px muted); logado: rodapé com hairline superior e links 11.5px "editar", "publicar como entrega" (apenas coluna Concluído), "apagar" (à direita, neutral-600). Arrastando: opacity .35, cursor grab.
- Modal novo/editar: `.dialog` 440px, fundo `--color-surface`, shadow-lg — campos Título, Descrição (textarea), Produto/tecnologia (select), Responsáveis (checkboxes com accent-color) + Cancelar (secondary) / Criar‑Salvar (primary).

### 5. Roadmap (roadmap.html)
- Hero centrado menor (54px): "Roadmap do squad" com "Roadmap" destacado em `--color-accent-200`; subtítulo muted; mesmos rabiscos decorativos.
- 3 colunas (Backlog/Planejado · Em progresso · Entregue no protótipo — usar os labels do repo: Planejado / Em andamento / Entregue), gap 40px: cabeçalho com numeral romano em círculo bordado acento 28px + título Cormorant 23px + contador; itens em lista vertical com hairline vertical à esquerda (margin-left 13px) e ponto de status sobre a linha (9px: Entregue = preenchido acento; Em andamento = borda acento; Planejado = borda `--color-neutral-400`); título Cormorant 17px + descrição 13px muted. Hover do item: tint acento 5%.

### 6. Login (login.html)
Centrado vertical, caixa 380px: traço 56×1px acento no topo, "Entrar" Cormorant 44px peso 400, subtítulo "A leitura do log é aberta a toda a rede. O login é só para quem escreve." (13.5px muted); campos Email e Senha (label 12px + .input); botão primary full-width "Entrar"; nota 11.5px "Esqueceu a senha? Fale com o admin do squad — contas são criadas manualmente (máx. 4 usuários)."

### 7. Rodapé (todas as páginas)
Fundo `#232120` com overlay de meio-tom claro (`rgba(248,244,244,.07)`, 9px), padding 44px 48px 36px, conteúdo max-width 1084px: brand + tagline "Diário de bordo público do squad. Escrito à mão, versionado no git." (12.5px, neutral-400); colunas "EXPLORAR" (Registros, Roadmap, Sobre o squad) e "CONTATO" — títulos de coluna 10px uppercase `--color-accent-400`, links 13px `--color-neutral-300`.

## Interactions & Behavior
- Busca (input) + filtro segmentado filtram os posts (título+resumo, case-insensitive); resetam a paginação.
- Paginação: 6 posts/página; troca de página rola ao topo.
- Kanban drag & drop (só logado): arrastar card sobre outro insere antes dele; sobre área vazia da coluna move para o fim da coluna; persistir via POST `/kanban/reorder` (já existe em `board.js`).
- "publicar como entrega" (coluna Concluído) → `/posts/new?title=…&body=…` pré-preenchido (fluxo já existente).
- Hovers: cards ganham shadow; links de nav e "ler registro" mudam para acento/acento-600; botões seguem os estados do sistema (tint 12% hover, 22% active).
- Transições sutis (~150ms) em sombra/cor; nada animado além disso.

## State Management (no alvo é servidor, não JS)
Sessão de login via cookie (já existe). Filtros do kanban via querystring (`?person=&tag=`, já existe). Busca/filtro da timeline: pode ser querystring (`?q=&tipo=`) server-side — o protótipo demonstra o comportamento esperado. Ordem do kanban persistida por posição (já existe).

## Assets
- Fontes: Google Fonts (Cormorant Garamond 400/600, Lora 400/600).
- Capas de post: **placeholders texturizados** no protótipo — substituir por upload real (`/data/uploads`, campo capa do post). Manter a moldura "plate" (borda 6px surface + outline hairline).
- Ícone GitHub: SVG inline (Lucide `github`). Usar Lucide para eventuais ícones.
- Sem emoji, sem gradientes coloridos; cor só como traço.

## Files
- `Squad-log Site.dc.html` — protótipo interativo de referência (Home/Timeline, Post, Kanban + modal, Roadmap, Login, estados logado/deslogado).
- `styles.css` — tokens e componentes do design system Classical (base para `app/static/style.css`).
