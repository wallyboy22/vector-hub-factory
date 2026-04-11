import os
import sys
import numpy as np
import faiss
import json
from google import genai
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Adicionar ROOT ao sys.path para importar config.py corretamente
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from config import DOCUMENTS, LLM_MODELS, GOOGLE_API_KEY, EMBEDDING_MODEL
from src.qa import answer, _clients

# Inicializar Cliente Gemini (SDK v1)
client = genai.Client(api_key=GOOGLE_API_KEY)

def embed_query(query: str) -> list[float]:
    """Gera embedding para uma query de busca."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config={"task_type": "RETRIEVAL_QUERY"}
    )
    return list(response.embeddings[0].values)

app = FastAPI(title="Vector Hub Factory", version="3.1")

# Servir a interface web
ui_path = os.path.join(os.path.dirname(__file__), "..", "ui")
app.mount("/ui", StaticFiles(directory=ui_path), name="ui")

@app.get("/")
def root():
    # A Vitrine agora é a Homepage principal
    return FileResponse(os.path.join(ui_path, "vitrine", "index.html"))

@app.get("/reports")
def list_reports():
    """Retorna metadados de todos os relatórios disponíveis."""
    return {
        key: {
            "name": cfg["name"],
            "short": cfg["short"],
            "emoji": cfg["emoji"],
            "color": cfg["color"],
            "has_index": os.path.exists(cfg.get("embeddings", {}).get("gemini", {}).get("index", "")),
        }
        for key, cfg in DOCUMENTS.items()
    }

@app.get("/models")
def list_models():
    return list(LLM_MODELS.keys())

@app.get("/pdf/{report}")
def get_pdf(report: str):
    cfg = DOCUMENTS.get(report)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Relatório '{report}' não encontrado.")
    if not os.path.exists(cfg["pdf"]):
        raise HTTPException(status_code=404, detail="PDF não encontrado no servidor.")
    return FileResponse(cfg["pdf"], media_type="application/pdf")

@app.get("/logo/{report}")
def get_logo(report: str):
    cfg = DOCUMENTS.get(report)
    if not cfg or "logo" not in cfg:
        # Fallback para logo padrão se não existir no config
        raise HTTPException(status_code=404, detail=f"Logo de '{report}' não configurada.")
    
    logo_path = cfg["logo"]
    if not os.path.exists(logo_path):
        raise HTTPException(status_code=404, detail=f"Arquivo de logo não encontrado em: {logo_path}")
    
    return FileResponse(logo_path)

@app.get("/assets/{filename}")
def serve_asset(filename: str):
    """Serve arquivos da pasta assets ou subpasta logos."""
    # 1. Tentar pasta raiz de assets
    asset_path = os.path.join(ui_path, "assets", filename)
    if os.path.exists(asset_path):
        return FileResponse(asset_path)
    
    # 2. Tentar subpasta logos
    logo_path = os.path.join(ui_path, "assets", "logos", filename)
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
        
    raise HTTPException(status_code=404, detail="Asset não encontrado.")

class Question(BaseModel):
    question: str
    report: str = "raf"
    model: str = "flash"

@app.post("/ask")
def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia")
    if q.report not in DOCUMENTS:
        raise HTTPException(status_code=400, detail=f"Relatório '{q.report}' inválido.")
    
    return answer(q.question, q.report, q.model)

# --- Rotas Adicionais para Apps Específicos ---

@app.get("/cross")
@app.get("/cross/")
def cross_page():
    return FileResponse(os.path.join(ui_path, "cross", "index.html"))

@app.get("/hub")
@app.get("/hub/")
def hub_page():
    return FileResponse(os.path.join(ui_path, "vitrine", "index.html"))

@app.get("/chatbot-raf")
@app.get("/chatbot-raf/")
def chatbot_raf_page():
    return FileResponse(os.path.join(ui_path, "chatbot-raf", "index.html"))

@app.get("/chatbot-rad")
@app.get("/chatbot-rad/")
def chatbot_rad_page():
    return FileResponse(os.path.join(ui_path, "chatbot-rad", "index.html"))

@app.get("/multi")
@app.get("/multi/")
def multi_page():
    # UI/index.html original era o multi-chat
    return FileResponse(os.path.join(ui_path, "index.html"))

# --- Busca Transversal (All Docs) ---

class CrossQuestion(BaseModel):
    question: str
    model: str = "flash"

@app.post("/ask_cross")
def ask_cross(q: CrossQuestion):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Pergunta vazia")

    retries = len(_clients)
    for i in range(retries):
        client = _clients[i % len(_clients)]
        try:
            # 1. Gerar embedding da pergunta
            res_emb = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=q.question,
                config={"task_type": "RETRIEVAL_QUERY"}
            )
            query_vec = list(res_emb.embeddings[0].values)

            # 2. Buscar em todos os documentos
            all_sources = []
            for doc_key, doc_cfg in DOCUMENTS.items():
                emb_cfg = doc_cfg.get("embeddings", {}).get("gemini", {})
                idx_path = emb_cfg.get("index", "")
                m_path = emb_cfg.get("meta", "")
                
                if os.path.exists(idx_path) and os.path.exists(m_path):
                    index = faiss.read_index(idx_path)
                    with open(m_path, encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    vec = np.array([query_vec], dtype="float32")
                    scores, indices = index.search(vec, 5)
                    
                    for score, idx in zip(scores[0], indices[0]):
                        if idx < len(meta):
                            chunk = meta[idx].copy()
                            chunk["score"] = float(score)
                            chunk["doc_key"] = doc_key
                            chunk["doc_short"] = doc_cfg["short"]
                            all_sources.append(chunk)

            # 3. Re-ranquear
            all_sources.sort(key=lambda x: x["score"])
            top_sources = all_sources[:8]

            # 4. Montar Contexto
            context = "\n\n".join([f"[{s['doc_short']}, p.{s['page']}] {s['content']}" for s in top_sources])
            
            # 5. Gerar Resposta
            model_name = LLM_MODELS.get(q.model, LLM_MODELS["flash"])
            prompt = f"""Você é um assistente especializado em relatórios científicos.
Use as fontes abaixo para responder. CITE A ORIGEM SEMPRE como [RAF, p.X] ou [RAD, p.X].

CONTEXTO:
{context}

PERGUNTA: {q.question}
"""
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"temperature": 0.1}
            )
            return {
                "answer": response.text,
                "sources": top_sources,
                "model": q.model
            }
        except Exception as e:
            err_str = str(e).upper()
            if ("429" in err_str or "QUOTA" in err_str or "EXHAUSTED" in err_str) and i < retries - 1:
                print(f"  [QA-CROSS] Chave {i+1} esgotada. Tentando Chave Reserva (ALT)... ⚡")
                continue
                
            if "429" in err_str or "QUOTA" in err_str or "EXHAUSTED" in err_str or "RESOURCE" in err_str:
                return {
                    "answer": "☕ **Ufa! Todas as nossas IAs estão sobrecarregadas por hoje.**\n\nIsso acontece quando atingimos o limite diário da conta gratuita do Google nas duas chaves disponíveis.\n\n**O que fazer?**\nAguarde cerca de 15 minutos e tente novamente.",
                    "sources": [],
                    "model": q.model
                }
            
            if i == retries - 1:
                raise HTTPException(status_code=500, detail=str(e))

# --- Busca Simples (sem LLM para testes rápidos) ---

@app.post("/search")
def search_doc(q: Question):
    client = _clients[0]
    res_emb = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=q.question,
        config={"task_type": "RETRIEVAL_QUERY"}
    )
    query_vec = list(res_emb.embeddings[0].values)
    doc_cfg = DOCUMENTS.get(q.report)
    if not doc_cfg: return {"answer": "Erro", "sources": []}
    
    emb_cfg = doc_cfg["embeddings"]["gemini"]
    index = faiss.read_index(emb_cfg["index"])
    with open(emb_cfg["meta"], encoding='utf-8') as f:
        meta = json.load(f)
        
    vec = np.array([query_vec], dtype="float32")
    scores, indices = index.search(vec, 5)
    
    sources = [meta[i] for i in indices[0] if i < len(meta)]
    
    # Gerar resposta rápida
    context = "\n".join([f"[p.{s['page']}] {s['content']}" for s in sources[:3]])
    prompt = f"Resumo curto baseado no contexto:\n{context}\n\nPergunta: {q.question}"
    
    response = client.models.generate_content(model=LLM_MODELS["flash"], contents=prompt)
    
    return {
        "answer": response.text,
        "sources": [{"page": s["page"]} for s in sources]
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": "3.1"}
