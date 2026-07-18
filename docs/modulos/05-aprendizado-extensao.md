# Módulo 5 — Aprendizado + Extensão de captura

Registro pessoal de cursos, palestras, livros e afins por pessoa — base pro PDI. A extensão de
navegador (`extension/`) captura página e manda direto pro Aprendizado, autenticada pela sessão
de quem estiver logado.

## Estado em 2026-07-17 (antes desta reconstrução)

- Nenhum log em criar/editar/apagar item.
- Zero teste no backend.
- **Duas vulnerabilidades reais encontradas** — a maior densidade de achado de segurança até
  agora nesta reconstrução.

## Vulnerabilidades encontradas e corrigidas

### 1. Campo `link` sem validação de esquema (backend)

`<a href="{{ item.link }}">` no template, campo cru vindo direto do formulário ou da extensão,
sem passar por markdown/sanitização nenhuma (diferente do corpo de post, que já tinha `bleach`
desde o módulo 2). Qualquer uma das contas com escrita podia salvar
`link = "javascript:alert(1)"`, e qualquer pessoa (a leitura é aberta, igual todo o resto do
squad-log) que clicasse em "ver link" executava o payload no contexto da página.

**Correção**: `_validate_link()` em `app/routes/learning.py` — só aceita link vazio ou começando
com `http://`/`https://`, aplicado nos três caminhos de escrita (form web, edição, API de
captura da extensão) via `_insert_item` e no `UPDATE` de edição.

### 2. XSS via `innerHTML` no popup da extensão (mais grave que #1)

`extension/popup/popup.js` tinha três pontos construindo HTML por concatenação de string com
dado não confiável — `item.title` (raspado de página arbitrária: `document.title`, meta tags
OpenGraph) e `entry.title`/mensagens de erro que embutem esse mesmo título — direto em
`el.innerHTML = \`...${title}...\``. Fluxo de exploração real: navegar numa página com `<title>`
malicioso → capturar com a extensão → abrir a fila → o payload executa **dentro do popup da
extensão**, que tem acesso a `chrome.storage` (as chaves de API do Claude/OpenAI guardadas ali).
Isso é pior que o #1 porque o blast radius inclui as chaves de IA, não só a sessão do squad-log.

Um terceiro ponto (`renderConnections`, sugestões de conexão por IA) tinha o mesmo padrão mas
está morto na prática hoje — `existingEntriesCache` nunca é populado (o próprio código já tinha
um comentário `ponytail:` avisando disso, à espera de um endpoint de listagem que ainda não
existe). Corrigido mesmo assim, por consistência e porque o comentário already sinaliza que vai
ser ligado no futuro.

**Correção**: os três pontos (`renderConnections`, `renderQueue`, `toast`) reconstruídos com
`document.createElement` + `.textContent`/`.title` (propriedade, não atributo em string) em vez
de template literal virando `innerHTML`. Nenhuma mudança visual — mesma estrutura, só a
construção do DOM que mudou.

## O que também mudou

- Log de auditoria em criar (form e API de captura), editar e apagar item.
- `extension/background.js`: removida marca antiga "ContentBlog" (sobra de um template anterior
  ao squad-log) do log de instalação.

## O que foi revisado, não mudado

- Chaves de API (Claude/OpenAI) armazenadas em `chrome.storage.sync`, só client-side, nunca
  enviadas pro squad-log. Padrão aceitável pra extensão de uso pessoal — não centralizar isso no
  backend seria complexidade sem necessidade real hoje.
- Extensão nunca deixa o cliente escolher o dono da captura — sempre vem da sessão autenticada
  (`credentials: 'include'`), já estava certo, comentário no próprio código confirma a decisão.

## Testes (`tests/test_learning.py`, 9 novos)

- Tipo inválido rejeitado.
- Link `javascript:` rejeitado na criação (form e API de captura) e na edição.
- Link `http(s)` e link vazio aceitos.
- Item aparece no perfil de quem criou.
- Só dono ou admin pode editar (não qualquer membro).
- Papel `leitor`: lê, não captura (403).

## Validação

- `pytest`: 53/53 passando.
- **Extensão**: servida localmente via `python -m http.server` (o `popup.html` usa ES modules,
  que não carregam de `file://`), payload `<img src=x onerror=...>` semeado direto no
  `localStorage` (mesmo formato que `chrome-mock.js` usa). Aberto a fila: nenhuma execução,
  `window.__xss_fired` continuou `false`, DOM mostrou o payload como texto escapado
  (`&lt;img ...&gt;`). Prova reversa no mesmo navegador, sem tocar no código real: o mesmo
  payload via `innerHTML` cru dispara de verdade (`true`) — confirma que a vulnerabilidade era
  real e que a correção neutraliza especificamente ela, não é acaso.
- **Backend**: subida real, link `javascript:` rejeitado (400) via requisição HTTP de verdade,
  link válido aceito (303) e confirmado renderizado em `/aprendizado` com "ver link →" funcional.
- Dado real: não aplicável, mesma situação dos módulos anteriores.

## Status

Concluído em 2026-07-17.
