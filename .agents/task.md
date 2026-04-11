# vector-hub-factory — Task List (Revisado)

> **Para a IA executora:**
> 1. Leia `.agents/skills/vector_hub_factory/SKILL.md` ANTES de começar.
> 2. O projeto raiz é: `c:\Users\wallace.silva\OneDrive - IPAM-Amazonia\Área de Trabalho\projetos\RAF-chatbot`
>    Abrevie como `ROOT` abaixo.
> 3. Cada tarefa tem critério de sucesso. Somente marque `[x]` após verificar.
> 4. **NÃO mova nem edite a pasta `.agents/`**.
> 5. **REFERÊNCIA DE DESIGN:** O arquivo `ROOT\ui\index.html` é o padrão visual que TODO novo HTML deve replicar. Leia-o completamente antes de criar qualquer HTML novo.

---

## FASE 0–5 — Concluídas ✅

- [x] T00 — Contratar Skills e Orquestradores
- [x] T01 — Arquivar projeto atual em `references/mapbiomas-chat/`
- [x] T02 — Criar estrutura de pastas nova
- [x] T03 — Criar `config.py` global
- [x] T04 — Criar `factory/01_chunk_pdf.py`
- [x] T05 — Criar `factory/02_01_embed_gemini.py`
- [x] T06 — Criar `factory/02_embed_chunks.py` (genérico)
- [x] T07 — Criar `factory/03_query_index.py`
- [x] T08 — Criar `factory/04_embed_text.py`
- [x] T09 — Criar `factory/00_run_all.py`
- [x] T10 — Migrar RAF chatbot para `apps/raf_chatbot/app.py` (Streamlit — substituído nas fases abaixo)
- [x] T11 — Migrar RAD chatbot para `apps/rad_chatbot/app.py` (Streamlit — substituído)
- [x] T12 — Criar `app.py` (Vitrine Streamlit — substituída pela HTML nas fases abaixo)
- [x] T13 — Criar `apps/multi_report/app.py` (Streamlit — substituído)
- [x] T14 — Criar `apps/cross_search/app.py` (Streamlit — substituído)

> ⚠️ Os apps Streamlit (T10–T14) estão funcionais mas serão substituídos por HTMLs que replicam fielmente o `ui/index.html`. O FastAPI (`src/api.py`) continua como backend de TODOS os apps.

---

## FASE 6 — Design System HTML Compartilhado

- [x] **T15 — Criar `ui/assets/shared.css`**
  - Criar as pastas: `ROOT\ui\assets\`
  - Criar o arquivo `ROOT\ui\assets\shared.css`
  - **Referência:** Leia a seção `<style>` do arquivo `ROOT\ui\index.html` (linhas 7–243)
  - Copiar TODOS os estilos da tag `<style>` para o `shared.css`
  - Adicionar ao final do arquivo as seguintes regras para documentos com cor dinâmica:
    ```css
    /* Cor primária dinâmica — sobrescrita por JavaScript */
    .primary-bg { background-color: var(--primary-color) !important; }
    .primary-color { color: var(--primary-color) !important; }
    .primary-border { border-color: var(--primary-color) !important; }
    ```
  - **NÃO remover** os estilos do `ui/index.html` ainda — apenas copiar.
  - **Critério de sucesso:** O arquivo `ROOT\ui\assets\shared.css` existe e tem mais de 200 linhas.

---

## FASE 7 — Vitrine HTML Estática (GitHub Pages)

- [x] **T16 — Criar `ui/vitrine/index.html`**
  - Criar a pasta: `ROOT\ui\vitrine\`
  - Criar o arquivo `ROOT\ui\vitrine\index.html`
  - **Referência de estilo:** `ROOT\ui\index.html` (mesmo CSS, mesma tipografia)
  - **IMPORTANTE:** Este arquivo é 100% estático — sem chamadas de API. Todos os dados são hardcoded com base no conteúdo atual do `ROOT\config.py`.
  - O arquivo deve conter:
    - `<link rel="stylesheet" href="/assets/shared.css">` no `<head>`
    - `<script src="/assets/config.js"></script>` no `<head>`
    - **Header** com logo e título "Vector Hub Factory"
    - **Grid de cards** (um por documento: RAF e RAD), cada card com:
      ```html
      <!-- Exemplo de card RAF -->
      <div class="doc-card" style="border-top: 4px solid #E8503A;">
        <div class="card-header">
          <span class="card-emoji">🔥</span>
          <h2>Relatório Anual do Fogo</h2>
          <span class="card-badge">RAF 2024</span>
        </div>
        <div class="card-downloads">
          <a href="[URL_GITHUB_RELEASE_PDF]" class="btn-download">⬇️ PDF Completo</a>
          <h4>🤖 Dados IA-Ready — Gemini</h4>
          <a href="[URL_FAISS_INDEX]" class="btn-download-small">⬇️ faiss.index</a>
          <a href="[URL_META_JSON]" class="btn-download-small">⬇️ meta.json</a>
          <p class="card-meta">768 dimensões · Gratuito · Google AI Studio</p>
        </div>
        <a href="http://localhost:8000" class="btn-chatbot">💬 Abrir Chatbot</a>
      </div>
      ```
    - Seção **"Como usar os dados"** com snippet de código:
      ```html
      <pre><code>python factory/03_query_index.py \
        --index docs/raf/data/embeddings/gemini-embedding-001/faiss.index \
        --meta  docs/raf/data/embeddings/gemini-embedding-001/meta.json \
        --text  "área queimada no cerrado" \
        --top-k 5</code></pre>
      ```
    - **Rodapé** com link para GitHub
  - Use URLs placeholder `[URL_GITHUB_RELEASE_PDF]` nos links de download — serão preenchidos após o primeiro release.
  - Para os links do chatbot, use `window.VHF_CONFIG.API_URL` (lido do `config.js`):
    ```javascript
    document.querySelectorAll('.btn-chatbot').forEach(btn => {
      btn.href = window.VHF_CONFIG.API_URL;
    });
    ```
  - **Critério de sucesso:** Abrir `ROOT\ui\vitrine\index.html` diretamente no browser (sem servidor) — a página carrega com os 2 cards de documentos visíveis. Não pode ter erros no console do browser.

- [x] **T19 — Criar pasta `public/` para GitHub Pages**
  - Criar a pasta `ROOT\public\`
  - Copiar `ROOT\ui\vitrine\index.html` para `ROOT\public\index.html`
  - Criar o arquivo `ROOT\.github\workflows\pages.yml` com o conteúdo:
    ```yaml
    name: Deploy GitHub Pages

    on:
      push:
        branches: [main]

    jobs:
      deploy:
        runs-on: ubuntu-latest
        permissions:
          contents: read
          pages: write
          id-token: write
        steps:
          - uses: actions/checkout@v4

          - name: Copy vitrine to public
            run: cp ui/vitrine/index.html public/index.html

          - name: Setup Pages
            uses: actions/configure-pages@v4

          - name: Upload artifact
            uses: actions/upload-pages-artifact@v3
            with:
              path: public/

          - name: Deploy to GitHub Pages
            uses: actions/deploy-pages@v4
    ```
  - **Critério de sucesso:** O arquivo `ROOT\public\index.html` existe e `ROOT\.github\workflows\pages.yml` existe.

- [x] **T21 — Criar `ui/assets/config.js`**
  - Criar o arquivo `ROOT\ui\assets\config.js` com o conteúdo exato:
    ```javascript
    // Vector Hub Factory — Configuração de URLs
    // Edite apenas este arquivo para apontar para produção.
    window.VHF_CONFIG = {
      API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : 'https://vector-hub-factory.onrender.com',
    };
    ```
  - **Critério de sucesso:** O arquivo existe. Abrir o browser console em `localhost:8000` e digitar `window.VHF_CONFIG.API_URL` retorna `"http://localhost:8000"`.

---

## FASE 8 — Busca Transversal HTML

- [x] **T17 — Criar `ui/cross/index.html`**
  - Criar a pasta: `ROOT\ui\cross\`
  - Criar o arquivo `ROOT\ui\cross\index.html`
  - **Ponto de partida:** Copiar TODO o conteúdo de `ROOT\ui\index.html` para o novo arquivo
  - **Modificações em relação ao `index.html` original:**
    1. Alterar o `<title>` para `"Busca Transversal — Vector Hub Factory"`
    2. Remover as abas de documentos (a busca é sempre em tudo)
    3. Alterar o placeholder do `<textarea>` para `"Busca em todos os relatórios..."`
    4. Adicionar ao `questionBanks` uma seção `cross` com perguntas que cruzam documentos:
       ```javascript
       const crossQuestions = [
         { label: "🔥🌳 Fogo vs Desmatamento", q: "Como o fogo se relaciona com o desmatamento no Brasil?" },
         { label: "🌿 Biomas", q: "Quais biomas sofreram mais com fogo E desmatamento em 2024?" },
         { label: "🛡️ Proteção", q: "Terras indígenas são mais protegidas do fogo ou do desmatamento?" }
       ];
       ```
    5. Modificar a função `sendQuestion()` para chamar `POST /ask_cross` em vez de `POST /ask`
    6. Modificar a função `addMsg()` para mostrar badges de origem:
       - Receber `sources` com campo `doc` adicional
       - Exibir `[RAF p.14]` `[RAD p.22]` em vez de apenas `p. X`
    7. Modificar `goToPage()` para aceitar também o documento:
       ```javascript
       function goToPage(page, doc) {
         pdfIframe.src = `${window.VHF_CONFIG.API_URL}/pdf/${doc}?t=${Date.now()}#page=${page}&toolbar=0`;
       }
       ```
  - **Critério de sucesso:** `http://localhost:8000/cross` abre a página com o mesmo visual do chatbot original, mas sem abas de documento.

- [x] **T18 — Expandir `src/api.py` com novas rotas**
  - **Referência:** Leia `ROOT\src\api.py` completamente antes de editar.
  - Adicionar as seguintes importações no topo do arquivo (após as existentes):
    ```python
    from src.qa import answer, search
    from config import DOCUMENTS
    import numpy as np
    ```
  - Adicionar a classe de request para cross-search:
    ```python
    class CrossQuestion(BaseModel):
        question: str
        model: str = "flash"
    ```
  - Adicionar as seguintes rotas AO FINAL do arquivo (antes não há rotas definidas após `/ask`):
    ```python
    @app.get("/cross")
    def cross_page():
        cross_path = os.path.join(os.path.dirname(__file__), "..", "ui", "cross", "index.html")
        return FileResponse(cross_path)

    @app.get("/hub")
    def hub_page():
        hub_path = os.path.join(os.path.dirname(__file__), "..", "ui", "vitrine", "index.html")
        return FileResponse(hub_path)

    @app.get("/assets/{filename}")
    def serve_asset(filename: str):
        asset_path = os.path.join(os.path.dirname(__file__), "..", "ui", "assets", filename)
        if not os.path.exists(asset_path):
            raise HTTPException(status_code=404, detail="Asset não encontrado.")
        return FileResponse(asset_path)

    @app.post("/ask_cross")
    def ask_cross(q: CrossQuestion):
        if not q.question.strip():
            raise HTTPException(status_code=400, detail="Pergunta vazia")

        from src.qa import search
        from src.embedder import embed_query
        from config import DOCUMENTS, GOOGLE_API_KEY
        import faiss, json
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)

        # 1. Gerar embedding da pergunta
        query_vec = embed_query(q.question)

        # 2. Buscar em todos os documentos com índice disponível
        all_sources = []
        for doc_key, doc_cfg in DOCUMENTS.items():
            emb_cfg = doc_cfg.get("embeddings", {}).get("gemini", {})
            index_path = emb_cfg.get("index", "")
            meta_path = emb_cfg.get("meta", "")
            if not (os.path.exists(index_path) and os.path.exists(meta_path)):
                continue
            index = faiss.read_index(index_path)
            with open(meta_path) as f:
                meta = json.load(f)
            vec = np.array([query_vec], dtype="float32")
            scores, indices = index.search(vec, 5)
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(meta):
                    chunk = meta[idx].copy()
                    chunk["score"] = float(score)
                    chunk["doc"] = doc_key
                    chunk["doc_short"] = doc_cfg["short"]
                    all_sources.append(chunk)

        # 3. Re-ranquear por score (menor = mais similar em L2)
        all_sources.sort(key=lambda x: x["score"])
        top_sources = all_sources[:8]

        # 4. Montar contexto com indicação de origem
        context_parts = []
        for s in top_sources:
            origin = f"[{s['doc_short']}, p.{s['page']}]"
            context_parts.append(f"{origin} {s['content']}")
        context = "\n\n".join(context_parts)

        # 5. Chamar LLM
        from config import LLM_MODELS
        model_name = LLM_MODELS.get(q.model, LLM_MODELS["flash"])
        model = genai.GenerativeModel(model_name)
        prompt = f"""Você é um assistente especializado em relatórios do MapBiomas.
Use APENAS as informações abaixo para responder. Ao citar dados, indique a origem entre colchetes como [RAF, p.X] ou [RAD, p.X].

Contexto:
{context}

Pergunta: {q.question}
"""
        response = model.generate_content(prompt)
        return {
            "answer": response.text,
            "sources": top_sources,
            "model": q.model
        }
    ```
  - **Critério de sucesso:** Rodar `curl -X POST http://localhost:8000/ask_cross -H "Content-Type: application/json" -d "{\"question\": \"fogo e desmatamento\", \"model\": \"flash\"}"` retorna JSON com `answer` e `sources` sem erro 500.

---

## FASE 9 — Deploy

- [x] **T20 — Criar `render.yaml`**
  - Criar o arquivo `ROOT\render.yaml` com o conteúdo exato:
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
          - key: GOOGLE_API_KEY_ALT
            sync: false
    ```
  - **Critério de sucesso:** O arquivo `ROOT\render.yaml` existe e tem YAML válido (pode verificar com `python -c "import yaml; yaml.safe_load(open('render.yaml'))"` sem erros).

---

## FASE 10 — Limpeza

- [x] **T22 — Simplificar `start_all.bat`**
  - Criar o arquivo `ROOT\start_all.bat` (substituir o existente) com o conteúdo:
    ```bat
    @echo off
    echo ========================================
    echo   Vector Hub Factory - Iniciando...
    echo ========================================
    echo.
    echo Acesse:
    echo   Chatbot:  http://localhost:8000
    echo   Busca:    http://localhost:8000/cross
    echo   Vitrine:  http://localhost:8000/hub
    echo.
    start "VHF" cmd /k ".venv\Scripts\activate && uvicorn src.api:app --port 8000 --reload"
    echo ========================================
    pause
    ```
  - **Critério de sucesso:** Rodar `start_all.bat` abre 1 janela de terminal. `http://localhost:8000` abre o chatbot sem erro.

- [x] **T23 — Criar skill `html_app_factory`**
  - Criar a pasta: `ROOT\.agents\skills\html_app_factory\`
  - Criar o arquivo `ROOT\.agents\skills\html_app_factory\SKILL.md` com o conteúdo:

  ````markdown
  ---
  name: html_app_factory
  description: Padrão para criar novos apps HTML+FastAPI no vector-hub-factory com fidelidade visual ao ui/index.html de referência.
  ---

  # html_app_factory — Skill

  Use esta skill ao criar qualquer novo frontend HTML para o projeto.

  ## Regra #1 — Nunca partir do zero
  Sempre copie `ROOT/ui/index.html` como ponto de partida e modifique.
  Nunca crie um HTML novo sem ler o original primeiro.

  ## Regra #2 — CSS compartilhado
  Todo HTML novo deve ter no `<head>`:
  ```html
  <link rel="stylesheet" href="/assets/shared.css">
  <script src="/assets/config.js"></script>
  ```
  Nunca copiar `<style>` inline — usar o compartilhado.

  ## Regra #3 — URLs via config.js
  Nunca hardcode `http://localhost:8000`. Usar sempre:
  ```javascript
  const apiUrl = window.VHF_CONFIG.API_URL;
  ```

  ## Regra #4 — Registrar no api.py
  Todo novo HTML precisa de uma rota GET no `src/api.py`:
  ```python
  @app.get("/novo-app")
  def novo_app():
      return FileResponse("ui/novo-app/index.html")
  ```

  ## Regra #5 — Testar sem servidor
  A vitrine (`ui/vitrine/index.html`) deve abrir sem backend.
  Os chatbots (`ui/index.html`, `ui/cross/index.html`) precisam do uvicorn rodando.

  ## Checklist antes de entregar um novo app HTML

  - [ ] Copiou `ui/index.html` como base
  - [ ] Usa `/assets/shared.css` (não tem `<style>` inline)
  - [ ] Usa `window.VHF_CONFIG.API_URL` para todas as chamadas de API
  - [ ] Tem rota GET registrada no `src/api.py`
  - [ ] Testou no browser sem erros no console
  - [ ] Aparência visual idêntica ao chatbot original (mesma fonte, cores, layout)
  ````

  - **Critério de sucesso:** O arquivo `ROOT\.agents\skills\html_app_factory\SKILL.md` existe e tem mais de 50 linhas.

---

## Critérios de Conclusão Final

Antes de declarar o projeto concluído, verificar:

- [ ] `http://localhost:8000` → chatbot multi-relatório (visual idêntico ao `ui/index.html`)
- [ ] `http://localhost:8000/cross` → busca transversal com badges `[RAF p.X]`
- [ ] `http://localhost:8000/hub` → vitrine estática funciona localmente
- [ ] Abrir `ROOT\public\index.html` no browser sem servidor → página carrega normalmente
- [ ] `ROOT\.github\workflows\pages.yml` existe
- [ ] `ROOT\render.yaml` existe e tem YAML válido
- [ ] `ROOT\ui\assets\shared.css` existe com mais de 200 linhas
- [ ] `ROOT\ui\assets\config.js` existe
- [ ] `ROOT\.agents\skills\html_app_factory\SKILL.md` existe
- [ ] `start_all.bat` inicia 1 único processo
