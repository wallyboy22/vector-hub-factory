import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

GOOGLE_API_KEY     = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY_ALT = os.getenv("GOOGLE_API_KEY_ALT")
GOOGLE_API_KEY_ALT2 = os.getenv("GOOGLE_API_KEY_ALT2")

# Lista consolidada de todas as chaves válidas (para fallback genérico)
def _load_all_api_keys() -> list[str]:
    keys = []
    # Primeiro adiciona a chave principal
    if GOOGLE_API_KEY:
        keys.append(GOOGLE_API_KEY)
    # Busca dinamicamente ALT, ALT2, ALT3, ... até ALT9
    for i in range(1, 10):
        suffix = "_ALT" if i == 1 else f"_ALT{i}"
        k = os.getenv(f"GOOGLE_API_KEY{suffix}")
        if k and len(k) > 20 and "SEU" not in k and k not in keys:
            keys.append(k)
    return keys

ALL_API_KEYS = _load_all_api_keys()

EMBEDDING_MODEL = "models/gemini-embedding-001"
LLM_MODELS = {
    "flash": "gemini-2.0-flash",
    "pro":   "gemini-1.5-pro"
}

CHUNK_SIZE    = 700
CHUNK_OVERLAP = 100
TOP_K         = 8

DOCUMENTS = {
    "raf": {
        "name":     "Relatório Anual do Fogo",
        "short":    "RAF",
        "emoji":    "🔥",
        "color":    "#E8503A",
        "pdf":      os.path.join("docs", "raf", "RAF2024.pdf"),
        "logo":     os.path.join("ui", "assets", "logos", "logomarca-mapbiomas_fogo_raf.png"),
        "chunks":   os.path.join("docs", "raf", "data", "chunks", "chunks.json"),
        "embeddings": {
            "gemini": {
                "index":    os.path.join("docs", "raf", "data", "embeddings", "gemini-embedding-001", "faiss.index"),
                "meta":     os.path.join("docs", "raf", "data", "embeddings", "gemini-embedding-001", "meta.json"),
                "model_id": "models/gemini-embedding-001",
                "dims":     768,
                "cost":     "Gratuito (quota)",
                "provider": "Google AI Studio"
            }
        },
        "prompt_role": "assistente especializado no Relatório Anual do Fogo (RAF) do MapBiomas",
        "app": os.path.join("apps", "raf_chatbot", "app.py")
    },
    "rad": {
        "name":     "Relatório Anual do Desmatamento",
        "short":    "RAD",
        "emoji":    "🌳",
        "color":    "#812411",
        "pdf":      os.path.join("docs", "rad", "RAD2024.pdf"),
        "logo":     os.path.join("ui", "assets", "logos", "logomarca_mapbiomas_alerta_rad.png"),
        "chunks":   os.path.join("docs", "rad", "data", "chunks", "chunks.json"),
        "embeddings": {
            "gemini": {
                "index":    os.path.join("docs", "rad", "data", "embeddings", "gemini-embedding-001", "faiss.index"),
                "meta":     os.path.join("docs", "rad", "data", "embeddings", "gemini-embedding-001", "meta.json"),
                "model_id": "models/gemini-embedding-001",
                "dims":     768,
                "cost":     "Gratuito (quota)",
                "provider": "Google AI Studio"
            }
        },
        "prompt_role": "assistente especializado no Relatório Anual do Desmatamento (RAD) do MapBiomas",
        "app": os.path.join("apps", "rad_chatbot", "app.py")
    }
}

HUB_CONFIG = {
    "title":    "Vector Hub Factory",
    "subtitle": "Documentos Científicos Prontos para IA",
    "github":   "https://github.com/seu-usuario/vector-hub-factory"
}