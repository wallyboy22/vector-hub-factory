"""
qa.py — Motor RAG Multi-Provedor
=================================
"""

import numpy as np
import time
import os
import json
from google import genai
import requests

from config import (
    TOP_K, GOOGLE_API_KEY, EMBEDDING_MODEL, DOCUMENTS,
    LLM_MODELS, ALL_API_KEYS, GROQ_API_KEY, ALL_GROQ_KEYS,
    EMBEDDING_PROVIDERS, JINA_API_KEY, HF_API_KEY, OPENCODE_API_KEY
)
from src.vectorstore import load_index
from src.telemetry import set_quota_cooldown, get_cooldown_remaining, is_provider_ok, log_usage

# ── Clientes Gemini (lazy) ────────────────────────────────────────────────────
_clients = {}

def get_client(index: int):
    if index not in _clients:
        try:
            _clients[index] = genai.Client(api_key=ALL_API_KEYS[index])
        except Exception as e:
            print(f"  [QA] Falha ao criar cliente Gemini {index}: {e}")
            return None
    return _clients.get(index)

# Controle de Chaves e Quotas
_key_blacklist = {}      # {idx_gemini: timestamp}
_groq_key_blacklist = {} # {idx_groq: timestamp}
_quota_cooldowns = {}    # {provider_id: timestamp}

def is_key_ok(index: int) -> bool:
    if index in _key_blacklist:
        if time.time() > _key_blacklist[index]:
            del _key_blacklist[index]
            return True
        return False
    return True

# ── Pré-carregamento dos Engines ──────────────────────────────────────────────
_engines = {}

def _load_engines():
    for key, cfg in DOCUMENTS.items():
        for provider_id, emb_cfg in cfg.get("embeddings", {}).items():
            index_path = emb_cfg.get("index", "")
            meta_path  = emb_cfg.get("meta", "")
            engine_key = f"{key}:{provider_id}"
            if os.path.exists(index_path):
                try:
                    idx, meta = load_index(index_path, meta_path)
                    _engines[engine_key] = {
                        "index":    idx,
                        "metadata": meta,
                        "config":   cfg,
                        "dims":     emb_cfg.get("dims", 768),
                    }
                    print(f"  [QA] Engine '{key}/{provider_id}' carregado.")
                except Exception as e:
                    print(f"  [QA] Falha ao carregar '{key}/{provider_id}': {e}")

_load_engines()

# ── Embedding da Query ────────────────────────────────────────────────────────
def _embed_query_gemini(query: str, override_key: str = None) -> list[float] | None:
    keys_to_try = [override_key] if override_key else ALL_API_KEYS
    for i, key in enumerate(keys_to_try):
        if not override_key and not is_key_ok(i): continue
        try:
            if override_key: client = genai.Client(api_key=key)
            else: client = get_client(i)
            if not client: continue
            resp = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=query,
                config={"task_type": "RETRIEVAL_QUERY"}
            )
            return list(resp.embeddings[0].values)
        except Exception as e:
            if not override_key and ("429" in str(e).upper() or "EXHAUSTED" in str(e).upper()):
                _key_blacklist[i] = time.time() + 3605
                continue
            if override_key: print(f"  [QA] Chave usuário falhou: {e}")
            return None
    return None

def _embed_query_provider(query: str, provider: str) -> list[float] | None:
    try:
        from src.embedder_providers import embed_query
        return embed_query(query, provider=provider)
    except Exception as e:
        print(f"  [QA] Embed via '{provider}' falhou: {e}")
        return None

def get_query_vector(query: str, embedding_provider: str = "gemini", user_keys: dict = {}) -> list[float] | None:
    gemini_key = user_keys.get("gemini")
    if embedding_provider == "gemini":
        return _embed_query_gemini(query, override_key=gemini_key)
    vec = _embed_query_provider(query, embedding_provider)
    if vec: return vec
    return _embed_query_gemini(query, override_key=gemini_key)

# ── Busca FAISS ───────────────────────────────────────────────────────────────
def search(query: str, report_key: str, embedding_provider: str = "gemini", user_keys: dict = {}) -> list[dict]:
    engine_key = f"{report_key}:{embedding_provider}"
    if engine_key not in _engines:
        cfg = DOCUMENTS.get(report_key)
        if cfg and "embeddings" in cfg and embedding_provider in cfg["embeddings"]:
            emb_cfg = cfg["embeddings"][embedding_provider]
            if os.path.exists(emb_cfg.get("index", "")):
                try:
                    idx, meta = load_index(emb_cfg["index"], emb_cfg["meta"])
                    _engines[engine_key] = {"index": idx, "metadata": meta}
                except: pass
    if engine_key not in _engines:
        gemini_engine_key = f"{report_key}:gemini"
        if gemini_engine_key in _engines: engine_key = gemini_engine_key
        else: return []
    engine = _engines[engine_key]
    vec = get_query_vector(query, embedding_provider, user_keys=user_keys)
    if not vec: return []
    try:
        q = np.array([vec], dtype="float32")
        distances, indices = engine["index"].search(q, TOP_K)
        return [engine["metadata"][i] for i in indices[0] if i < len(engine["metadata"])]
    except: return []

# ── Geradores ─────────────────────────────────────────────────────────────────
def generate_groq(question: str, context: str, prompt_role: str, override_key: str = None) -> str:
    from groq import Groq
    keys_to_try = [override_key] if override_key else ALL_GROQ_KEYS
    prompt = f"Você é um {prompt_role}.\nResponda APENAS com o contexto. CITE A PÁGINA.\n\nContexto:\n{context}\n\nPergunta: {question}"
    for i, key in enumerate(keys_to_try):
        if not override_key and _groq_key_blacklist.get(i, 0) > time.time(): continue
        try:
            client = Groq(api_key=key)
            completion = client.chat.completions.create(
                model=LLM_MODELS["groq"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=1024,
            )
            log_usage("groq", LLM_MODELS["groq"], completion.usage.total_tokens)
            return completion.choices[0].message.content
        except Exception as e:
            if not override_key and ("429" in str(e).upper() or "RATE" in str(e).upper()):
                _groq_key_blacklist[i] = time.time() + 600
                continue
            if override_key: raise e
            continue
    if not override_key: set_quota_cooldown("groq", 60)
    raise RuntimeError("Groq esgotada.")

def generate_gemini(question: str, context: str, prompt_role: str, override_key: str = None) -> str:
    target_model = LLM_MODELS["flash"]
    prompt = f"Você é um {prompt_role}.\nResponda APENAS com o contexto. CITE A PÁGINA.\n\nContexto:\n{context}\n\nPergunta: {question}"
    keys_to_try = [override_key] if override_key else ALL_API_KEYS
    for i, key in enumerate(keys_to_try):
        if not override_key and not is_key_ok(i): continue
        try:
            if override_key: client = genai.Client(api_key=key)
            else: client = get_client(i)
            if not client: continue
            resp = client.models.generate_content(model=target_model, contents=prompt, config={"temperature": 0.1})
            usage = getattr(resp, 'usage_metadata', None)
            if usage: log_usage("gemini", target_model, usage.total_token_count)
            return resp.text
        except Exception as e:
            if not override_key and ("429" in str(e).upper() or "EXHAUSTED" in str(e).upper()):
                _key_blacklist[i] = time.time() + 3605
                continue
            if override_key: raise e
            continue
    if not override_key: set_quota_cooldown("gemini", 3600)
    raise RuntimeError("Gemini esgotada.")

def generate_jina(question: str, context: str, prompt_role: str, override_key: str = None) -> str:
    key = override_key or JINA_API_KEY
    if not key: raise RuntimeError("Sem chave Jina.")
    url = "https://deepsearch.jina.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    prompt = f"Você é um {prompt_role}.\nResponda APENAS com o contexto. CITE A PÁGINA.\n\nContexto:\n{context}\n\nPergunta: {question}"
    data = {"model": "jina-deepsearch-v1", "messages": [{"role": "user", "content": prompt}], "stream": False}
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    log_usage("jina", "deepsearch", result.get("usage", {}).get("total_tokens", 0))
    return result["choices"][0]["message"]["content"]

def generate_bigpickle(question: str, context: str, prompt_role: str, override_key: str = None) -> str:
    key = override_key or OPENCODE_API_KEY
    if not key: raise RuntimeError("Sem chave OpenCode Zen.")
    url = "https://opencode.ai/zen/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    prompt = f"Você é um {prompt_role}.\nResponda APENAS com o contexto. CITE A PÁGINA.\n\nContexto:\n{context}\n\nPergunta: {question}"
    data = {"model": "big-pickle", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": 2048}
    resp = requests.post(url, headers=headers, json=data, timeout=120)
    if resp.status_code == 429:
        set_quota_cooldown("bigpickle", 300)
        raise RuntimeError("Big Pickle rate limited.")
    if resp.status_code == 401:
        raise RuntimeError("Chave OpenCode inválida.")
    resp.raise_for_status()
    result = resp.json()
    content = result["choices"][0]["message"]["content"]
    content = content.encode('utf-8', errors='replace').decode('utf-8')
    log_usage("bigpickle", "big-pickle", result.get("usage", {}).get("total_tokens", 0))
    return content

def answer(question: str, report_key: str = "raf", model_key: str = "flash", embedding_provider: str = "gemini", llm_provider: str = "groq", user_keys: dict = {}) -> dict:
    if report_key not in DOCUMENTS: return {"answer": "Erro doc.", "sources": [], "mode": "error"}
    chunks = search(question, report_key, embedding_provider, user_keys=user_keys)
    if not chunks: return {"answer": "Não encontrado.", "sources": [], "mode": "error"}
    context = "\n".join([f"[Pág {c.get('page','?')}] {c.get('content','')}" for c in chunks])
    prompt_role = DOCUMENTS[report_key].get("prompt_role", "especialista")
    if llm_provider == "raw_chunks":
        from src.qa_utils import format_raw_chunks # hypothetical split if needed, using existing for now
        return _format_raw_chunks_local(chunks)
    
    # Try Providers
    if llm_provider == "groq" and (GROQ_API_KEY or user_keys.get("groq")):
        try:
            return {"answer": generate_groq(question, context, prompt_role, user_keys.get("groq")), "sources": chunks, "mode": "groq"}
        except: pass
    if is_provider_ok("gemini") or user_keys.get("gemini"):
        try:
            return {"answer": generate_gemini(question, context, prompt_role, user_keys.get("gemini")), "sources": chunks, "mode": "gemini"}
        except: pass
    if JINA_API_KEY or user_keys.get("jina"):
        try:
            return {"answer": generate_jina(question, context, prompt_role, user_keys.get("jina")), "sources": chunks, "mode": "jina"}
        except: pass
    # Fallback: Big Pickle (OpenCode Zen)
    if OPENCODE_API_KEY or user_keys.get("bigpickle"):
        try:
            return {"answer": generate_bigpickle(question, context, prompt_role, user_keys.get("bigpickle")), "sources": chunks, "mode": "bigpickle"}
        except: pass
    return _format_raw_chunks_local(chunks)

def _format_raw_chunks_local(chunks):
    lines = ["⚠️ **IA local indisponível**\n"]
    for i, c in enumerate(chunks, 1):
        lines.append(f"\n**[{i}] Pág. {c.get('page')}**\n> {c.get('content')[:500]}")
    return {"answer": "\n".join(lines), "sources": chunks, "mode": "raw_chunks"}

def get_key_status():
    """Status de saúde de todas as chaves API - versão completa."""
    from config import (
        GROQ_API_KEY, JINA_API_KEY, GOOGLE_API_KEY, 
        HF_API_KEY, OPENCODE_API_KEY
    )
    
    status = []
    
    # Gemini keys (multiple keys support)
    for idx, key in enumerate(ALL_API_KEYS):
        off = _key_blacklist.get(idx, 0)
        rem = int(max(0, off - time.time()))
        has_key = bool(GOOGLE_API_KEY or os.getenv(f"GOOGLE_API_KEY_{idx}") or os.getenv(f"GOOGLE_API_KEY_ALT"))
        status.append({
            "provider": "gemini", 
            "key_index": idx,
            "has_key": has_key,
            "status": "BLOQUEADA" if rem > 0 else "DISPONÍVEL" if has_key else "SEM CHAVE",
            "remaining": rem
        })
    
    # Groq keys
    for i, key in enumerate(ALL_GROQ_KEYS):
        off = _groq_key_blacklist.get(i, 0)
        rem = int(max(0, off - time.time()))
        has_key = bool(GROQ_API_KEY or os.getenv(f"GROQ_API_KEY_{i}"))
        status.append({
            "provider": "groq", 
            "key_index": i,
            "has_key": has_key,
            "status": "BLOQUEADA" if rem > 0 else "DISPONÍVEL" if has_key else "SEM CHAVE",
            "remaining": rem
        })
    
    # Jina
    jina_rem = get_cooldown_remaining("jina")
    has_jina_key = bool(JINA_API_KEY)
    status.append({
        "provider": "jina",
        "key_index": 0,
        "has_key": has_jina_key,
        "status": "COTA ESGOTADA" if jina_rem > 0 else "DISPONÍVEL" if has_jina_key else "SEM CHAVE",
        "remaining": jina_rem
    })
    
    # HuggingFace
    status.append({
        "provider": "huggingface",
        "key_index": 0,
        "has_key": bool(HF_API_KEY),
        "status": "DISPONÍVEL" if HF_API_KEY else "SEM CHAVE",
        "remaining": 0
    })
    
    # OpenCode / Big Pickle
    status.append({
        "provider": "opencode (big-pickle)",
        "key_index": 0,
        "has_key": bool(OPENCODE_API_KEY),
        "status": "DISPONÍVEL" if OPENCODE_API_KEY else "SEM CHAVE",
        "remaining": 0
    })
    
    return status

def get_engine_registry():
    return {k.split(":")[0]: k.split(":")[1] for k in _engines.keys()}
