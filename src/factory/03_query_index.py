import argparse
import json
import os
import sys

import numpy as np
import faiss
from google import genai


def load_api_key():
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", "references", "mapbiomas-chat", "refference", ".env")
    load_dotenv(env_path)
    return os.getenv("GOOGLE_API_KEY")


EMBEDDING_MODEL = "models/gemini-embedding-001"
TOP_K_DEFAULT = 5


def search(query: str, index_path: str, meta_path: str, api_key: str, top_k: int = 5) -> list[dict]:
    index = faiss.read_index(index_path)
    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)
    
    client = genai.Client(api_key=api_key)
    resp = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config={"task_type": "RETRIEVAL_QUERY"}
    )
    vec_list = list(resp.embeddings[0].values)
    vec = np.array([vec_list], dtype="float32")
    
    distances, indices = index.search(vec, top_k)
    return [metadata[i] for i in indices[0] if i < len(metadata)]


def main():
    parser = argparse.ArgumentParser(description="Buscar no indice")
    parser.add_argument("--index", required=True, help="Caminho do faiss.index")
    parser.add_argument("--meta", required=True, help="Caminho do meta.json")
    parser.add_argument("--text", required=True, help="Texto da busca")
    parser.add_argument("--top-k", type=int, default=TOP_K_DEFAULT, help="Numero de resultados")
    parser.add_argument("--model", default="gemini", help="Modelo (gemini)")
    parser.add_argument("--api-key", help="Chave da API (opcional)")
    args = parser.parse_args()
    
    api_key = args.api_key or load_api_key()
    if not api_key:
        print("Erro: GOOGLE_API_KEY nao encontrada.")
        sys.exit(1)
    
    results = search(args.text, args.index, args.meta, api_key, args.top_k)
    
    output = []
    for rank, r in enumerate(results, 1):
        output.append({
            "rank": rank,
            "score": float(1 / (1 + rank * 0.1)),
            "page": r.get("page"),
            "chunk_id": r.get("chunk_id"),
            "content": r.get("content", "")[:200]
        })
    
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdout.buffer.write(json.dumps(output, ensure_ascii=False, indent=2).encode('utf-8'))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()