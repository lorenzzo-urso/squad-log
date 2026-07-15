# squad-log MCP server

Dá pra um agente de IA (Claude Code, etc.) ler e escrever nos Registros e no
Kanban do squad-log, sem precisar abrir o navegador.

**Sem tool de apagar, de propósito.** O agente pode listar, criar e editar —
nunca remover. Deletar continua sendo só na interface web, por uma pessoa.

A autenticação usa login normal (email/senha) contra `/login`, guardando o
cookie de sessão — quem estiver configurado ali é o dono de tudo que o agente
criar ou alterar (edição de registro publicado ainda exige admin, mesma regra
da interface web).

## Instalar

```bash
cd mcp_server
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Configurar no Claude Code

Variáveis de ambiente necessárias:

| Variável | Valor |
|---|---|
| `SQUADLOG_URL` | ex. `http://127.0.0.1:8000` ou o IP da rede |
| `SQUADLOG_EMAIL` | email de uma conta do squad-log |
| `SQUADLOG_PASSWORD` | senha dessa conta |

Adicione em `.claude/settings.json` (ou via `claude mcp add`):

```json
{
  "mcpServers": {
    "squad-log": {
      "command": "C:\\Users\\lurso\\Documents\\Timeline\\mcp_server\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\lurso\\Documents\\Timeline\\mcp_server\\server.py"],
      "env": {
        "SQUADLOG_URL": "http://127.0.0.1:8000",
        "SQUADLOG_EMAIL": "seu-email@empresa.com",
        "SQUADLOG_PASSWORD": "sua-senha"
      }
    }
  }
}
```

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
