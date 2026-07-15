# Changelog

Registro do que mudou no próprio Registro da Equipe, por versão.

## 2026-07-15

- **Tokens de API** (`/tokens`): cada pessoa gera seus próprios tokens pessoais pra autenticar ferramentas externas (MCP, scripts), em vez de expor a senha de login. O MCP server agora usa `SQUADLOG_TOKEN` (Bearer) no lugar de email/senha; revogar um token no `/tokens` desliga o acesso na hora, sem mexer na senha.
- **Timeline com data de publicação própria e arquivo**: registros agora têm uma "Data de publicação" editável (separada de quando foram digitados no sistema), pra poder cadastrar entregas antigas com a data real delas. A tela principal mostra só os últimos 30 dias (destaque + grade); o resto vira um **Arquivo** abaixo, organizado por Ano → Trimestre, recolhível.
- **Servidor MCP** (`mcp_server/`): 6 tools pra um agente de IA listar, criar e editar Registros e cards do Kanban direto — sem tool de apagar, de propósito.
- **API JSON** `/api/posts` e `/api/kanban/cards` (list/create/update), base do servidor MCP e reaproveitável por qualquer outro integração futura.
- **"Meu radar"** (`/radar`): painel pessoal com meus registros, meus cards e atalho pro meu Aprendizado, tudo num lugar.
- **Dashboard** (`/dashboard`): registros por mês, cards concluídos por pessoa, contadores gerais — visão de entrega do squad.
- **Exportar registro em PDF**: botão que aciona a impressão nativa do navegador, com layout formatado como documento (sem lib nova).
- **Modo escuro**: alternância manual persistida, além de respeitar a preferência do sistema por padrão.
- **Busca full-text**: a busca da Timeline agora cobre o corpo do registro, não só título e resumo.
- **Módulo Aprendizado**: nova área pra registrar cursos, palestras, livros e afins, por pessoa — base pro PDI.
- **Extensão de captura** (`extension/`): captura páginas no navegador (curso, artigo, vídeo, livro) e envia direto pro Aprendizado via API, autenticado pela sessão de quem estiver logado — sem digitar nada na mão.
- **Changelog, RSS e backup**: página `/changelog`, feed `/feed.xml`, e `backup.bat` pra exportar o volume Docker.

## 2026-07-14

- **Correções de bugs do Kanban e Roadmap**: popup de card que ficava preso na tela após fechar, filtro quebrando com seleção vazia, coluna do Roadmap não podia ser escolhida ao criar um item.
- **Multi-tag no Kanban**: cards agora aceitam mais de uma tag de produto/tecnologia.
- **Popup de card no Kanban**: clicar num card abre os detalhes completos sem sair da tela.
- **Imagens sem corte**: capas de posts e miniaturas mostram a imagem inteira (`object-fit: contain`), sem cortar conteúdo.
- **Editor de posts estilo blog**: EasyMDE substitui a caixa de texto simples — toolbar de formatação, preview, upload de imagem inline.
- **Redesign completo**: novo sistema visual (Classical — Cormorant Garamond + Lora, paleta terrosa, texturas), busca e paginação na Timeline. Projeto renomeado de "Timeline do Squad" para "Registro da Equipe".

## 2026-07-13

- **Lançamento inicial**: Timeline (registros com coautoria e markdown), Kanban (board único com filtros), Roadmap (planejado/em andamento/entregue, desacoplado do Kanban), IAM simples (login, admin gerencia até 4 usuários), deploy via Docker.
