---
name: vector_hub_factory
description: Guia de arquitetura, convenções e fluxo de trabalho do projeto vector-hub-factory. Leia ANTES de qualquer alteração de código ou estrutura de pastas.
---

# vector-hub-factory — Skill de Manutenção

Este documento define as regras, convenções e padrões do projeto `vector-hub-factory`.
**Leia integralmente antes de fazer qualquer modificação no projeto.**

---

## 1. Identidade do Projeto

- **Nome do repositório:** `vector-hub-factory`
- **Propósito:** Fábrica de dados IA-Ready para documentos científicos (PDFs)
- **Referência preservada:** O projeto original `RAF-chatbot` está em `references/mapbiomas-chat/`

## 2. Estrutura de Pastas (Regras Obrigatórias)

```
vector-hub-factory/
├── app.py                    ← Vitrine Streamlit (Hub principal)
├── config.py                 ← ÚNICO ponto de registro de documentos
├── docs/                     ← Um documento = Uma pasta autônoma
│   └── {doc_id}/
│       ├── {doc_id}.pdf      ← PDF original
│       └── data/             ← Tudo gerado fica AQUI, nunca fora desta pasta
│           ├── chunks/
│           │   └── chunks.json
│           └── embeddings/
│               └── {model_id}/
│                   ├── faiss.index
│                   └── meta.json
├── factory/                  ← Scripts autônomos, sem dependência cruzada
│   ├── 00_run_all.py         ← Orquestrador principal
│   ├── 01_chunk_pdf.py       ← Chunk Factory
│   ├── 02_embed_chunks.py    ← Embedding Factory (genérico)
│   ├── 02_01_embed_gemini.py ← Embedding Factory (Gemini)
│   ├── 02_02_embed_ollama.py ← Embedding Factory (Ollama local) [planejado]
│   ├── 02_03_embed_openrouter.py [planejado]
│   ├── 02_04_embed_groq.py   [planejado]
│   ├── 03_query_index.py     ← Query Factory (universal)
│   └── 04_embed_text.py      ← Demo / Hello World de embeddings
└── apps/
    ├── {doc_id}_chatbot/
    │   └── app.py            ← Chatbot individual por documento
    ├── multi_report/
    │   └── app.py            ← Alternância entre documentos (sem cruzar dados)
    └── cross_search/
        └── app.py            ← Busca transversal em .index E .pdf disponíveis
```

**Regras:**
- ❌ NUNCA salvar dados gerados fora de `docs/{doc_id}/data/`
- ❌ NUNCA registrar um documento novo fora do `config.py`
- ✅ Cada script da `factory/` deve funcionar independentemente, sem imports do projeto

---

## 3. Registro de Documentos (`config.py`)

Todo novo documento DEVE ser registrado em `config.py` com esta estrutura:

```python
DOCUMENTS = {
    "raf": {
        "name": "Relatório Anual do Fogo",
        "short": "RAF",
        "emoji": "🔥",
        "color": "#E8503A",
        "pdf": "docs/raf/RAF2024.pdf",
        "chunks": "docs/raf/data/chunks/chunks.json",
        "embeddings": {
            "gemini": {
                "index": "docs/raf/data/embeddings/gemini-embedding-001/faiss.index",
                "meta":  "docs/raf/data/embeddings/gemini-embedding-001/meta.json",
                "model_id": "models/gemini-embedding-001",
                "dims": 768,
                "cost": "Gratuito (quota)",
                "provider": "Google AI Studio"
            }
        },
        "prompt_role": "assistente especializado no RAF",
        "app": "apps/raf_chatbot/app.py"
    }
    # Adicionar novos documentos aqui
}
```

---

## 4. Fábricas — Convenções de Parâmetros

Todos os scripts da `factory/` seguem estas convenções de argparse:

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `--pdf` | path | Caminho do PDF de entrada |
| `--chunks` | path | Caminho do `chunks.json` |
| `--index` | path | Caminho do `faiss.index` |
| `--meta` | path | Caminho do `meta.json` |
| `--model` | str | ID do modelo (`gemini`, `ollama`, `openrouter`, `groq`) |
| `--top-k` | int | Número de chunks a retornar (default: 5) |
| `--api-key` | str | Chave da API (default: lê do `.env`) |
| `--output-dir` | path | Diretório de saída (default: calculado automaticamente) |

---

## 5. Modelos Suportados

| ID | Modelo | Dims | Custo | Status |
|---|---|---|---|---|
| `gemini` | `models/gemini-embedding-001` | 768 | Gratuito (quota) | ✅ Ativo |
| `ollama` | `nomic-embed-text` (local) | 768 | Gratuito | 🔧 Planejado |
| `openrouter` | variável | variável | Pago | 🔧 Planejado |
| `groq` | variável | variável | Pago | 🔧 Planejado |

**Regra:** O modelo usado para indexar (`02_embed`) DEVE ser o mesmo usado para buscar (`03_query`).

---

## 6. Apps — Style Guide

Todos os apps (`apps/*/app.py`) compartilham:

- **Layout:** Split — Chat ~30% à esquerda + PDF ~70% à direita
- **Paleta primária:** Definida por documento em `config.py` (campo `color`)
- **Paleta global:** Fundo escuro `#1a1a2e`, texto `#e0e0e0`
- **Componentes padrão:**
  - Input de chat com sugestões em chips (upward-opening drawer)
  - Visualizador de PDF com navegação por página
  - Fontes de resposta clicáveis que saltam para a página no PDF
- **CSS:** Injetado via `st.markdown(unsafe_allow_html=True)` + padrões do `streamlit_ux_pro`
- **Referência de design:** HTML do `references/mapbiomas-chat/` é o padrão visual a replicar

---

## 7. Adicionando um Novo Documento (Checklist)

- [ ] Criar pasta `docs/{doc_id}/` com o PDF
- [ ] Rodar `python factory/00_run_all.py` (detecta automaticamente)
- [ ] Adicionar entrada em `config.py`
- [ ] A vitrine e os apps detectam automaticamente — sem editar código

---

## 8. Adicionando um Novo Modelo de Embedding (Checklist)

- [ ] Criar `factory/02_0X_embed_{model}.py` seguindo a interface padrão
- [ ] Registrar o modelo em `config.py` no campo `embeddings` do documento
- [ ] Rodar o novo script para gerar `.index` e `meta.json`
- [ ] A vitrine exibirá automaticamente o novo card de download

---

## 9. Skills Relacionadas

- **`streamlit_ux_pro`**: Para CSS e layout fullscreen nos apps Streamlit
- **`app_validator`**: Para validar paridade entre apps e referência HTML
