import faiss
import numpy as np
import json
import os
from src.embedder import EMBEDDING_DIM

def build_and_save(embeddings: list[dict], index_path: str, meta_path: str):
    if not embeddings:
        print("Erro crítico: Nenhuma embedding foi gerada para este índice.")
        return
        
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    vectors = np.array([e["vector"] for e in embeddings], dtype="float32")
    
    if len(vectors.shape) < 2:
        print(f"Erro no formato dos vetores: {vectors.shape}")
        return
        
    n, d = vectors.shape
    index = faiss.IndexFlatL2(d)
    index.add(vectors)
    faiss.write_index(index, index_path)
    
    metadata = [e["metadata"] for e in embeddings]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)
    
    print(f"✓ Índice salvo com sucesso: {index.ntotal} vetores em {index_path}")

def load_index(index_path: str, meta_path: str):
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Arquivo do índice não encontrado ({index_path})")
    index = faiss.read_index(index_path)
    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)
    return index, metadata

if __name__ == "__main__":
    import argparse
    from src.embedder import embed_chunks
    from src.config import REPORTS
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="raf", choices=REPORTS.keys())
    args = parser.parse_args()
    
    cfg = REPORTS[args.report]
    chunks_path = cfg["chunks"]
    index_path = cfg["index"]
    meta_path = cfg["meta"]
    
    print(f"[Vectorstore] [{cfg['short']}] Verificando chunks em {chunks_path}...")
    
    if os.path.exists(chunks_path):
        with open(chunks_path, encoding="utf-8") as f:
            chunks = json.load(f)
        
        print(f"[Vectorstore] {len(chunks)} chunks encontrados. Iniciando Embedder...")
        
        embeddings = embed_chunks(chunks)
        build_and_save(embeddings, index_path, meta_path)
    else:
        print(f"ERRO: Chunks não encontrados em {chunks_path}. Rode o src.chunker --report {args.report} primeiro.")
