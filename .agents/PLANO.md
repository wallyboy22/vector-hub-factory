# Vector Hub Factory — Plano de Implementação

## Visão Geral

O Vector Hub Factory é uma plataforma local (FastAPI + HTML) para consultar documentos científicos via RAG (Retrieval-Augmented Generation) com LLMs da Google Gemini.

A interface é um **Workspace** com uma sidebar slim à esquerda e um canvas tabulado à direita.  
O acesso a qualquer chatbot é **sempre pela Vitrine** — não existem URLs standalone expostas ao usuário.

---

## Arquitetura Alvo

```
http://localhost:8000/
│
├── Vitrine (ui/vitrine/index.html)          ← Root. Layout: Sidebar + iFrame
│   ├── Sidebar slim (52px, hover expande)
│   │   ├── 🏠 Hub       → carrega home.html no iFrame
│   │   ├── 🔥 RAF       → carrega /raf no iFrame
│   │   └── 🌳 RAD       → carrega /rad no iFrame
│   └── iFrame principal  → renderiza o app selecionado
│
├── Hub (ui/vitrine/home.html)              ← Cards de documentos + links
│   └── Paleta escura, coerente com a Vitrine
│
├── Chatbot RAF (ui/chatbot-raf/index.html) ← Layout: Chat (30%) + Canvas (70%)
│   ├── Chat panel com sugestões retráteis
│   └── Canvas: Aba PDF (fixa) + Abas secundárias fecháveis (⚙️ Monitor IA)
│
└── Chatbot RAD (ui/chatbot-rad/index.html) ← Mesmo template, config diferente
```

---

## Regras de Design

| Regra | Valor |
|---|---|
| Cor RAF | `#E8503A` |
| Cor RAD | `#812411` |
| Cor Hub/Sidebar | `#1a1a2e` (fundo escuro) + `#ffffff` (texto/ícones) |
| Sidebar largura | `52px` repouso, `160px` hover |
| Chat panel largura | `30%` da tela |
| Canvas largura | `70%` (flex: 1) |
| Fonte | Inter (Google Fonts ou system-ui) |
| Sem botão Voltar | Navegação feita exclusivamente pela sidebar |
| Sem Multi-chat | Removido da sidebar e do hub |
| Sem Gaveta Skills | Removida dos chatbots |

---

## Template Universal de Chatbot

Os chatbots RAF e RAD são **idênticos em estrutura HTML/CSS/JS**.  
A única diferença é a configuração injetada no topo do script:

```javascript
const CHATBOT_CONFIG = {
  report: 'raf',           // chave do relatório para /ask e /pdf
  primaryColor: '#E8503A', // cor do tema
  title: '🔥 Relatório Anual do Fogo (RAF 2024)',
  placeholder: 'Sua dúvida sobre o RAF...',
  questionBank: [          // sugestões específicas do documento
    { label: '🇧🇷 Total Brasil', q: 'Qual a área total queimada no Brasil em 2024?' },
    // ...
  ]
};
```

Ao adicionar um novo relatório (ex: RAQ), basta copiar o template e alterar o `CHATBOT_CONFIG`.

---

## O que está pronto e funciona

- `src/api.py` — FastAPI com todas as rotas necessárias (`/ask`, `/pdf`, `/reports`, `/health/v2`)
- `ui/assets/config.js` — URLs configuráveis local vs. produção
- `ui/assets/tab-manager.js` — Gerenciador de abas (funcional, mas mal integrado)
- `ui/assets/shared.css` — CSS base (funcional, mas com regras novas quebradas)

---

## O que está quebrado e precisa ser corrigido

### Bug #1 — Canvas PDF não aparece no RAF/RAD
**Causa:** O `TabManager` chama `container.innerHTML = ...` destruindo o `#pdf-container` original antes que o JS o referencie.  
**Fix:** O `TabManager` deve receber o container do canvas vazio. O PDF deve ser adicionado via `addTab()` **depois** que o DOM está pronto. Alternativamente, simplificar: não usar `TabManager` para a aba PDF — o PDF fica fixo no container, e `TabManager` só gerencia abas **secundárias** sobrepostas.

### Bug #2 — Layout body quebrado
**Causa:** O CSS tem `flex-direction: column` e `flex-direction: row` no mesmo seletor `body`.  
**Fix:** Remover o override inline — o `body` deve só ter `flex-direction: row` para suportar o wrapper `chat-wrapper` interno.

### Bug #3 — Sidebar com visual errado
**Causa:** Ícones grandes demais (`font-size: 1.4rem`) e padding excessivo (`12px 8px`) para uma sidebar de 52px.  
**Fix:** Ícone `1.1rem`, padding `8px 6px`, label `0.5rem`.

### Bug #4 — Hub com paleta azul divergente  
**Causa:** `home.html` define `--primary-color: #00b4d8` que destoa dos relatórios.  
**Fix:** Hub usa paleta neutra (`#1a1a2e` fundo, `#e0e0e0` texto, sem override do `--primary-color` global).

### Bug #5 — Aba ⚙️ "Monitor IA" não implementada corretamente
**Causa:** Tentativa de injetar `<script>` via `innerHTML` — browsers ignoram por segurança.  
**Fix:** A aba Monitor deve ser criada com conteúdo HTML estático + o fetch feito em JS separado, executado via `setTimeout` após injeção.

---

## Diagrama de Arquivos a Modificar

```
ui/
├── vitrine/
│   ├── index.html    [MODIFICAR] Corrigir sidebar (visual), remover Multi
│   └── home.html     [MODIFICAR] Corrigir paleta de cores
├── chatbot-raf/
│   └── index.html    [REESCREVER] Limpar bugs, usar template universal
├── chatbot-rad/
│   └── index.html    [REESCREVER] Limpar bugs, usar template universal
└── assets/
    ├── shared.css    [MODIFICAR] Remover regras conflitantes
    └── tab-manager.js [MANTER] Está correto, só a integração quebrou
```

---

## Sobre os Tokens da API Gemini

Ao testar localmente, **usar o endpoint `/health/v2`** para verificar o status das chaves **antes** de tentar o chat. O endpoint não consome tokens — ele faz um `embed_content` mínimo de "heartbeat".

Se todas as chaves estiverem `exhausted`: aguardar o reset diário (meia-noite PT). Não é bug da aplicação.

Para simular respostas sem consumir tokens durante testes de UI: adicionar um **modo mock** na função `sendQuestion()` que retorna uma resposta fake quando `API_URL` contém `localhost` e uma variável `MOCK_MODE = true` está ativa.
