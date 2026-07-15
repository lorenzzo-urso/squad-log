# Changelog

Registro do que mudou no próprio Registro da Equipe, por versão.

## 2026-07-15

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
