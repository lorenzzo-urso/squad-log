# squad-log Capture (extensão de navegador)

Extensão de Chrome que captura cursos, artigos, vídeos e livros enquanto você navega e manda direto pro módulo **Aprendizado** do squad-log — sem digitar nada na mão.

## Como funciona

```
Você navega e acha algo interessante
        ↓
Abre a extensão do Chrome
        ↓
Ela scrapa a página (título, autor, URL, tipo)
        ↓
IA sugere tags e notas (opcional)
        ↓
Você revisa, edita e adiciona à fila
        ↓
Push → POST autenticado pro squad-log (/api/learning)
        ↓
Aparece em /aprendizado, no perfil de quem estiver logado
```

A extensão não tem login próprio — ela usa o cookie de sessão que já existe no navegador. Quem estiver logado no squad-log é o dono da captura; a extensão nunca escolhe isso por conta própria (veja `app/routes/learning.py`, o dono sempre vem da sessão autenticada, nunca do corpo da requisição).

## Instalar

1. `chrome://extensions/` → ative o **Modo do desenvolvedor**
2. **Carregar sem compactação** → selecione esta pasta (`extension/`)
3. Clique no ícone da extensão → **⚙** → preencha a **URL do squad-log** (ex. `http://192.168.1.50:8000`) e aceite a permissão de acesso quando o Chrome pedir
4. Faça login no squad-log nesse mesmo navegador — a fila mostra "Salvando como: {seu nome}" quando está tudo certo

## Estrutura

```
extension/
├── manifest.json
├── background.js
├── popup/
│   ├── popup.html / popup.js / popup.css
│   └── chrome-mock.js   # mock das APIs do Chrome, pra abrir popup.html direto num navegador comum em dev
└── utils/
    ├── schema.js         # estrutura de uma entrada capturada
    ├── storage.js        # fila local e configurações
    ├── squadlog.js        # fala com /api/whoami e /api/learning
    └── ai.js             # sugestões via Claude/OpenAI (opcional)
```

## Detecção automática de sites

Amazon/Goodreads/Skoob/Google Books → livro · YouTube/Vimeo/Twitch → vídeo · Udemy/Coursera/Alura/Pluralsight → curso · sites de notícia → notícia · resto → artigo.

## Limitações

- Máquina compartilhada: confira sempre o "Salvando como" antes de enviar.
- Sugestões de IA não têm contexto do que já está salvo no squad-log ainda (precisaria de um endpoint de listagem em JSON — não existe hoje).
