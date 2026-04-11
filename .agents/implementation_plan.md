# 🏭 vector-hub-factory — Plano de Implementação (Revisado)

## Contexto e Diagnóstico

O projeto já completou as Fases 0–5 (T00–T14) do plano anterior.
O resultado foi funcional, mas o usuário está **insatisfeito com a aparência dos apps Streamlit**
e muito satisfeito com o `ui/index.html` + FastAPI (`src/api.py`).

**Diagnóstico:** O Streamlit renderiza componentes React que resistem ao controle fino de layout
necessário para replicar a interface HTML. Não é um problema de skill de CSS — é uma limitação
estrutural da tecnologia para este caso de uso.

---

## Decisão Arquitetural

> Expandir o que já funciona: **HTML + FastAPI** para todos os chatbots.  
> Streamlit é mantido apenas na vitrine (`app.py`) onde está aceitável.  
> A vitrine principal migra para HTML estático hospedado no **GitHub Pages**.

---

## Estado Atual (Pós T00–T14)

```
ROOT/
├── .agents/             ← Skills e planos (NÃO mover)
├── app.py               ← Vitrine Streamlit (funcional, será substituída)
├── config.py            ← Config global (✅ pronto)
├── factory/             ← Scripts de fábrica (✅ prontos: T04–T09)
├── apps/                ← Chatbots Streamlit (✅ criados, serão substituídos)
│   ├── raf_chatbot/app.py
│   ├── rad_chatbot/app.py
│   ├── multi_report/app.py
│   └── cross_search/app.py
├── docs/                ← PDFs + dados gerados (✅ estrutura pronta)
├── ui/
│   └── index.html       ← App HTML que o usuário AMA (multi-relatório)
├── src/
│   ├── api.py           ← FastAPI backend (✅ funcionando)
│   └── qa.py            ← RAG pipeline (✅ funcionando)
└── start_all.bat        ← Inicia 1 FastAPI + 5 Streamlits (será simplificado)
```

---

## Visão Geral da Nova Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│          GitHub Pages (estático, automático)                │
│  public/index.html ← vitrine HTML sem backend              │
│  - Cards de documentos, downloads, links para chatbots      │
└─────────────────────────────────────────────────────────────┘
                     ↕ links apontam para →
┌─────────────────────────────────────────────────────────────┐
│         Servidor FastAPI — uvicorn porta 8000               │
│                                                             │
│  GET  /           → ui/index.html  (chatbot multi-relatório)│
│  GET  /cross      → ui/cross/index.html  (busca transversal)│
│  GET  /hub        → ui/vitrine/index.html (vitrine local)   │
│  GET  /pdf/{doc}  → serve PDF                               │
│  GET  /reports    → JSON com metadados de todos os docs     │
│  POST /ask        → RAG single-doc                          │
│  POST /ask_cross  → RAG multi-doc (todos os índices)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Nova Estrutura de Pastas Alvo

```
ROOT/
├── .agents/
│   ├── skills/
│   │   ├── vector_hub_factory/SKILL.md
│   │   ├── streamlit_ux_pro/SKILL.md
│   │   ├── app_validator/SKILL.md
│   │   └── html_app_factory/SKILL.md   ← NOVA (T23)
│   ├── implementation_plan.md
│   └── task.md
│
├── ui/
│   ├── index.html              ← Chatbot multi-relatório (já existe, manter)
│   ├── vitrine/
│   │   └── index.html          ← NOVA: Hub estático (T16)
│   ├── cross/
│   │   └── index.html          ← NOVA: Busca transversal (T17)
│   └── assets/
│       ├── shared.css          ← NOVO: CSS compartilhado (T15)
│       └── config.js           ← NOVO: URLs configuráveis (T21)
│
├── public/                     ← NOVA: Saída para GitHub Pages (T19)
│   └── index.html              ← Cópia da ui/vitrine/index.html
│
├── src/
│   └── api.py                  ← Expandir com /cross e /ask_cross (T18)
│
├── render.yaml                 ← NOVO: Deploy automático Render (T20)
├── start_all.bat               ← Simplificar para 1 processo (T22)
└── config.py                   ← Sem mudanças
```

---

## Fase 6 — Design System HTML Compartilhado

### `ui/assets/shared.css` (T15)

Extrair as CSS variables e estilos base do `ui/index.html` para um arquivo compartilhado.
Todos os HTMLs novos importam este arquivo com `<link rel="stylesheet" href="/assets/shared.css">`.

**Variáveis obrigatórias:**
```css
:root {
  --primary-color: #E8503A;   /* sobrescrito por JS por documento */
  --secondary-color: #555555;
  --bg-light: #fdfdfd;
  --chat-bg: #ffffff;
  --text-dark: #333333;
  --text-muted: #888888;
  --border-color: #eeeeee;
}
```

**Estilos base a extrair:** header, tab-bar, chat container, input area, suggestions, page-links, PDF container.

---

## Fase 7 — Vitrine HTML Estática (GitHub Pages)

### `ui/vitrine/index.html` (T16)

Página HTML pura (zero chamadas de API — funciona sem servidor):

- **Header:** "Vector Hub Factory" + subtítulo
- **Cards por documento** (RAF, RAD — hardcoded com valores do config.py):
  - Nome, emoji, cor do documento
  - `<a href="...">⬇️ Baixar PDF</a>` → link para GitHub Release
  - `<a href="...">⬇️ faiss.index</a>` + `<a href="...">⬇️ meta.json</a>`
  - Dimensões do vetor, modelo, provedor, custo
  - `<a href="{API_URL}">💬 Abrir Chatbot</a>` → abre o FastAPI
- **Seção "Como usar"** com snippet do `factory/03_query_index.py`
- **Rodapé** com link para GitHub

> A URL do FastAPI (`API_URL`) é lida de `assets/config.js` para ser configurável sem recompilar.

---

## Fase 8 — Busca Transversal HTML

### `ui/cross/index.html` (T17)

Idêntico ao `ui/index.html` (copiar e modificar), com as diferenças:
- Sem a aba de seleção de relatório (busca em tudo de uma vez)
- As respostas têm badges de origem: `[RAF p.14]` `[RAD p.22]`
- O PDF viewer mostra o documento da fonte mais relevante (troca automaticamente)
- Faz `POST /ask_cross` em vez de `POST /ask`

### Rota `POST /ask_cross` no `src/api.py` (T18)

```python
@app.post("/ask_cross")
def ask_cross(q: CrossQuestion):
    # Para cada doc em DOCUMENTS:
    #   1. Buscar top-K chunks no índice do documento
    # Unir todos os chunks, re-ranquear por score
    # Montar contexto com indicação de origem [doc.short, p.X]
    # Chamar o LLM com o contexto unificado
    # Retornar resposta + sources com campo "doc" adicionado
```

---

## Fase 9 — Deploy

### `public/index.html` — GitHub Pages (T19)

- Criar pasta `public/` na raiz
- Copiar `ui/vitrine/index.html` para `public/index.html`
- Criar `.github/workflows/pages.yml` com Action que faz esse deploy automaticamente a cada push na `main`

### `render.yaml` — Deploy FastAPI no Render (T20)

```yaml
services:
  - type: web
    name: vector-hub-factory
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
```

### `ui/assets/config.js` — URLs Configuráveis (T21)

```javascript
// Edite apenas este arquivo para apontar para produção
window.VHF_CONFIG = {
  API_URL: window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://vector-hub-factory.onrender.com',
};
```

---

## Fase 10 — Limpeza e Atualização

### `start_all.bat` Simplificado (T22)

```bat
@echo off
echo [1/1] Iniciando Vector Hub Factory (porta 8000)...
start "VHF" uvicorn src.api:app --port 8000 --reload
echo Acesse: http://localhost:8000
pause
```

### Skill `html_app_factory` (T23)

Nova skill em `.agents/skills/html_app_factory/SKILL.md` que documenta:
- Como criar um novo `ui/{app}/index.html` a partir do template base
- Como registrar a rota no `api.py`
- Como o `config.js` resolve URLs local vs. produção
- Como fazer o link aparecer na vitrine
- Padrão de passagem de dados Python → JSON → JavaScript

---

## Informações Técnicas Importantes para a IA Executora

### Arquivo `ui/index.html` — Como Funciona (Não Modificar)

| Elemento | Implementação |
|---|---|
| Abas de documentos | `GET /reports` retorna JSON → JS cria `<div class="tab">` |
| Cor do tema | `document.documentElement.style.setProperty('--primary-color', info.color)` |
| PDF viewer | `<iframe src="/pdf/{doc}#toolbar=0">` |
| Envio de pergunta | `POST /ask` com body `{question, report, model}` |
| Chips de sugestão | Hardcoded em `questionBanks` por relatório |
| Navegação de página | `iframe.src = /pdf/{doc}?t={ts}#page={n}` |

### `src/api.py` — Rotas Existentes (Manter Funcionando)

```
GET  /           → FileResponse(ui/index.html)
GET  /pdf/{doc}  → FileResponse(PDF do documento)
GET  /logo/{doc} → FileResponse(logo do documento)
GET  /reports    → JSON de metadados
POST /ask        → RAG pipeline
```

---

## Verificação de Sucesso Final

- [ ] `http://localhost:8000` → chatbot multi-relatório idêntico ao HTML original
- [ ] `http://localhost:8000/cross` → busca transversal com badges de origem
- [ ] `http://localhost:8000/hub` → vitrine estática local
- [ ] `public/index.html` → abre no browser sem servidor (zero API calls)
- [ ] Push para main → GitHub Pages publica `public/index.html`
- [ ] Render detecta push → deployta FastAPI automaticamente
- [ ] `start_all.bat` inicia apenas 1 processo
