import time
from google import genai
from config import GOOGLE_API_KEY, EMBEDDING_MODEL

# Configura o Cliente Google GenAI
client = genai.Client(api_key=GOOGLE_API_KEY)

EMBEDDING_DIM = 768   # Gemini-embedding-001 usa 768

def embed_query(query: str) -> list[float]:
    """Gera embedding para uma query de busca."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config={"task_type": "RETRIEVAL_QUERY"}
    )
    return list(response.embeddings[0].values)

def embed(texts: list[str], retries: int = 3) -> list[list[float]]:
    """Gera embeddings com suporte a re-tentativa e pausa para evitar 429."""
    for i in range(retries):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config={
                    "task_type": "RETRIEVAL_DOCUMENT"
                }
            )
            return [list(e.values) for e in response.embeddings]
        except Exception as e:
            if "429" in str(e):
                # Se for limite de cota, espera 10 segundos e tenta de novo
                wait = (i + 1) * 10
                print(f"  [Aviso] Cota atingida. Esperando {wait}s antes de tentar novamente...")
                time.sleep(wait)
                continue
            print(f"Erro ao gerar embeddings (Modelo {EMBEDDING_MODEL}): {e}")
            break
    return []

def embed_chunks(chunks: list[dict], batch_size: int = 30) -> list[dict]:
    """Processa blocos menores para evitar estourar a cota do AI Studio."""
    result = []
    print(f"[Início] Gerando embeddings para {len(chunks)} chunks...")
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch]
        vectors = embed(texts)
        if not vectors:
            continue
            
        for chunk, vector in zip(batch, vectors):
            result.append({"vector": vector, "metadata": chunk})
        
        # Pausa obrigatória de 1 segundo entre bateladas (segurança)
        time.sleep(1)
        print(f"  Embeds gerados: {min(i + batch_size, len(chunks))}/{len(chunks)}")
        
    return result
