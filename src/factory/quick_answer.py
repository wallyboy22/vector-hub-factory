import os
import sys

root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root)

import numpy as np
import faiss
import json
from google import genai

from config import DOCUMENTS, LLM_MODELS, GOOGLE_API_KEY, EMBEDDING_MODEL, TOP_K


_clients = [genai.Client(api_key=GOOGLE_API_KEY)]
if GOOGLE_API_KEY_ALT := os.getenv("GOOGLE_API_KEY_ALT"):
    if len(GOOGLE_API_KEY_ALT) > 20 and "SEU" not in GOOGLE_API_KEY_ALT:
        _clients.append(genai.Client(api_key=GOOGLE_API_KEY_ALT))

_top_k = TOP_K
_idx = None
_meta = None


def _load_doc(doc_key: str):
    global _idx, _meta
    cfg = DOCUMENTS.get(doc_key)
    if not cfg:
        return False
    emb = cfg.get("embeddings", {}).get("gemini")
    if not emb or not os.path.exists(emb["index"]):
        return False
    _idx = faiss.read_index(emb["index"])
    with open(emb["meta"], encoding="utf-8") as f:
        _meta = json.load(f)
    return True


def search(query: str, doc_key: str = "raf", client_index: int = 0) -> list[dict]:
    global _idx, _meta
    if _idx is None:
        if not _load_doc(doc_key):
            return []
    client = _clients[client_index if client_index < len(_clients) else 0]
    try:
        resp = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config={"task_type": "RETRIEVAL_QUERY"}
        )
        vec = np.array([list(resp.embeddings[0].values)], dtype="float32")
        _, indices = _idx.search(vec, _top_k)
        return [_meta[i] for i in indices[0] if i < len(_meta)]
    except Exception as e:
        print(f"Erro na busca: {e}")
        return []


def answer(question: str, doc_key: str = "raf", model_key: str = "flash") -> dict:
    if not _load_doc(doc_key):
        return {"answer": f"Documento '{doc_key}' ainda nao indexado.", "sources": []}
    
    target_model = LLM_MODELS.get(model_key, LLM_MODELS["flash"])
    
    for i in range(len(_clients)):
        client = _clients[i]
        try:
            chunks = search(question, doc_key, client_index=i)
            if not chunks:
                return {"answer": "Nao encontrei informacoes no documento.", "sources": []}
            
            context = "\n".join([f"\n[Pag {c['page']}]\n{c['content']}\n" for c in chunks])
            
            cfg = DOCUMENTS.get(doc_key, DOCUMENTS["raf"])
            prompt = f"Voce e um {cfg['prompt_role']}.\nResponda APENAS com base no contexto abaixo.\nCITE PAGINA.\n\nCONTEXTO:\n{context}\n\nPERGUNTA: {question}\n\nRESPOSTA (Portugues):"
            
            resp = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config={"temperature": 0.1}
            )
            return {
                "answer": resp.text,
                "sources": [{"page": c["page"], "chunk_id": c["chunk_id"]} for c in chunks]
            }
        except Exception as e:
            err = str(e).upper()
            if ("429" in err or "EXHAUSTED" in err) and i < len(_clients) - 1:
                continue
            return {"answer": f"Erro: {e}", "sources": []}
    
    return {"answer": "IA temporariamente lenta. Tente novamente.", "sources": []}


if __name__ == "__main__":
    print("Modulo de resposta rapida carregado.")