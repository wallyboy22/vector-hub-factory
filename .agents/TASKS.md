# Vector Hub Factory — Tasks de Execução

> Leia `PLANO.md` primeiro para entender o contexto completo antes de executar qualquer task.

---

## Como Executar

1. Inicie o backend: `.venv\Scripts\python.exe -m uvicorn src.api:app --port 8000`
2. Acesse `http://localhost:8000` para testar cada mudança
3. Marque `[x]` conforme concluir e **verifique no browser antes de avançar**

---

## STATUS DA REFORMA (REFEITO APÓS FEEDBACK)

- [x] **Sidebar da Vitrine:** Restaurada Busca Transversal (🔍), removido Multi (📊). Legendas e ícones compactos em fundo escuro conforme plano.
- [x] **Hub de Documentos:** Totalmente refeito com **cores claras** e design premium (clean white/pale border). Sem botões de apps redundantes.
- [x] **Correção PDF (RAF/RAD):** Template universal reescrito do zero. O PDF agora carrega com altura 100% garantida via Flexbox.
- [x] **Remoção de Gavetas:** Eliminadas todas as gavetas interativas ("Ferramentas & Skills" e "Toggle Chat"). O painel agora é fixo e limpo.
- [x] **Aba Monitor IA:** Mantida como uma aba do canvas (trigger ⚙️ no topo direito), não como gaveta do chat.
- [x] **Modo Mock:** Ativado em todos os chatbots para testes de UI.

**Arquivo:** `ui/chatbot-raf/index.html` e `ui/chatbot-rad/index.html`

**Problema:** O seletor `body` tem duas declarações de `flex-direction` — a segunda sobrescreve a primeira causando layout incorreto.

**Fix:** No `<style>` interno de ambos os arquivos, o seletor `body` deve ter APENAS:
```css
body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg-light);
  display: flex;
  flex-direction: row;
  height: 100vh;
  overflow: hidden;
}
```
Remover qualquer linha duplicada de `flex-direction`.

**Verificação:** Abrir `/raf` no browser. O layout deve ser: chat panel à esquerda, canvas à direita, sem bagunça vertical.

- [ ] Corrigir `chatbot-raf/index.html`
- [ ] Corrigir `chatbot-rad/index.html`

---

## TASK 2 — Corrigir o canvas PDF que não aparece

**Arquivo:** `ui/chatbot-raf/index.html` e `ui/chatbot-rad/index.html`

**Problema:** O `TabManager` destrói o conteúdo de `#pdf-container` ao chamar `container.innerHTML = ...` no construtor, matando o `<iframe id="pdf-viewer">` antes que o JS o referencie.

**Fix:** Mudar a estratégia de integração do `TabManager`:
1. No HTML, deixar o `#pdf-container` **vazio** (sem iframe dentro)
2. No JS, inicializar o `TabManager` e adicionar a aba PDF como primeira aba:
```javascript
const tabManager = new TabManager('pdf-container');
const API_URL = window.VHF_CONFIG?.API_URL || 'http://localhost:8000';

// Aba PDF — não fechável, sempre presente
tabManager.addTab(
  'pdf',
  'RAF 2024',          // título da aba (ajustar por relatório)
  false,               // não fechável
  `<iframe id="pdf-viewer" style="width:100%;height:100%;border:none" src="${API_URL}/pdf/raf#toolbar=0"></iframe>`,
  '📄'
);
```
3. A referência `pdfIframe` no JS deve usar `document.getElementById('pdf-viewer')` **após** o `addTab`.

**Verificação:** O PDF deve aparecer imediatamente ao abrir `/raf`. O leitor deve ocupar 100% do canvas.

- [ ] Corrigir integração TabManager em `chatbot-raf/index.html`
- [ ] Corrigir integração TabManager em `chatbot-rad/index.html`

---

## TASK 3 — Adicionar aba ⚙️ Monitor IA (acessada por botão no canvas tab-bar)

**Arquivo:** `ui/chatbot-raf/index.html` e `ui/chatbot-rad/index.html`  
**Arquivo:** `ui/assets/shared.css`

**Comportamento esperado (igual ao VS Code):**
- Na aba-bar do canvas, ao lado da aba PDF, deve haver um botão fixo `⚙️` (ícone de engrenagem)
- Clicar nele ABRE ou FECHA a aba "Monitor IA" (toggle)
- Quando aberta, a aba mostra o status das chaves via `GET /health/v2`
- A aba Monitor é fechável com `×`

**Fix no HTML** — adicionar botão fixo na `.canvas-tab-bar` gerada pelo TabManager. O botão não é uma aba, é um trigger:
```html
<!-- Adicionado via JS após tabManager.init -->
<button id="btn-monitor" onclick="toggleMonitor()" title="Monitor de IA" 
  style="margin-left:auto; background:none; border:none; cursor:pointer; font-size:1rem; padding:0 10px; color:#888;">
  ⚙️
</button>
```

**Fix no JS** — a função `toggleMonitor()`:
```javascript
function toggleMonitor() {
  if (tabManager.tabs['monitor']) {
    tabManager.closeTab('monitor');
  } else {
    tabManager.addTab('monitor', 'Monitor IA', true, '<div id="monitor-content" style="padding:20px;color:#ccc;">Carregando...</div>', '⚙️');
    // Busca os dados APÓS o DOM da aba estar pronto
    setTimeout(() => {
      fetch(`${API_URL}/health/v2`)
        .then(r => r.json())
        .then(data => {
          const el = document.getElementById('monitor-content');
          if (!el) return;
          el.innerHTML = data.keys.map(k => `
            <div style="margin-bottom:12px; padding:12px; border-radius:8px; background:#2a2a3e;">
              <b>Chave ${k.id}</b> (${k.prefix}…)
              <span style="float:right; color:${k.status==='ready'?'#4caf50':k.status==='exhausted'?'#f44336':'#ff9800'}">
                ● ${k.status.toUpperCase()}
              </span>
              ${k.error ? `<div style="font-size:0.7rem;color:#aaa;margin-top:4px">${k.error}</div>` : ''}
            </div>
          `).join('') + `<div style="margin-top:16px;font-size:0.75rem;color:#666">Sistema: ${data.system}</div>`;
        })
        .catch(() => { const el = document.getElementById('monitor-content'); if(el) el.innerHTML = 'Falha ao contatar a API.'; });
    }, 50);
  }
}
```

**Fix no CSS** (`shared.css`) — estilo do botão fixo na tab-bar:
```css
.canvas-tab-bar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}
.btn-settings {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0 10px;
  color: #888;
  transition: color 0.2s;
}
.btn-settings:hover { color: var(--primary-color); }
```

**Verificação:** Clicar em ⚙️ deve abrir a aba Monitor. Clicar no `×` da aba deve fechá-la. Clicar no ⚙️ de novo deve abrí-la novamente.

- [ ] Adicionar botão ⚙️ e função `toggleMonitor()` em `chatbot-raf/index.html`
- [ ] Adicionar botão ⚙️ e função `toggleMonitor()` em `chatbot-rad/index.html`
- [ ] Adicionar CSS `.btn-settings` em `shared.css`

---

## TASK 4 — Corrigir Sidebar da Vitrine

**Arquivo:** `ui/vitrine/index.html`

**Problemas:**
1. Ícones grandes demais
2. Multi-chat listado — remover
3. Ordem e estilo dos itens errado

**Fix — CSS da sidebar:**
```css
.slim-sidebar {
  width: 52px;
  min-width: 52px;
  background: #1a1a2e;
  border-right: 1px solid #2a2a3e;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  gap: 4px;
  z-index: 100;
}

.slim-sidebar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 6px;
  color: #888;
  cursor: pointer;
  text-decoration: none;
  transition: 0.2s;
  border-radius: 6px;
  width: 44px;
}

.slim-sidebar-item:hover { background: rgba(255,255,255,0.08); color: #fff; }
.slim-sidebar-item.active { background: rgba(255,255,255,0.12); color: #fff; }

.sidebar-icon { font-size: 1.1rem; }
.sidebar-label { font-size: 0.5rem; margin-top: 3px; font-weight: 600; text-align: center; letter-spacing: 0.5px; text-transform: uppercase; }
```

**Fix — HTML da sidebar (remover Multi, manter só HUB/RAF/RAD):**
```html
<div class="slim-sidebar">
  <div class="slim-sidebar-item active" onclick="loadApp(this, '/ui/vitrine/home.html')" title="Hub de Documentos">
    <span class="sidebar-icon">🏠</span>
    <span class="sidebar-label">HUB</span>
  </div>
  <div class="slim-sidebar-item" onclick="loadApp(this, '/raf')" title="Relatório Anual do Fogo 2024">
    <span class="sidebar-icon">🔥</span>
    <span class="sidebar-label">RAF</span>
  </div>
  <div class="slim-sidebar-item" onclick="loadApp(this, '/rad')" title="Relatório Anual do Desmatamento 2024">
    <span class="sidebar-icon">🌳</span>
    <span class="sidebar-label">RAD</span>
  </div>
</div>
```

**Fix — função `loadApp`:** Remover o parâmetro `color` (não mais necessário, o active state é pelo CSS).

**Verificação:** Sidebar deve ter 52px de largura, ícones pequenos, sem cor de destaque colorida no item ativo (apenas fundo sutil branco translúcido).

- [ ] Corrigir CSS da sidebar em `vitrine/index.html`
- [ ] Remover item Multi da sidebar
- [ ] Corrigir função `loadApp()`

---

## TASK 5 — Corrigir paleta de cores do Hub (`home.html`)

**Arquivo:** `ui/vitrine/home.html`

**Problema:** O hub usa `--primary-color: #00b4d8` (azul claro) que destoa da identidade da plataforma.

**Fix:** Remover o `--primary-color` do `:root` do hub. O hub deve usar uma paleta neutra/escura:
- Fundo: `#111827` (quase preto)
- Cards: `#1f2937`
- Texto destaque: `#e5e7eb`
- Texto secundário: `#9ca3af`
- Links/hover: `#e8503a` (cor RAF, identidade da plataforma)
- Borda superior dos cards RAF: `#e8503a`, RAD: `#812411`

Remover a seção "Aplicativos" (Multi-Relatório e Busca Transversal) do hub.  
Remover o botão `← Hub de Apps` (que aponta para localhost:8501 — Streamlit inexistente).

**Verificação:** Hub deve ter paleta escura consistente com a sidebar. Nenhum elemento azul.

- [ ] Remover override de `--primary-color` do hub
- [ ] Atualizar paleta de cores do hub
- [ ] Remover seção Multi-Relatório e Busca Transversal
- [ ] Remover botão Hub de Apps

---

## TASK 6 — Remover Gaveta "Skills & Ferramentas" dos chatbots

**Arquivo:** `ui/chatbot-raf/index.html` e `ui/chatbot-rad/index.html`

**Fix:** Remover do HTML:
```html
<!-- REMOVER ESTE BLOCO INTEIRO -->
<div class="suggestions-header" onclick="toggleSkills()" ...>
  <span>Ferramentas (Skills)</span>
  ...
</div>
<div id="skills-container" ...>...</div>
```

Remover do JS as funções `toggleSkills()` e `openSkill()` e a referência a `skillsContainer` e `skillsIcon`.

**Verificação:** O painel de sugestões deve ter apenas as chips de perguntas, sem seção de ferramentas abaixo.

- [ ] Remover gaveta Skills do HTML de `chatbot-raf/index.html`
- [ ] Remover funções JS relacionadas em `chatbot-raf/index.html`
- [ ] Remover gaveta Skills do HTML de `chatbot-rad/index.html`
- [ ] Remover funções JS relacionadas em `chatbot-rad/index.html`

---

## TASK 7 — Remover botão "← Voltar" dos chatbots

**Arquivo:** `ui/chatbot-raf/index.html` e `ui/chatbot-rad/index.html`

**Fix:** Remover do HTML o elemento:
```html
<div>
  <a href="/" class="btn-download">← Voltar</a>
</div>
```
E remover o `<div>` wrapper vazio que sobrar no header.

**Verificação:** O header do chatbot deve ter apenas o logo/título à esquerda e o botão de download do PDF à direita (já no tab-bar).

- [ ] Remover botão Voltar de `chatbot-raf/index.html`
- [ ] Remover botão Voltar de `chatbot-rad/index.html`

---

## TASK 8 — Adicionar modo MOCK para testes de UI sem consumir tokens

**Arquivo:** `ui/chatbot-raf/index.html` e `ui/chatbot-rad/index.html`

**Por quê:** As chaves Gemini têm cota diária. Testes de layout não devem consumir tokens.

**Fix:** No topo do `<script>`, adicionar:
```javascript
const MOCK_MODE = true; // Mude para false para usar a API real
```

Na função `sendQuestion()`, adicionar no início:
```javascript
if (MOCK_MODE) {
  await new Promise(r => setTimeout(r, 800)); // simula latência
  addMsg(`[MOCK] Resposta simulada para: "${q}"\n\nEste é um modo de teste. Defina MOCK_MODE = false para usar a API real.`, 'bot', [
    { page: 5 }, { page: 12 }
  ]);
  isLoading = false;
  btn.disabled = false;
  btn.textContent = '➔';
  return;
}
```

**Verificação:** Com `MOCK_MODE = true`, o chat deve responder com uma mensagem fake em ~800ms sem fazer nenhuma chamada de rede. Os page links devem aparecer e navegar o PDF.

- [ ] Adicionar MOCK_MODE em `chatbot-raf/index.html`
- [ ] Adicionar MOCK_MODE em `chatbot-rad/index.html`

---

## TASK 9 — Verificação Final

Após concluir todas as tasks acima, verificar:

- [ ] `http://localhost:8000` → Vitrine com sidebar slim, hub carregado no iframe
- [ ] Clicar em 🔥 RAF na sidebar → chatbot RAF abre no iframe, PDF visível
- [ ] Clicar em 🌳 RAD na sidebar → chatbot RAD abre no iframe, PDF visível
- [ ] Clicar em ⚙️ no canvas do RAF → aba Monitor IA aparece e fecha corretamente
- [ ] Clicar no `×` da aba Monitor → volta para aba PDF
- [ ] Sugestões de perguntas aparecem e funcionam (em MOCK_MODE)
- [ ] Hub tem paleta escura sem elementos azuis
- [ ] Sidebar tem ícones pequenos, legíveis, sem overflow
- [ ] Nenhum botão "← Voltar" nos chatbots
- [ ] Nenhuma gaveta "Skills/Ferramentas" nos chatbots

---

## Notas para a IA Executora

- **Não mexer em:** `src/api.py`, `src/qa.py`, `src/guardian.py`, `config.py`, `ui/assets/config.js`, `ui/assets/tab-manager.js`
- **Não criar novos arquivos** — todas as mudanças são em arquivos existentes
- **Sempre verificar no browser** antes de marcar uma task como concluída
- **Se encontrar um bug novo**, descrever no final deste arquivo antes de tentar corrigir
- O backend deve estar rodando em porta 8000 durante todos os testes
