import numpy as np
import time
import os
from google import genai
from config import TOP_K, GOOGLE_API_KEY, GOOGLE_API_KEY_ALT, EMBEDDING_MODEL, DOCUMENTS, LLM_MODELS
from src.vectorstore import load_index

# Gerenciador de Clientes (Chave Principal e Reserva)
_clients = [genai.Client(api_key=GOOGLE_API_KEY)]
# Só adiciona a segunda chave se ela for real e diferente da padrão
if GOOGLE_API_KEY_ALT and len(GOOGLE_API_KEY_ALT) > 20 and "SEU" not in GOOGLE_API_KEY_ALT:
    _clients.append(genai.Client(api_key=GOOGLE_API_KEY_ALT))
    print(f"  [QA] Sistema de Chave Dupla Ativado! (2 chaves prontas)")
else:
    print(f"  [QA] Operando com Chave Unica (1 chave pronta)")

# Pré-carrega todos os índices disponíveis
_engines = {}
for key, cfg in DOCUMENTS.items():
    index_path = cfg.get("embeddings", {}).get("gemini", {}).get("index", "")
    meta_path = cfg.get("embeddings", {}).get("gemini", {}).get("meta", "")
    if os.path.exists(index_path):
        try:
            idx, meta = load_index(index_path, meta_path)
            _engines[key] = {"index": idx, "metadata": meta, "config": cfg}
            print(f"  [QA] Motor '{cfg['short']}' carregado.")
        except Exception as e:
            print(f"  [QA] Falha ao carregar '{cfg['short']}': {e}")

def search(query: str, report_key: str = "raf", client_index: int = 0) -> list[dict]:
    engine = _engines.get(report_key)
    if not engine:
        return []
    
    # Seleciona o cliente (principal ou alt)
    client = _clients[client_index if client_index < len(_clients) else 0]
    
    try:
        resp = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config={"task_type": "RETRIEVAL_QUERY"}
        )
        vec_list = list(resp.embeddings[0].values)
        vec = np.array([vec_list], dtype="float32")
        
        distances, indices = engine["index"].search(vec, TOP_K)
        return [engine["metadata"][i] for i in indices[0] if i < len(engine["metadata"])]
    except Exception as e:
        print(f"Erro na busca [{report_key}]: {e}")
        return []

def answer(question: str, report_key: str = "raf", model_key: str = "flash", retries: int = len(_clients)) -> dict:
    if report_key not in _engines:
        return {"answer": f"O relatório '{report_key}' ainda não foi indexado.", "sources": []}
    
    target_model = LLM_MODELS.get(model_key, LLM_MODELS["flash"])
    
    # Roda as tentativas alternando entre as chaves se necessário
    for i in range(retries):
        client = _clients[i % len(_clients)]
        try:
            chunks = search(question, report_key, client_index=(i % len(_clients)))
            if not chunks:
                return {"answer": "Não encontrei informações no documento para responder.", "sources": []}
                
            context = ""
            for c in chunks:
                context += f"\n[Pág {c['page']}]\n{c['content']}\n"
            
            cfg = DOCUMENTS.get(report_key, DOCUMENTS["raf"])
            prompt = f"Você é um {cfg['prompt_role']}.\nResponda APENAS com base no contexto abaixo.\nCITE PÁGINA.\n\nCONTEXTO:\n{context}\n\nPERGUNTA: {question}\n\nRESPOSTA (Português):"
            
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config={"temperature": 0.1}
            )
            return {
                "answer": response.text,
                "sources": [{"page": c["page"], "chunk_id": c["chunk_id"]} for c in chunks]
            }
            
        except Exception as e:
            err_str = f"{e}".upper()
            
            # Se for erro de COTA (429) e tivermos outra chave, tenta a próxima chave sem avisar erro ainda!
            if ("429" in err_str or "EXHAUSTED" in err_str) and i < retries - 1:
                print(f"  [QA] Chave {i+1} esgotada. Tentando Chave Reserva (ALT)... ⚡")
                continue 

            # Se TODAS as chaves falharem, aí sim avisamos
            if "429" in err_str or "EXHAUSTED" in err_str or "404" in err_str:
                return {
                    "answer": "☕ **Ufa! Todas as nossas IAs estão sobrecarregadas por hoje.**\n\nIsso acontece quando atingimos o limite diário da conta gratuita do Google nas duas chaves disponíveis.\n\n**O que fazer?**\nAguarde cerca de 15 minutos e tente novamente. Infelizmente, as cotas do plano gratuito são limitadas.",
                    "sources": [],
                    "error_type": "QUOTA"
                }
            
            if i < retries - 1:
                time.sleep(2)
                continue
                
            return {"answer": "O servidor da IA teve um problema técnico externo. Tente de novo em segundos!", "sources": []}
    
    return {"answer": "IA temporariamente lenta. Tente em instantes.", "sources": []}
