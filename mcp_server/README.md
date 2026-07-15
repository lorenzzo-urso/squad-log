# squad-log MCP server

Dá pra um agente de IA (Claude Code, etc.) ler e escrever nos Registros e no
Kanban do squad-log, sem precisar abrir o navegador.

**Sem tool de apagar, de propósito.** O agente pode listar, criar e editar —
nunca remover. Deletar continua sendo só na interface web, por uma pessoa.

A autenticação usa login normal (email/senha) contra `/login`, guardando o
cookie de sessão — quem estiver configurado ali é o dono de tudo que o agente
criar ou alterar (edição de registro publicado ainda exige admin, mesma regra
da interface web).

## Instalar (cada pessoa faz a própria cópia)

```bash
cd mcp_server
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

`mcp_server/.venv/` é ignorado pelo git — cada um instala o seu.

## Configurar no Claude Code

O Claude Code lê servidores MCP de um arquivo **`.mcp.json` na raiz do repo**
(não é `.claude/settings.json`). Esse arquivo tem sua senha em texto puro,
então **é ignorado pelo git** (`.mcp.json` está no `.gitignore`) — nunca é
compartilhado nem sobe pro GitHub. Cada pessoa cria o próprio, com as
próprias credenciais.

1. Copie o template:
   ```bash
   cp .mcp.json.example .mcp.json
   ```
2. Edite `.mcp.json` na raiz do repo e preencha:

   | Campo | Valor |
   |---|---|
   | `command` / `args` | caminho completo pro `python.exe` do seu venv e pro `server.py` — ajuste pra onde *você* clonou o repo (o caminho é diferente por máquina) |
   | `SQUADLOG_URL` | ex. `http://192.168.1.50:8000` (IP da rede) ou `http://127.0.0.1:8000` se for testar na mesma máquina do servidor |
   | `SQUADLOG_EMAIL` | seu email de login no squad-log |
   | `SQUADLOG_PASSWORD` | sua senha |

3. Feche e abra o Claude Code de novo nesse projeto — é assim que ele detecta um `.mcp.json` novo. Na primeira vez ele pergunta se você confia no servidor "squad-log"; aprova.
4. Teste pedindo algo tipo *"liste os registros do squad-log via MCP"*.

## Tools disponíveis

| Tool | Faz |
|---|---|
| `list_posts` | Lista os registros da Timeline |
| `create_post` | Cria um registro (título, resumo, corpo markdown, coautores) |
| `update_post` | Atualiza um registro (precisa de conta admin) |
| `list_cards` | Lista os cards do Kanban, com tags e responsáveis |
| `create_card` | Cria um card (título, tags, descrição, responsáveis, coluna) |
| `update_card` | Atualiza um card existente (só os campos enviados mudam) |

Não existe `delete_post` nem `delete_card`.
