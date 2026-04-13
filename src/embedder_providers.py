"""
embedder_providers.py — Motor de Embeddings Multi-Provedor
==========================================================
Abstrai a geração de vetores via diferentes provedores:

  PROVEDOR             KEY ENV                  DIMS   ONLINE?
  ─────────────────────────────────────────────────────────
  gemini               GOOGLE_API_KEY           768    API
  jina                 JINA_API_KEY            1024   API
  huggingface          HUGGINFACE_API_KEY       384    API (opcional)
  local                (sem key)                384    LOCAL (sentence-transformers)

Uso:
  from src.embedder_providers import embed_query, PROVIDERS_INFO
  vec = embed_query("minha pergunta", provider="gemini")
"""

import os
import time
import json
import requests
import numpy as np

# ── Carregamento de chaves ────────────────���────────────────────────────────────

def _load_keys():
    from dotenv import load_dotenv
    root = os.path.join(os.path.dirname(__file__), "..")
    load_dotenv(os.path.join(root, ".env"))

_load_keys()

GOOGLE_KEY   = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY_0")
JINA_KEY    = os.getenv("JINA_API_KEY") or os.getenv("JINA_API_KEY_0")
HF_KEY     = os.getenv("HUGGINFACE_API_KEY") or os.getenv("HUGGINFACE_API_KEY_0") or os.getenv("HUGGINGFACE_API_KEY")


# ── Registry de provedores ────────────────────────────────────────────────────

PROVIDERS_INFO = {
    "gemini": {
        "name":    "Google Gemini",
        "model":   "models/gemini-embedding-001",
        "dims":    768,
        "type":    "api",
        "key_env": "GOOGLE_API_KEY",
        "available": bool(GOOGLE_KEY),
        "render_ok": True,
        "description": "Alta qualidade, cota gratuita generosa para embeddings",
    },
    "jina": {
        "name":    "Jina AI",
        "model":   "jina-embeddings-v3",
        "dims":    1024,
        "type":    "api",
        "key_env": "JINA_API_KEY",
        "available": bool(JINA_KEY),
        "render_ok": True,
        "description": "Multilingual, 1M tokens grátis, excelente para PT-BR",
    },
    "huggingface": {
        "name":    "HuggingFace API",
        "model":   "sentence-transformers/all-MiniLM-L6-v2",
        "dims":    384,
        "type":    "api",
        "key_env": "HUGGINFACE_API_KEY",
        "available": True,  # funciona sem key (rate limited)
        "render_ok": True,
        "description": "Gratuito com ou sem key (limitado sem token)",
    },
    "local": {
        "name":    "Local (sentence-transformers)",
        "model":   "all-MiniLM-L6-v2",
        "dims":    384,
        "type":    "local",
        "key_env": None,
        "available": True,  # verificado no import
        "render_ok": False,  # RAM insuficiente no Render free tier
        "description": "100% offline, sem API, sem limites de cota",
    },
}

# Verificar se sentence-transformers está instalável
_local_model = None
def _get_local_model():
    global _local_model
    if _local_model is not None:
        return _local_model
    try:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("  [Embedding] Modelo local carregado: all-MiniLM-L6-v2")
        return _local_model
    except Exception as e:
        print(f"  [Embedding] Modelo local indisponível: {e}")
        PROVIDERS_INFO["local"]["available"] = False
        return None


# ── Funções de Embedding por Provedor ─────────────────────────────────────────

def _embed_gemini(texts: list[str], task_type: str = "RETRIEVAL_QUERY", user_keys: dict = {}) -> list[list[float]]:
    """Gemini embedding via google-genai SDK."""
    from google import genai
    key = user_keys.get("gemini") or GOOGLE_KEY
    if not key: raise RuntimeError("Sem chave Gemini.")
    client = genai.Client(api_key=key)
    resp = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=texts,
        config={"task_type": task_type}
    )
    return [list(e.values) for e in resp.embeddings]


def _embed_jina(texts: list[str], task: str = "retrieval.query", user_keys: dict = {}) -> list[list[float]]:
    """Jina AI embeddings via REST API."""
    headers = {"Content-Type": "application/json"}
    key = user_keys.get("jina") or JINA_KEY
    if key:
        headers["Authorization"] = f"Bearer {key}"

    resp = requests.post(
        "https://api.jina.ai/v1/embeddings",
        headers=headers,
        json={"input": texts, "model": "jina-embeddings-v3", "task": task},
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


def _embed_huggingface(texts: list[str]) -> list[list[float]]:
    """HuggingFace Inference API — funciona com ou sem key."""
    url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    headers = {"Content-Type": "application/json"}
    if HF_KEY:
        headers["Authorization"] = f"Bearer {HF_KEY}"

    resp = requests.post(url, headers=headers, json={"inputs": texts}, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    # HF retorna [[float,...]] direto
    return result if isinstance(result[0], list) else [result]


def _embed_local(texts: list[str]) -> list[list[float]]:
    """sentence-transformers local — sem internet, sem key."""
    model = _get_local_model()
    if not model:
        raise RuntimeError("Modelo local não disponível")
    vecs = model.encode(texts, convert_to_numpy=True)
    return vecs.tolist()


# ── Função pública principal ──────────────────────────────────────────────────

def embed_query(text: str, provider: str = "gemini", user_keys: dict = {}) -> list[float] | None:
    """
    Gera embedding para UMA query (busca).
    Retorna None se falhar completamente.
    """
    results = embed_batch([text], provider=provider, user_keys=user_keys)
    return results[0] if results else None


def embed_batch(texts: list[str], provider: str = "gemini",
                batch_size: int = 32, on_progress: callable = None,
                task: str = None, user_keys: dict = {}) -> list[list[float]]:
    """
    Gera embeddings para uma lista de textos com suporte a batching.
    `task`: específico para alguns provedores (ex: Jina v3 'retrieval.passage' vs 'retrieval.query')
    """
    if provider not in PROVIDERS_INFO:
        raise ValueError(f"Provider '{provider}' desconhecido. Disponíveis: {list(PROVIDERS_INFO.keys())}")

    all_vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        for attempt in range(3):
            try:
                if provider == "gemini":
                    vecs = _embed_gemini(batch, user_keys=user_keys)
                elif provider == "jina":
                    kwargs = {"texts": batch, "user_keys": user_keys}
                    if task: kwargs["task"] = task
                    vecs = _embed_jina(**kwargs)
                elif provider == "huggingface":
                    vecs = _embed_huggingface(batch)
                elif provider == "local":
                    vecs = _embed_local(batch)
                else:
                    raise ValueError(f"Provider desconhecido: {provider}")

                all_vectors.extend(vecs)
                if on_progress:
                    on_progress(len(all_vectors), len(texts))
                break

            except Exception as e:
                err = str(e).upper()
                if "429" in err or "RATE" in err or "EXHAUSTED" in err:
                    wait = (attempt + 1) * 15
                    print(f"  [Embed/{provider}] Cota atingida. Aguardando {wait}s...")
                    from src.telemetry import set_quota_cooldown
                    if provider == "jina":
                        set_quota_cooldown("jina", 3600) # 1 hora para Jina se bater cota
                    time.sleep(wait)
                    continue
                print(f"  [Embed/{provider}] Erro: {e}")
                break

        # Pausa entre batches
        if i + batch_size < len(texts):
            time.sleep(1)

    return all_vectors


def get_providers_status() -> dict:
    """Retorna o status de todos os provedores para a API."""
    status = {}
    for key, info in PROVIDERS_INFO.items():
        status[key] = {
            "name":        info["name"],
            "model":       info["model"],
            "dims":        info["dims"],
            "available":   info["available"],
            "has_key":     bool(os.getenv(info["key_env"])) if info["key_env"] else None,
            "render_ok":   info["render_ok"],
            "description": info["description"],
        }
    return status
