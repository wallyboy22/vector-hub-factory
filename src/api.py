"""
api.py — Vector Hub Factory Backend v4.0
==========================================
Multi-provedor: Groq (LLM prim.) + Gemini (embed + fallback LLM) + Jina + HuggingFace
DEV_MODE: endpoints de factory e upload apenas em modo desenvolvedor (local)
"""

import os
import sys
import uuid
import time
import threading
import numpy as np
import faiss
import json
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional

# ── Setup path ─────────────────────────────────────────────────────────────────
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.ERROR)

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

print("\n" + "="*55)
print("  [VHF] VECTOR HUB FACTORY - BACKEND v4.0")
print("="*55)

from config import (
    DOCUMENTS, LLM_MODELS, GOOGLE_API_KEY, EMBEDDING_MODEL,
    ALL_API_KEYS, DEV_MODE, GROQ_API_KEY, EMBEDDING_PROVIDERS, LLM_PROVIDERS, HUB_CONFIG,
    set_dev_mode, _save_env_key
)
from src.qa import (
    answer, get_client, _key_blacklist, _clients,
    get_key_status, get_engine_registry
)
from src.guardian import AppGuardian
from google import genai

# ── Guardião ──────────────────────────────────────────────────────────────────
guardian = AppGuardian()
integrity = guardian.check_system_integrity()
if not integrity["ready"]:
    print("\n[!] Problemas detectados:")
    for issue in integrity["issues"]:
        print(f"  ! {issue}")
else:
    print(f"\n[OK] Integridade confirmada. DEV_MODE={'SIM (Desenvolvedor)' if DEV_MODE else 'NÃO (Usuário)'}\n")

# ── Groq status ───────────────────────────────────────────────────────────────
if GROQ_API_KEY:
    print(f"  [LLM] Groq configurado: {GROQ_API_KEY[:8]}...")
else:
    print("  [LLM] Groq: sem chave — Gemini será o primário.")

# ── App FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI(title="Vector Hub Factory", version="4.0")

ui_path = os.path.join(os.path.dirname(__file__), "..", "ui")
docs_path = os.path.join(os.path.dirname(__file__), "..")

app.mount("/ui", StaticFiles(directory=ui_path), name="ui")

# ── Jobs de background (factory) ─────────────────────────────────────────────
_jobs: dict[str, dict] = {}

def _run_job(job_id: str, fn, *args):
    """Executa uma função em thread separada e rastreia o status."""
    _jobs[job_id] = {"status": "running", "progress": 0.0, "message": "Iniciando...", "started_at": time.time()}
    try:
        fn(job_id, *args)
        _jobs[job_id].update({"status": "done", "progress": 1.0, "message": "Concluído!"})
    except Exception as e:
        _jobs[job_id].update({"status": "error", "progress": 0.0, "message": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# ROTAS BASE
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return FileResponse(os.path.join(ui_path, "apps", "vitrine", "index.html"))

# ── App RAF ───────────────────────────────────────────────────────────────
@app.get("/raf")
@app.get("/raf/")
def page_raf():
    return FileResponse(os.path.join(ui_path, "apps", "raf", "index.html"))

@app.get("/raf/pdf")
@app.get("/raf/pdf/")
def pdf_raf():
    return FileResponse(os.path.join(root_path, "docs", "raf", "RAF2024.pdf"))

@app.get("/raf/brain")
@app.get("/raf/brain/")
def brain_raf():
    return RedirectResponse("/raf?tab=brain")

# ── App RAD ───────────────────────────────────────────────────────────────
@app.get("/rad")
@app.get("/rad/")
def page_rad():
    return FileResponse(os.path.join(ui_path, "apps", "rad", "index.html"))

@app.get("/rad/pdf")
@app.get("/rad/pdf/")
def pdf_rad():
    return FileResponse(os.path.join(root_path, "docs", "rad", "RAD2024.pdf"))

@app.get("/rad/brain")
@app.get("/rad/brain/")
def brain_rad():
    return RedirectResponse("/rad?tab=brain")

@app.get("/pdfs")
@app.get("/pdfs/")
@app.get("/embeddings")
@app.get("/embeddings/")
@app.get("/monitoring")
@app.get("/monitoring/")
def page_hub_sections():
    return FileResponse(os.path.join(ui_path, "apps", "vitrine", "index.html"))

@app.get("/relatorios_anuais")
@app.get("/relatorios_anuais/")
def page_relatorios_anuais():
    return FileResponse(os.path.join(ui_path, "apps", "relatorios_anuais", "index.html"))

@app.get("/relatorios_anuais/pdf")
@app.get("/relatorios_anuais/pdf/")
def pdf_relatorios_anuais():
    return FileResponse(os.path.join(root_path, "docs", "raf", "RAF2024.pdf"))

@app.get("/relatorios_anuais/brain")
@app.get("/relatorios_anuais/brain/")
def brain_relatorios_anuais():
    return RedirectResponse("/relatorios_anuais?tab=brain")

# ── Factory Apps ───────────────────────────────────────────────────
@app.get("/apps")
@app.get("/apps/")
def page_apps():
    return FileResponse(os.path.join(ui_path, "apps", "vitrine", "index.html"))

@app.get("/assets/{filename}")
def serve_asset(filename: str):
    for path in [
        os.path.join(ui_path, "assets", filename),
        os.path.join(ui_path, "assets", "logos", filename),
    ]:
        if os.path.exists(path):
            return FileResponse(path)
    raise HTTPException(404, "Asset não encontrado.")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO E STATUS (API)
# ═══════════════════════════════════════════════════════════════════════════════

from src.discovery import discover_indices
discover_indices()

@app.get("/factory/apps")
def get_factory_apps():
    """Retorna o registry de apps nativos (emoji, perguntas, cores)."""
    from config import APP_REGISTRY
    return APP_REGISTRY

@app.get("/config")
def get_config():
    """Retorna a configuração do Hub para o frontend (DEV_MODE, providers disponíveis)."""
    from src.qa import get_key_status, OPENCODE_API_KEY
    keys = get_key_status()
    gemini_avail = any(k["status"] == "DISPONÍVEL" for k in keys if k["provider"] == "gemini")

    return {
        "dev_mode":      DEV_MODE,
        "hub":           HUB_CONFIG,
        "llm_providers": {k: v for k, v in LLM_PROVIDERS.items()},
        "embedding_providers": EMBEDDING_PROVIDERS,
        "groq_available": bool(GROQ_API_KEY),
        "gemini_keys": len(ALL_API_KEYS),
        "gemini_available": gemini_avail,
        "bigpickle_available": bool(OPENCODE_API_KEY),
    }

@app.get("/usage")
def get_usage():
    """Retorna o uso de tokens do dia."""
    from src.telemetry import get_daily_usage
    return get_daily_usage()

@app.get("/keys")
def list_keys():
    """Status de saúde de todas as chaves API."""
    return get_key_status()

@app.get("/reports")
def list_reports():
    """Metadados de todos os documentos registrados."""
    result = {}
    for key, cfg in DOCUMENTS.items():
        # Check standard config
        embeddings = {
            provider: os.path.exists(emb.get("index", ""))
            for provider, emb in cfg.get("embeddings", {}).items()
        }
        
        # Auto-discover from assets/embeddings folder
        emb_dir = os.path.join("docs", key, "assets", "embeddings")
        if os.path.exists(emb_dir):
            for model_folder in os.listdir(emb_dir):
                # Map model_folder back to provider id if possible
                for p_id, p_info in EMBEDDING_PROVIDERS.items():
                    if p_info["model_id"].replace("/", "-") == model_folder:
                        idx_path = os.path.join(emb_dir, model_folder, "faiss.index")
                        if os.path.exists(idx_path):
                            embeddings[p_id] = True

        result[key] = {
            "name":       cfg["name"],
            "short":      cfg["short"],
            "emoji":      cfg["emoji"],
            "color":      cfg["color"],
            "has_pdf":    os.path.exists(cfg.get("pdf", "")),
            "embeddings": embeddings,
        }
    return result

@app.get("/models")
def list_models():
    return list(LLM_MODELS.keys())

@app.get("/providers/{doc_id}")
def get_providers_for_doc(doc_id: str):
    """Quais índices de embedding existem para um documento."""
    cfg = DOCUMENTS.get(doc_id)
    if not cfg:
        raise HTTPException(404, f"Documento '{doc_id}' não encontrado.")

    result = {}
    for provider_id, provider_cfg in EMBEDDING_PROVIDERS.items():
        # Tenta localizar o índice na estrutura padrão
        index_path = os.path.join(
            "docs", doc_id, "assets", "embeddings", provider_cfg["model_id"].replace("/", "-"), "faiss.index"
        )
        # Também verifica no config caso exista entrada explícita
        if doc_id in DOCUMENTS and provider_id in DOCUMENTS[doc_id].get("embeddings", {}):
            index_path = DOCUMENTS[doc_id]["embeddings"][provider_id].get("index", index_path)

        result[provider_id] = {
            **provider_cfg,
            "index_exists": os.path.exists(index_path),
            "index_path":   index_path,
        }
    return result

@app.get("/health")
def health():
    from src.qa import get_engine_registry
    return {
        "status":   "ok",
        "version":  "4.0",
        "dev_mode": DEV_MODE,
        "engines":  get_engine_registry(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ARQUIVOS ESTÁTICOS (PDFs, índices, meta)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/pdf/{report}")
def get_pdf(report: str):
    cfg = DOCUMENTS.get(report)
    if not cfg or not os.path.exists(cfg["pdf"]):
        raise HTTPException(404, "PDF não encontrado.")
    return FileResponse(cfg["pdf"], media_type="application/pdf")

@app.get("/index/{report}/{provider}")
@app.get("/index/{report}")
def get_index(report: str, provider: str = "gemini"):
    cfg = DOCUMENTS.get(report)
    if not cfg:
        raise HTTPException(404)
    path = cfg.get("embeddings", {}).get(provider, {}).get("index", "")
    if not os.path.exists(path):
        raise HTTPException(404, f"Índice '{provider}' não encontrado para '{report}'.")
    return FileResponse(path, filename=f"{report}_{provider}_faiss.index")

@app.get("/meta/{report}/{provider}")
@app.get("/meta/{report}")
def get_meta(report: str, provider: str = "gemini"):
    cfg = DOCUMENTS.get(report)
    if not cfg:
        raise HTTPException(404)
    path = cfg.get("embeddings", {}).get(provider, {}).get("meta", "")
    if not os.path.exists(path):
        raise HTTPException(404, f"Meta '{provider}' não encontrado para '{report}'.")
    return FileResponse(path, filename=f"{report}_{provider}_meta.json")

@app.get("/logo/{report}")
def get_logo(report: str):
    cfg = DOCUMENTS.get(report)
    if not cfg or "logo" not in cfg or not os.path.exists(cfg["logo"]):
        raise HTTPException(404, "Logo não encontrada.")
    return FileResponse(cfg["logo"])


# ═══════════════════════════════════════════════════════════════════════════════
# BRAIN (Visualização 3D do Cérebro)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/brain/combined")
def get_brain_combined(provider: str = "gemini"):
    """Retorna cérebro combinado de todos os docs."""
    all_neurons = []
    doc_ids = list(DOCUMENTS.keys())
    
    for doc_id in doc_ids:
        paths_to_try = [
            os.path.join("docs", doc_id, "assets", "embeddings", provider, "brain.json"),
            os.path.join("docs", doc_id, "assets", "embeddings", "gemini-embedding-001", "brain.json"),
            os.path.join("docs", doc_id, "assets", "embeddings", "jina-embeddings-v3", "brain.json"),
        ]
        
        brain_path = None
        for p in paths_to_try:
            if os.path.exists(p):
                brain_path = p
                break
        
        if brain_path and os.path.exists(brain_path):
            with open(brain_path, encoding="utf-8") as f:
                brain = json.load(f)
                for n in brain.get("neurons", []):
                    n["source_doc"] = doc_id
                    all_neurons.append(n)
    
    return {
        "provider": provider,
        "doc_count": len(set(n.get("source_doc") for n in all_neurons)),
        "chunk_count": len(all_neurons),
        "neurons": all_neurons
    }


@app.get("/brain/{doc_id}")
def get_brain(doc_id: str, provider: str = "gemini"):
    """Retorna o cérebro (brain.json) do doc."""
    # Map provider names to folder names
    provider_folders = {
        "gemini": "gemini-embedding-001",
        "jina": "jina-embeddings-v3",
    }
    folder = provider_folders.get(provider, provider)
    
    # Try provider-specific path first, then fallbacks
    paths_to_try = [
        os.path.join("docs", doc_id, "assets", "embeddings", folder, "brain.json"),
        os.path.join("docs", doc_id, "assets", "embeddings", "gemini-embedding-001", "brain.json"),
        os.path.join("docs", doc_id, "assets", "embeddings", "jina-embeddings-v3", "brain.json"),
    ]
    
    brain_path = None
    for p in paths_to_try:
        if os.path.exists(p):
            brain_path = p
            break
    
    if not brain_path:
        raise HTTPException(404, f"Cérebro não encontrado para {doc_id}/{provider}.")
    
    with open(brain_path, encoding="utf-8") as f:
        brain = json.load(f)
    
    return brain


@app.get("/brain/{doc_id}/query")
def brain_query(doc_id: str, question: str, provider: str = "gemini"):
    """Retorna brain com neurônios da query ativados."""
    cfg = DOCUMENTS.get(doc_id)
    if not cfg:
        raise HTTPException(404, f"Doc '{doc_id}' não encontrado.")
    
    emb_cfg = cfg.get("embeddings", {}).get(provider)
    if not emb_cfg:
        raise HTTPException(404, f"Embedding '{provider}' não encontrado.")
    
    brain_path = emb_cfg.get("brain")
    if not brain_path or not os.path.exists(brain_path):
        raise HTTPException(404, "Cérebro não encontrado.")
    
    with open(brain_path, encoding="utf-8") as f:
        brain = json.load(f)
    
    # Pegar embeddings do FAISS para calcular scores
    from src.vectorstore import load_index
    meta_path = emb_cfg.get("meta")
    index_path = emb_cfg.get("index")
    if not os.path.exists(index_path):
        raise HTTPException(404, "Índice não encontrado.")
    
    index, meta = load_index(index_path, meta_path)
    
    # Buscar embedding da pergunta
    from src.embedder_providers import embed_query
    q_vec = embed_query(question, provider=provider)
    if not q_vec:
        return {"error": "Falha ao gerar embedding da pergunta."}
    
    q_vec = np.array([q_vec], dtype="float32")
    scores, indices = index.search(q_vec, 100)
    
    # Atualizar neurônios com scores
    activated_ids = set(indices[0])
    for neuron in brain["neurons"]:
        neuron["activated"] = False
        neuron["score"] = 0
    
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx < len(brain["neurons"]):
            brain["neurons"][idx]["score"] = float(score)
            brain["neurons"][idx]["activated"] = True
    
    # Filtrar só os top 100 ativados
    activated = [n for n in brain["neurons"] if n.get("activated")]
    activated.sort(key=lambda x: x["score"], reverse=True)
    top_100 = activated[:100]
    
    return {
        "question": question,
        "provider": provider,
        "centroid": brain["centroid"],
        "neurons": top_100,
        "meta": {
            "doc_id": doc_id,
            "dim": brain.get("dim_original"),
            "total_chunks": brain.get("chunk_count")
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PERGUNTAS (RAG Principal)
# ═══════════════════════════════════════════════════════════════════════════════

class Question(BaseModel):
    question:           str
    report:             str = "raf"
    embedding_provider: str = "gemini"   # qual índice usar para busca
    llm_provider:       str = "groq"     # qual LLM gerar resposta
    user_keys:          dict = {}        # {groq: '...', gemini: '...'}

@app.post("/ask")
def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(400, "Pergunta vazia.")
    if q.report not in DOCUMENTS:
        raise HTTPException(400, f"Relatório '{q.report}' inválido.")

    return answer(
        question=q.question,
        report_key=q.report,
        embedding_provider=q.embedding_provider,
        llm_provider=q.llm_provider,
        user_keys=q.user_keys
    )


class CrossQuestion(BaseModel):
    question:           str
    embedding_provider: str = "gemini"
    llm_provider:       str = "groq"
    user_keys:          dict = {}

@app.post("/ask_cross")
def ask_cross(q: CrossQuestion):
    """Busca transversal em todos os documentos indexados."""
    if not q.question.strip():
        raise HTTPException(400, "Pergunta vazia.")

    from src.qa import get_query_vector, format_raw_chunks

    # Embedding da query (usa user keys se presentes)
    query_vec = get_query_vector(q.question, q.embedding_provider, user_keys=q.user_keys)
    if not query_vec:
        return {"answer": "Falha ao gerar embedding da pergunta.", "sources": [], "mode": "error"}

    # Busca em todos os docs
    all_sources = []
    for doc_key, doc_cfg in DOCUMENTS.items():
        emb_cfg = doc_cfg.get("embeddings", {}).get(q.embedding_provider) or \
                  doc_cfg.get("embeddings", {}).get("gemini", {})
        idx_path = emb_cfg.get("index", "")
        m_path   = emb_cfg.get("meta", "")

        if os.path.exists(idx_path) and os.path.exists(m_path):
            index = faiss.read_index(idx_path)
            with open(m_path, encoding="utf-8") as f:
                meta = json.load(f)
            vec = np.array([query_vec], dtype="float32")
            scores, indices = index.search(vec, 5)
            for score, i in zip(scores[0], indices[0]):
                if i < len(meta):
                    chunk = meta[i].copy()
                    chunk.update({"score": float(score), "doc_key": doc_key, "doc_short": doc_cfg["short"]})
                    all_sources.append(chunk)

    all_sources.sort(key=lambda x: x["score"])
    top = all_sources[:8]

    if not top:
        return {"answer": "Nenhuma fonte encontrada.", "sources": [], "mode": "error"}

    if q.llm_provider == "raw_chunks":
        return format_raw_chunks(top)

    context = "\n\n".join([f"[{s['doc_short']}, p.{s['page']}] {s['content']}" for s in top])

# Geração: Groq → Gemini → Jina → Big Pickle → raw
    from src.qa import generate_groq, generate_gemini, generate_jina, generate_bigpickle, is_provider_ok, set_quota_cooldown, OPENCODE_API_KEY
    
    prompt_role = "assistente especializado em relatórios científicos do MapBiomas"

    if q.llm_provider == "groq" and (GROQ_API_KEY or q.user_keys.get("groq")):
        try:
            text = generate_groq(q.question, context, prompt_role, override_key=q.user_keys.get("groq"))
            return {"answer": text, "sources": top, "mode": "groq"}
        except Exception as e:
            if not q.user_keys.get("groq") and ("429" in str(e).upper() or "RATE" in str(e).upper()):
                set_quota_cooldown("groq", 60)
            print(f"  [Cross/Groq] {e}")

    if is_provider_ok("gemini") or q.user_keys.get("gemini"):
        try:
            text = generate_gemini(q.question, context, prompt_role, override_key=q.user_keys.get("gemini"))
            return {"answer": text, "sources": top, "mode": "gemini"}
        except Exception as e:
            print(f"  [Cross/Gemini] {e}")

    # Tentativa 3: Jina DeepSearch
    if is_provider_ok("jina"):
        try:
            text = generate_jina(q.question, context, prompt_role)
            return {"answer": text, "sources": top, "mode": "jina"}
        except Exception as e:
            print(f"  [Cross/Jina] {e}")

    # Tentativa 4: Big Pickle (OpenCode Zen)
    if OPENCODE_API_KEY or q.user_keys.get("bigpickle"):
        try:
            text = generate_bigpickle(q.question, context, prompt_role, override_key=q.user_keys.get("bigpickle"))
            return {"answer": text, "sources": top, "mode": "bigpickle"}
        except Exception as e:
            print(f"  [Cross/BigPickle] {e}")

    return format_raw_chunks(top)


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY — só ativo em DEV_MODE
# ═══════════════════════════════════════════════════════════════════════════════

def _require_dev():
    if not DEV_MODE:
        raise HTTPException(403, "Endpoint disponível apenas em modo desenvolvedor (DEV_MODE=true).")

class EmbedRequest(BaseModel):
    report_id: str
    provider:  str = "gemini"
    user_keys: dict = {}

@app.post("/factory/delete_asset")
def delete_asset(req: dict):
    """
    Remove assets do Hub.
    req: { type: 'app'|'embedding'|'chunks'|'pdf', doc_id: str, provider: str (opcional) }
    """
    _require_dev()
    t = req.get("type")
    doc_id = req.get("doc_id")
    provider = req.get("provider")

    import shutil

    if t == "app":
        app_path = os.path.join("apps", doc_id)
        if os.path.exists(app_path):
            shutil.rmtree(app_path)
            return {"status": "ok", "message": f"App '{doc_id}' removido."}

    elif t == "embedding":
        if not provider: return {"status": "error", "message": "Provider necessário."}
        provider_cfg = EMBEDDING_PROVIDERS.get(provider, {})
        model_id = provider_cfg.get("model_id", provider).replace("/", "-")
        emb_dir  = os.path.join("docs", doc_id, "assets", "embeddings", model_id)
        
        # ── Limpeza agressiva para Windows (liberar lock) ──
        import gc
        engine_key = f"{doc_id}:{provider}"
        from src.qa import _engines
        if engine_key in _engines:
            print(f"  [Factory] Descarregando engine {engine_key} para exclusão...")
            # Limpa referências internas
            engine_data = _engines.pop(engine_key)
            if "index" in engine_data:
                del engine_data["index"] # Remove objeto FAISS
            del engine_data
        
        gc.collect() # Força liberação de memória e handles
        import time
        time.sleep(0.5) # Pequeno fôlego para o SO liberar o arquivo

        if os.path.exists(emb_dir):
            try:
                shutil.rmtree(emb_dir)
                return {"status": "ok", "message": f"Embedding '{provider}' de '{doc_id}' removido."}
            except Exception as e:
                # Se ainda falhar, tenta apenas o que for possível
                return {"status": "error", "message": f"Erro de permissão: {e}. Tente fechar o PDF ou reiniciar o servidor."}

    elif t == "chunks":
        chunks_path = os.path.join("docs", doc_id, "assets", "chunks")
        if os.path.exists(chunks_path):
            shutil.rmtree(chunks_path)
            return {"status": "ok", "message": f"Chunks de '{doc_id}' removidos."}

    elif t == "pdf":
        doc_dir = os.path.join("docs", doc_id)
        if os.path.exists(doc_dir):
            shutil.rmtree(doc_dir)
            return {"status": "ok", "message": f"Documento '{doc_id}' completamente removido (PDF + Assets)."}

    raise HTTPException(404, f"Ativo '{t}' não encontrado ou não deletável.")


class AppCreateRequest(BaseModel):
    doc_id: str  # Template base
    app_id: str  # Slug
    name:   str  # Titulo amigavel
    docs:   list[str] # Lista de docs no contexto
    user_keys: dict = {}

@app.post("/factory/embed")
async def factory_embed(req: EmbedRequest):
    """Gera embeddings para um dock específico usando o provider escolhido."""
    _require_dev(req.user_keys)
    
    report_id = req.report_id
    cfg = DOCUMENTS.get(report_id)
    if not cfg:
        raise HTTPException(404, f"Documento '{report_id}' não registrado.")

    chunks_path = cfg.get("chunks", "")
    if not os.path.exists(chunks_path):
        raise HTTPException(400, "Chunks não encontrados. Execute o chunking primeiro.")

    job_id = str(uuid.uuid4())[:8]

    def _do_embed(jid, doc_id, provider, chunks_p, user_keys):
        _jobs[jid]["message"] = f"Carregando chunks de {doc_id}..."
        with open(chunks_p, encoding="utf-8") as f:
            chunks = json.load(f)

        _jobs[jid]["message"] = f"Gerando embeddings ({provider})..."
        _jobs[jid]["progress"] = 0
        from src.embedder_providers import embed_batch
        texts = [c["content"] for c in chunks]
        
        def _prog_cb(cur, total):
            pct = int((cur / total) * 100)
            _jobs[jid]["progress"] = pct
            _jobs[jid]["message"] = f"Progresso {provider}: {cur}/{total} ({pct}%)"
            
        task_name = "retrieval.passage" if provider == "jina" else None
        vecs  = embed_batch(texts, provider=provider, on_progress=_prog_cb, task=task_name, user_keys=user_keys)

        if not vecs:
            raise RuntimeError("Nenhum vetor gerado.")

        # Salvar índice
        provider_cfg = EMBEDDING_PROVIDERS.get(provider, {})
        model_id = provider_cfg.get("model_id", provider).replace("/", "-")
        out_dir  = os.path.join("docs", doc_id, "assets", "embeddings", model_id)
        os.makedirs(out_dir, exist_ok=True)

        arr   = np.array(vecs, dtype="float32")
        index = faiss.IndexFlatL2(arr.shape[1])
        index.add(arr)
        faiss.write_index(index, os.path.join(out_dir, "faiss.index"))

        meta = chunks
        with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)

# Gerar brain.json (visualização 3D)
        brain_path = os.path.join(out_dir, "brain.json")
        try:
            from sklearn.decomposition import PCA
            import datetime
            
            arr = np.array(vecs, dtype="float32")
            
            # PCA para 3 dimensões
            n_components = min(3, len(vecs))
            pca = PCA(n_components=n_components)
            coords_3d = pca.fit_transform(arr).tolist()
            
            # Centróide
            centroid = [float(np.mean(coords_3d[:, i])) for i in range(n_components)]
            
            # Neurônios (todos os chunks)
            neurons = []
            for i, chunk in enumerate(chunks):
                neurons.append({
                    "id": i,
                    "page": chunk.get("page", 0),
                    "content_preview": chunk.get("content", "")[:120].replace("\n", " "),
                    "coords_3d": list(coords_3d[i]) if i < len(coords_3d) else [0, 0, 0],
                    "activated": False,
                    "score": 0
                })
            
            brain_data = {
                "doc_id": doc_id,
                "provider": provider,
                "dim_original": arr.shape[1],
                "chunk_count": len(chunks),
                "created_at": datetime.datetime.now().isoformat(),
                "centroid": centroid,
                "pca_variance": pca.explained_variance_ratio_.tolist()[:3],
                "neurons": neurons
            }
            
            with open(brain_path, "w", encoding="utf-8") as f:
                json.dump(brain_data, f, ensure_ascii=False)
            
            print(f"  [Brain] Cérebro gerado: {brain_path}")
        except Exception as e:
            print(f"  [!] Erro ao gerar cérebro: {e}")

        # Registrar no live memory
        if "embeddings" not in DOCUMENTS[doc_id]:
            DOCUMENTS[doc_id]["embeddings"] = {}
            
        DOCUMENTS[doc_id]["embeddings"][provider] = {
            "index":    os.path.join(out_dir, "faiss.index"),
            "meta":     os.path.join(out_dir, "meta.json"),
            "brain":   brain_path,
            "model_id": provider_cfg.get("model_id", provider),
            "dims":     provider_cfg.get("dims", 768)
        }

        _jobs[jid]["status"]   = "done"
        _jobs[jid]["progress"] = 100
        _jobs[jid]["message"]  = f"Concluído! {len(vecs)} vetores indexados ({provider}). Cérebro gerado."

    t = threading.Thread(target=_run_job, args=(job_id, _do_embed, req.report_id, req.provider, chunks_path, req.user_keys), daemon=True)
    t.start()

    return {"job_id": job_id, "status": "running", "message": "Job iniciado."}

@app.get("/factory/status/{job_id}")
def factory_status(job_id: str):
    """Polling do status de um job de embedding."""
    # Status é público para quem tem ID do job
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado.")
    return job

@app.post("/factory/upload")
async def upload_doc(
    file: UploadFile = File(...), 
    report_id: str = Form(...),
    user_keys: str = Form("{}")
):
    try:
        uk = json.loads(user_keys)
    except:
        uk = {}
        
    _require_dev(uk)
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Apenas arquivos .pdf são aceitos.")

    dest_dir = os.path.join("docs", report_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    # Registra no runtime (não persiste no config.py ainda — fase futura)
    DOCUMENTS[report_id] = {
        "name":        report_id,
        "short":       report_id.upper(),
        "emoji":       "📄",
        "color":       "#6c757d",
        "pdf":         dest_path,
        "chunks":      os.path.join(dest_dir, "assets", "chunks", "chunks.json"),
        "embeddings":  {},
        "prompt_role": f"assistente especializado em {report_id}",
    }

    return {
        "ok":      True,
        "doc_id":  report_id,
        "pdf":     dest_path,
        "message": f"PDF '{file.filename}' carregado com sucesso.",
    }

@app.post("/factory/create_app")
def create_app(req: AppCreateRequest):
    """Gera o app. Se DEV_MODE, salva no disco. Se não, guarda apenas na memória."""
    _require_dev(req.user_keys)
    # Pegamos info do doc principal para o template
    base_cfg = DOCUMENTS.get(req.doc_id)
    if not base_cfg: 
        raise HTTPException(404, "Documento base não encontrado.")

    # 1. Carregar Template (sempre do RAF que é o nosso melhor)
    template_path = os.path.join(ui_path, "apps", "raf", "index.html")
    if not os.path.exists(template_path):
        raise HTTPException(500, "Template base (RAF) não encontrado.")
        
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # 2. Customizações
    html = html.replace("Relatório Anual do Fogo", req.name)
    html = html.replace("RAF 2024", req.app_id.upper())
    html = html.replace("report: 'raf'", f"report: '{req.doc_id}'") # Alvo de busca
    html = html.replace("#E8503A", base_cfg.get("color", "#6c757d"))
    html = html.replace("🔥", base_cfg.get("emoji", "📄"))
    
    # Lógica de múltiplos documentos (se o usuário selecionar vários)
    if len(req.docs) > 1:
        import json
        html = html.replace("report: 'raf'", f"docs: {json.dumps(req.docs)}")

    # 3. Entrega (Disco vs Memória)
    if DEV_MODE:
        app_dir = os.path.join(ui_path, "apps", req.app_id)
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [Factory] App '{req.app_id}' persistido no disco (DEV_MODE).")

    # Registrar no Global Registro (volátil para todos, mas persistente no disco se DEV)
    DOCUMENTS[req.app_id] = {
        "name":          req.name,
        "short":         req.app_id.upper(),
        "emoji":         base_cfg.get("emoji", "📄"),
        "color":         base_cfg.get("color", "#6c757d"),
        "pdf":           base_cfg.get("pdf", ""), 
        "is_custom":     True,
        "docs":          req.docs,
        "html_content":  None if DEV_MODE else html # Só guarda HTML em memória se não salvou no disco
    }
        
    return {"ok": True, "app_url": f"/{req.app_id}", "is_persistent": DEV_MODE}


# ═══════════════════════════════════════════════════════════════════════════════
# DEV MODE E CHAVES DE API (Apenas em modo desenvolvedor)
# ═══════════════════════════════════════════════════════════════════════════════

class DevModeRequest(BaseModel):
    enabled: bool

@app.post("/dev-mode")
def toggle_dev_mode(req: DevModeRequest):
    """Alterna o modo desenvolvedor entre true/false. Este endpoint é público."""
    success = set_dev_mode(req.enabled)
    return {"ok": success, "dev_mode": DEV_MODE}

class SaveKeyRequest(BaseModel):
    key_name: str
    key_value: str

@app.post("/dev-mode/save-key")
def save_api_key(req: SaveKeyRequest):
    """Salva uma chave de API no arquivo .env local."""
    _require_dev()
    success = _save_env_key(req.key_name, req.key_value)
    return {"ok": success, "key": req.key_name}

# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD DE ARQUIVOS DOS APPS
# ═══════════════════════════════════════════════════════════════════════════════

import zipfile
import io
from fastapi.responses import StreamingResponse

@app.get("/download/{doc_id}")
def download_app_files(doc_id: str):
    """Baixa todos os arquivos de um app como .zip."""
    cfg = DOCUMENTS.get(doc_id)
    if not cfg:
        raise HTTPException(404, f"App '{doc_id}' não encontrado.")
    
    if not os.path.exists("docs"):
        raise HTTPException(404, "Diretório de documentos não encontrado.")
    
    doc_dir = os.path.join("docs", doc_id)
    if not os.path.exists(doc_dir):
        raise HTTPException(404, f"Diretório '{doc_id}' não encontrado.")
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(doc_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, doc_dir)
                arcname = f"{doc_id}-{rel_path.replace(os.sep, '-')}"
                try:
                    with open(file_path, 'rb') as f:
                        zf.writestr(arcname, f.read())
                except Exception as e:
                    print(f"[!] Erro ao adicionar {file_path}: {e}")
    
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={doc_id}.zip"}
    )

@app.get("/download_cross")
def download_cross_all():
    """Baixa todos os arquivos de todos os docs indexados (para busca transversal)."""
    if not os.path.exists("docs"):
        raise HTTPException(404, "Diretório de documentos não encontrado.")
    
    buffer = io.BytesIO()
    doc_count = 0
    file_count = 0
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc_id, doc_cfg in DOCUMENTS.items():
            doc_dir = os.path.join("docs", doc_id)
            if not os.path.exists(doc_dir):
                continue
            
            has_files = False
            for root, dirs, files in os.walk(doc_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, doc_dir)
                    arcname = f"{doc_id}-{rel_path.replace(os.sep, '-')}"
                    try:
                        with open(file_path, 'rb') as f:
                            zf.writestr(arcname, f.read())
                        file_count += 1
                        has_files = True
                    except Exception as e:
                        print(f"[!] Erro ao adicionar {file_path}: {e}")
            
            if has_files:
                doc_count += 1
    
    if file_count == 0:
        raise HTTPException(404, "Nenhum arquivo encontrado.")
    
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=cross-{doc_count}docs.zip"}
    )

@app.get("/download/{doc_id}/file/{file_name}")
def download_single_file(doc_id: str, file_name: str):
    """Baixa um arquivo específico do app."""
    cfg = DOCUMENTS.get(doc_id)
    if not cfg:
        raise HTTPException(404, f"App '{doc_id}' não encontrado.")
    
    doc_dir = os.path.join("docs", doc_id)
    file_path = os.path.join(doc_dir, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(404, f"Arquivo '{file_name}' não encontrado em '{doc_id}'.")
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/pdf" if file_name.endswith(".pdf") else "application/octet-stream"
    )

@app.get("/files/{doc_id}")
def list_app_files(doc_id: str):
    """Lista todos os arquivos disponíveis para download de um app."""
    cfg = DOCUMENTS.get(doc_id)
    if not cfg:
        raise HTTPException(404, f"App '{doc_id}' não encontrado.")
    
    doc_dir = os.path.join("docs", doc_id)
    if not os.path.exists(doc_dir):
        return {"files": [], "doc_id": doc_id}
    
    files = []
    for root, dirs, filenames in os.walk(doc_dir):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, doc_dir)
            size = os.path.getsize(full_path)
            files.append({
                "name": filename,
                "path": rel_path,
                "size": size,
                "type": "pdf" if filename.endswith(".pdf") else "other"
            })
    
    return {"files": files, "doc_id": doc_id}


# ═══════════════════════════════════════════════════════════════════════════════
# SPA CATCH-ALL (Mantenha sempre no final)
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi.responses import HTMLResponse

@app.get("/{app_id}")
def serve_any_app(app_id: str):
    """Serve um app seja do disco (DEV) ou da memória (USER)."""
    # 1. Se estiver na memória (App virtual gerado em runtime)
    if app_id in DOCUMENTS and "html_content" in DOCUMENTS[app_id] and DOCUMENTS[app_id]["html_content"]:
        return HTMLResponse(content=DOCUMENTS[app_id]["html_content"])
    
    # 2. Se estiver no disco (Apps fixos ou gerados em DEV_MODE)
    path = os.path.join(ui_path, "apps", app_id, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    
    # 3. Fallback para Vitrine (faz as rotas funcionarem no SPA)
    return FileResponse(os.path.join(ui_path, "apps", "vitrine", "index.html"))

