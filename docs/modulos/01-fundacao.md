# Módulo 1 — Fundação

Auth, sessão, papéis, configuração e inicialização do banco. Base de todos os outros módulos —
qualquer coisa errada aqui se propaga pra tudo que vier depois.

## Estado em 2026-07-16 (antes desta reconstrução)

- `app/db.py` lia `DB_PATH`/`UPLOADS_DIR` do ambiente pra dentro de constantes de módulo, na hora
  do import. Isso fazia teste precisar de `monkeypatch` em atributo interno do módulo — sintoma
  de um problema maior: config não era injetável.
- `app/main.py` criava o diretório de upload e montava `StaticFiles` também na hora do import,
  usando o mesmo valor fixo.
- `@app.on_event("startup")` — API depreciada do FastAPI.
- Nenhum log em lugar nenhum do módulo.
- Nenhum handler de erro — exceção não tratada virava 500 cru do Starlette, sem log, sem
  resposta padronizada.
- `_seed_admin` lia `ADMIN_EMAIL`/`ADMIN_PASSWORD` direto do `os.environ`, mesmo padrão do
  problema acima.

## O que mudou, e por quê

- **`app/settings.py` (novo)** — `Settings` (dataclass congelada) + `get_settings()` cacheado
  (`lru_cache`). Troca "constante lida uma vez no import" por "função injetável via
  `Depends(get_settings)`". Resolve o problema na raiz, não só nos testes — qualquer rota que
  precisar de config agora declara a dependência, em vez de importar um valor fixo.
- **`app/db.py`** — `get_connection`, `get_db`, `init_db`, `_seed_admin` passam a receber
  `Settings` explicitamente em vez de ler globals do módulo.
- **`app/main.py`**:
  - `@app.on_event("startup")` → `lifespan` (context manager assíncrono) — API atual do FastAPI,
    remove o warning de depreciação que aparecia até nos testes.
  - `logging.basicConfig(...)` uma vez, no bootstrap — todo o app ganha log estruturado sem
    precisar configurar em cada módulo.
  - `@app.exception_handler(Exception)` — captura qualquer erro não tratado em qualquer rota,
    loga com stack trace no servidor, devolve `{"detail": "Erro interno"}` genérico pro cliente
    (nunca vaza detalhe de exceção pra fora). É a correção na causa raiz do "zero tratamento de
    erro" do projeto inteiro — feita uma vez aqui, não repetida em cada rota de cada módulo.
  - `no_cache_static` reescrito de `@app.middleware("http")` (baseado em `BaseHTTPMiddleware`)
    pra middleware ASGI puro. Motivo real, não estético: o `BaseHTTPMiddleware` estava impedindo
    o exception handler acima de funcionar — exceção de rota não chegava nele. Confirmado
    quebrando antes da correção e passando depois, com teste (`test_fundacao.py`).
- **`app/routes/auth.py`** — log de `login ok` / `login failed` / `logout`. Auditoria mínima de
  quem entrou e quando.
- **`app/routes/admin.py`** — log em criar usuário, resetar senha, remover usuário. Mesma lógica:
  ações de admin ficam rastreáveis.
- **`app/routes/timeline.py`** — `_save_cover` e as três rotas que a chamam passaram a receber
  `uploads_dir` via `Settings` em vez do import direto de `UPLOADS_DIR`. Efeito colateral
  necessário da mudança de config — não é trabalho do módulo Timeline ainda (isso é módulo 2),
  só o suficiente pra não quebrar com a fundação nova.

## O que não mudou (decisão consciente, não descuido)

- PBKDF2 200k iterações + comparação de tempo constante — já estava correto.
- Hash mais barato pra token de API — já estava correto e justificado.
- Papéis `admin`/`membro` via `CHECK` no SQLite — suficiente pro tamanho do time.
- **Sessão sem expiração.** Decisão explícita: 4 pessoas confiáveis, rede interna, sem SSO/MFA
  por escolha própria já registrada no PRD original. Revisitar se a ferramenta algum dia sair
  desse perímetro de confiança (mais usuários, acesso externo).

## Testes (`tests/test_fundacao.py`, 8 novos + 5 de `test_permissions.py` já existentes)

- `Settings`/`get_settings` respeita variável de ambiente e usa default correto.
- Hash de senha: roundtrip correto, senha errada falha, salt aleatório a cada chamada.
- Token de API: formato (`sqlg_...`), hash determinístico e diferente do token em si.
- Login com senha errada devolve 401.
- Logout de fato invalida a sessão (rota protegida volta a exigir login).
- Exceção não tratada em qualquer rota devolve 500 genérico, não stack trace — e o teste prova
  isso quebrando uma rota de propósito.

`tests/conftest.py` foi atualizado junto: a troca de config por `Depends` permitiu substituir o
`monkeypatch` em atributo de módulo por `app.dependency_overrides[get_settings]` — o jeito
padrão do FastAPI de trocar dependência em teste. Menos frágil, documentado no próprio arquivo.

## Validação

- `pytest`: 13/13 passando.
- Subida real (`uvicorn`, fora do pytest) verificada no navegador: `/timeline` carrega,
  login funciona, `/admin` mostra o admin criado via bootstrap, log estruturado aparece no
  console pra `db initialized`, `bootstrap admin created` e `login ok`.
- **Dado real preservado**: não aplicável — confirmado com Lorenzzo (2026-07-17) que não existe
  banco com dado real em nenhuma máquina ainda; o squad-log roda hoje só localmente, sem uso real
  registrado. O requisito de preservação da PRD fica dormente até o dia em que a ferramenta
  passar a guardar dado de verdade — nesse dia, todo módulo já reconstruído até então precisa ser
  revalidado contra esse dado real antes de seguir confiando nele.

## Revisão — papel `leitor` (2026-07-17, durante o módulo 2)

Motivo: squad-log vai ser consumido via MCP por gente de fora do squad (colegas, gestores) —
até então qualquer token de API válido tinha o mesmo poder de escrita que login normal. Não
existia papel "só consultar".

- **Schema**: `CHECK (role IN ('admin', 'membro'))` → inclui `'leitor'`. Migração
  `_migrate_user_roles` (rename/recria/copia, mesmo padrão de `_migrate_learning_types`) —
  testada isoladamente contra uma tabela no formato antigo pra provar que preserva dado (não só
  o caso de banco novo, que nunca exercitaria a migração de verdade).
- **`app/auth.py`**: nova dependência `require_writer` (autenticado E papel ≠ `leitor`).
  `require_admin` agora encadeia por cima dela, em vez de `require_user` direto.
- Toda rota de criar/editar em `timeline.py`, `kanban.py`, `roadmap.py`, `learning.py` trocou
  `require_user` → `require_writer`. Ficaram de fora, de propósito: `/api/whoami` (só identifica
  o token, não escreve) e todo GET de leitura, que já era aberto por padrão.
- **`MAX_USERS` (4) passa a valer só pra admin/membro** — é limite de vaga de escrita, da PRD
  original; leitor não compete por essa vaga. Painel de admin ajustado pra mostrar os dois
  números separados e não esconder o formulário de novo usuário quando só as vagas de escrita
  estão cheias (achado e corrigido durante a própria validação: o template ainda usava a
  contagem antiga).
- Validado fim a fim com sessão HTTP real (não só teste): criado um leitor pelo painel de
  verdade, login como esse leitor, tentativa de publicar → 403, leitura → 200, `/api/whoami` →
  identifica a pessoa certa.
- 5 testes novos em `test_fundacao.py` (leitura sim, escrita não, whoami, contagem de vaga,
  migração preservando dado antigo) — 28/28 no total.

**Fila de aprovação** (ideia de módulo 2, ver `02-timeline.md`) ainda não decidida — esse papel
`leitor` resolve o caso "consulta sem poder publicar", que era o problema imediato. Submissão
externa com aprovação continua em aberto, sem gatilho suficiente ainda.

## Status

Concluído em 2026-07-17.
