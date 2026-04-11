import os
import sys
import numpy as np
import faiss
import json
from google import genai

# Adicionar ROOT ao path
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_path)

from config import DOCUMENTS, LLM_MODELS, GOOGLE_API_KEY, EMBEDDING_MODEL

print("--- DEBUG RAG (Clean) ---")

try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    test_query = "qual a area queimada"
    
    print(f"Embedding query: '{test_query}'...")
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=test_query,
        config={"task_type": "RETRIEVAL_QUERY"}
    )
    vec = list(response.embeddings[0].values)
    print(f"Embedding success. Dims: {len(vec)}")
    
    # Testar busca no primeiro documento
    doc_key = "raf"
    cfg = DOCUMENTS[doc_key]
    # Usar a estrutura aninhada correta do config.py
    emb_cfg = cfg["embeddings"]["gemini"]
    index_path = emb_cfg["index"]
    meta_path = emb_cfg["meta"]
    
    print(f"Searching index '{doc_key}'...")
    print(f"Index Path: {index_path}")
    
    if not os.path.exists(index_path):
        print(f"ERROR: Index not found at {index_path}")
    else:
        index = faiss.read_index(index_path)
        with open(meta_path, encoding='utf-8') as f:
            meta = json.load(f)
        
        query_vec = np.array([vec], dtype="float32")
        scores, indices = index.search(query_vec, 3)
        print(f"Search success. Top indices: {indices[0]}")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
