# PRD — Timeline do Squad

## 1. Problema

O squad (2 pessoas, atuando em dados, Slack, IA e integração) é um setor novo, isolado do
restante da empresa — não está no fluxo natural de outras equipes e não aparece no radar de
gestores e pares por acidente. As entregas do squad variam muito em relevância (triviais a
muito relevantes) e ficam espalhadas por diferentes stakeholders, sem nenhum lugar único onde
o trabalho feito, em andamento e planejado possa ser visto.

Consequências concretas hoje:
- Gestores não conseguem avaliar a visibilidade/entrega real do squad.
- Sem ferramenta de backlog (não usam Jira/Trello): ideias surgem do nada e há conflito de
  prioridade.
- Direção do setor não é comunicada a quem está de fora.

## 2. Objetivo

Uma aplicação interna com três superfícies que resolvem, juntas, visibilidade de entregas,
organização do trabalho em andamento e comunicação de direção — sem depender de ferramentas
externas que o squad não usa.

## 3. Não-objetivos (fora de escopo)

- Reações, comentários, notificações ou qualquer curadoria de terceiros.
- Múltiplos boards de kanban por pessoa/produto (é um board único, filtrado/agrupado).
- Acoplamento entre Roadmap e Kanban (são independentes).
- Prazos/datas de entrega no Kanban e no Roadmap (sem deadline, sem trimestre).
- SSO/MFA, self-signup, fluxo de "esqueci minha senha" automatizado.
- Versionamento/histórico de edições, lixeira/soft-delete.
- Storage externo de arquivos (S3 etc.), processamento de imagem.
- HTTPS embutido na aplicação (acesso é interno, TLS fica a critério de proxy externo se um
  dia for necessário).

## 4. Usuários e acesso

- **Leitura**: aberta a qualquer pessoa dentro da rede interna da empresa, sem login. Controle
  de acesso é feito a nível de rede (VPN/intranet), não pela aplicação.
- **Escrita**: restrita a contas cadastradas, no máximo **4 usuários**.
- **Papéis**: `admin` e `membro`.
  - Membro: cria posts, cards e itens de roadmap; edita/apaga apenas os próprios enquanto não
    publicados — uma vez publicado, só admin edita/apaga.
  - Admin: tudo que membro faz, mais gerenciar usuários (criar, remover, resetar senha) e
    editar/apagar qualquer conteúdo publicado.
- **Bootstrap**: primeira conta admin é criada automaticamente no primeiro boot a partir de
  variáveis de ambiente (`ADMIN_EMAIL`, `ADMIN_PASSWORD`). Sem endpoint público de setup.
- Login simples (usuário/senha, sessão via cookie), sem OAuth/SSO/MFA.

## 5. Funcionalidades

### 5.1 Timeline (prova de entrega)

Lista cronológica (mais recente primeiro) de posts publicados pelo squad. Formato único
(inspirado no blog do Excalidraw+) — sem distinção formal entre "update" e "entrega"; a
riqueza do conteúdo varia livremente por post.

**Post**
| Campo | Tipo | Obrigatório |
|---|---|---|
| título | texto | sim |
| data | timestamp (auto) | sim |
| autor | usuário cadastrado | sim |
| coautores | usuários cadastrados (0+) | não |
| resumo | texto curto | sim |
| corpo | markdown | sim |
| capa | imagem (upload local) | não |

Sem tags, sem categorias, sem reações/comentários de terceiros.

### 5.2 Kanban (backlog operacional interno)

Um único board com três colunas: **Ideia → Em andamento → Concluído**. Sem múltiplos boards
— pessoa e produto/tecnologia são filtros/agrupamentos sobre o mesmo conjunto de cards.

**Card**
| Campo | Tipo | Obrigatório |
|---|---|---|
| título | texto | sim |
| descrição | texto/markdown | não |
| responsáveis | usuários cadastrados (1+) | sim |
| produto/tecnologia | valor de lista fixa (gerida pelo admin) | sim |
| coluna | Ideia \| Em andamento \| Concluído | sim |
| ordem | posição manual dentro da coluna (define prioridade) | sim |
| criado_em | timestamp (auto) | sim |

Sem campo de prazo/deadline. Atalho "publicar como entrega" num card concluído pré-preenche
título/descrição de um novo post na Timeline (ação manual, não automática).

### 5.3 Roadmap do setor

Board próprio, independente do Kanban (dados e cards não se conectam). Três colunas:
**Planejado → Em andamento → Entregue**. Curadoria manual — nem todo card do Kanban vira item
de roadmap, e o inverso também não é automático.

**Item de roadmap**
| Campo | Tipo | Obrigatório |
|---|---|---|
| título | texto | sim |
| descrição | texto curto | sim |
| status | Planejado \| Em andamento \| Entregue | sim |
| ordem | posição manual dentro da coluna | sim |

Sem datas, sem trimestre — comunica direção, não cronograma.

## 6. Requisitos técnicos

- **Stack**: Python + FastAPI, servindo API e HTML (Jinja2/HTMX) num serviço único — sem
  frontend separado (SPA).
- **Banco**: SQLite (arquivo único, sem serviço de banco separado).
- **Arquivos**: uploads salvos em volume Docker local (`/data/uploads`), limite de 5MB por
  arquivo. Banco guarda apenas o caminho.
- **Deploy**: `docker-compose.yml` com um serviço (`app`), porta configurável no host. Dois
  volumes nomeados persistentes: `/data/db` (SQLite) e `/data/uploads`.
- **Hospedagem**: servidor interno da empresa, acesso restrito à rede interna.

## 7. Fluxos principais

1. **Publicar entrega**: membro logado cria post (título, resumo, corpo, coautores opcionais,
   capa opcional) → aparece no topo da Timeline, visível a qualquer um na rede interna.
2. **Gerenciar backlog**: membro cria card no Kanban (Ideia), atribui responsáveis e
   produto/tecnologia, arrasta entre colunas e reordena por prioridade dentro da coluna.
3. **Publicar entrega a partir de um card concluído**: membro aciona "publicar como entrega"
   num card em Concluído → formulário de novo post pré-preenchido, edita e publica.
4. **Curar roadmap**: membro/admin cria ou move itens entre Planejado/Em andamento/Entregue,
   independente do estado de qualquer card do Kanban.
5. **Gerenciar usuários**: admin cria/remove contas e reseta senha via painel simples.

## 8. Critérios de aceite (MVP)

- [ ] Qualquer pessoa na rede interna acessa Timeline, Kanban e Roadmap sem login.
- [ ] Login restringe criação/edição a usuários cadastrados (máx. 4).
- [ ] Primeiro admin é criado automaticamente via variável de ambiente no primeiro boot.
- [ ] Post publicado só pode ser editado/apagado por admin.
- [ ] Kanban é um board único; filtro por pessoa e por produto/tecnologia funciona sobre o
      mesmo conjunto de cards.
- [ ] Ordem dentro da coluna do Kanban e do Roadmap é manual e persistida.
- [ ] Upload de imagem (capa de post) funciona e persiste após restart do container.
- [ ] `docker compose up` sobe a aplicação completa com um único serviço.

## 9. Suposição mais arriscada

Que o squad sustente o hábito de registrar posts e manter o Kanban atualizado depois que a
novidade da ferramenta passar. Mitigação sugerida (fora do escopo técnico): atrelar o
preenchimento a um ritual já existente (ex: fechamento de sprint/semana).
