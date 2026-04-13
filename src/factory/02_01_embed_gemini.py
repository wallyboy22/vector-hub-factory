import argparse
import json
import os
import time

import faiss
import numpy as np
from google import genai


EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 768
BATCH_SIZE = 30


def load_api_key():
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", "references", "mapbiomas-chat", "refference", ".env")
    load_dotenv(env_path)
    return os.getenv("GOOGLE_API_KEY")


def embed(texts: list[str], api_key: str, retries: int = 3) -> list[list[float]]:
    client = genai.Client(api_key=api_key)
    for i in range(retries):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config={"task_type": "RETRIEVAL_DOCUMENT"}
            )
            return [list(e.values) for e in response.embeddings]
        except Exception as e:
            if "429" in str(e):
                wait = (i + 1) * 10
                print(f"  [Aviso] Cota atingida. Esperando {wait}s...")
                time.sleep(wait)
                continue
            print(f"Erro ao gerar embeddings: {e}")
            break
    return []


def embed_chunks(chunks: list[dict], api_key: str) -> list[dict]:
    result = []
    print(f"[Inicio] Gerando embeddings para {len(chunks)} chunks...")
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        vectors = embed(texts, api_key)
        if not vectors:
            continue
        
        for chunk, vector in zip(batch, vectors):
            result.append({"vector": vector, "metadata": chunk})
        
        time.sleep(1)
        print(f"  Embeds gerados: {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")
    
    return result


def build_and_save(embeddings: list[dict], index_path: str, meta_path: str):
    if not embeddings:
        print("Erro: Nenhuma embedding gerada.")
        return
    
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    vectors = np.array([e["vector"] for e in embeddings], dtype="float32")
    
    n, d = vectors.shape
    index = faiss.IndexFlatL2(d)
    index.add(vectors)
    faiss.write_index(index, index_path)
    
    metadata = [e["metadata"] for e in embeddings]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)
    
    print(f"OK Indice salvo: {index.ntotal} vetores em {index_path}")


def main():
    parser = argparse.ArgumentParser(description="Gerar embeddings com Gemini")
    parser.add_argument("--chunks", required=True, help="Caminho do chunks.json")
    parser.add_argument("--output-dir", required=True, help="Diretorio de saida")
    parser.add_argument("--api-key", help="Chave da API (opcional)")
    args = parser.parse_args()
    
    api_key = args.api_key or load_api_key()
    if not api_key:
        print("Erro: GOOGLE_API_KEY nao encontrada.")
        return
    
    with open(args.chunks, encoding="utf-8") as f:
        chunks = json.load(f)
    
    embeddings = embed_chunks(chunks, api_key)
    if not embeddings:
        print("Erro: Nenhuma embedding gerada.")
        return
    
    model_dir = os.path.join(args.output_dir, "gemini-embedding-001")
    index_path = os.path.join(model_dir, "faiss.index")
    meta_path = os.path.join(model_dir, "meta.json")
    
    build_and_save(embeddings, index_path, meta_path)


if __name__ == "__main__":
    main()