import os
from dotenv import load_dotenv

# Caminho para o arquivo .env
env_path = os.path.join(os.path.dirname(__file__), "..", "refference", ".env")
load_dotenv(env_path)

GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY_ALT = os.getenv("GOOGLE_API_KEY_ALT")

# Configurações de Modelos (Confirmados pelo Diagnóstico)
EMBEDDING_MODEL = "models/gemini-embedding-001"
LLM_MODELS = {
    "flash": "models/gemini-flash-latest",
    "pro":   "models/gemini-pro-latest"
}
LLM_MODEL_DEFAULT = LLM_MODELS["flash"]

CHUNK_SIZE    = 700
CHUNK_OVERLAP = 100
TOP_K = 8

# Dicionário de relatórios disponíveis
REPORTS = {
    "raf": {
        "name": "Relatório Anual do Fogo",
        "short": "RAF",
        "emoji": "🔥",
        "color": "#E8503A",
        "logo":  os.path.join("data", "logomarca-mapbiomas_fogo_raf.png"),
        "pdf":    os.path.join("data", "raf", "raw", "RAF2024_24.06.2025_v2.pdf"),
        "chunks": os.path.join("data", "raf", "chunks", "chunks.json"),
        "index":  os.path.join("data", "raf", "index", "faiss.index"),
        "meta":   os.path.join("data", "raf", "index", "meta.json"),
        "prompt_role": "assistente especializado no Relatório Anual do Fogo (RAF) do MapBiomas",
    },
    "rad": {
        "name": "Relatório Anual do Desmatamento",
        "short": "RAD",
        "emoji": "🌳",
        "color": "#812411",
        "logo":  os.path.join("data", "logomarca_mapbiomas_alerta_rad.png"),
        "pdf":    os.path.join("data", "rad", "raw", "RAD2024_28_10.pdf"),
        "chunks": os.path.join("data", "rad", "chunks", "chunks.json"),
        "index":  os.path.join("data", "rad", "index", "faiss.index"),
        "meta":   os.path.join("data", "rad", "index", "meta.json"),
        "prompt_role": "assistente especializado no Relatório Anual do Desmatamento (RAD) do MapBiomas",
    },
}

# Mantém compatibilidade com outros arquivos
PDF_PATH    = REPORTS["raf"]["pdf"]
CHUNKS_PATH = REPORTS["raf"]["chunks"]
INDEX_PATH  = REPORTS["raf"]["index"]
META_PATH   = REPORTS["raf"]["meta"]
LLM_MODEL   = LLM_MODEL_DEFAULT
