import os
from dotenv import load_dotenv

_is_render = os.getenv("RENDER") == "true" or (os.getenv("PORT") is not None and os.getenv("HOME") == "/opt/render/project/src")
_is_cloud = _is_render or os.getenv("RENDER_EXTERNAL_HOSTNAME") is not None

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

# ── Modo de Operação ───────────────────────────────────────────────────────────
# DEV_MODE=true  → Hub completo (upload, factory, criar apps) — uso LOCAL
# DEV_MODE=false → Hub limpo (apenas chatbots) — deploy Render/produção

if _is_cloud:
    DEV_MODE = False
else:
    DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"

# Se estiver no Render, NUNCA permite DEV_MODE por segurança
if _is_render:
    DEV_MODE = False

# ── APP REGISTRY (Apps Nativos do Hub) ───────────────────────────────────────────
# Gerenciado automaticamente na inicialização do servidor
# Cada app define: emoji, cor, perguntas sugeridas, docs relacionados

APP_REGISTRY = {
    "raf": {
        "name": "Relatório Anual do Fogo",
        "emoji": "🔥",
        "color": "#E8503A",
        "doc_id": "raf",
        "docs": ["raf"],
        "type": "single_doc",
        "questions": [
            "Qual a área total queimada no Brasil em 2024?",
            "Como o fogo afetou o Pantanal em 2024?",
            "Qual o impacto do fogo na Amazônia?",
            "Qual a metodologia usada pelo MapBiomas?",
            "Quais estados tiveram mais área queimada?",
            "Como evoluiu o fogo nos últimos anos?"
        ]
    },
    "rad": {
        "name": "Relatório Anual de Desmatamento",
        "emoji": "🌳",
        "color": "#812411",
        "doc_id": "rad",
        "docs": ["rad"],
        "type": "single_doc",
        "questions": [
            "Qual a área total desmatada no Brasil em 2024?",
            "Quais estados tiveram mais desmatamento?",
            "Como está a tendência na Amazônia?",
            "Qual o impacto em terras indígenas?",
            "Quanto foi de desmatamento ilegal?",
            "Como evolução do desmatamento nos últimos anos?"
        ]
    },
    "relatorios_anuais": {
        "name": "Relatórios Anuais (Fogo + Desmatamento)",
        "emoji": "📚",
        "color": "#1e293b",
        "doc_id": "cross",
        "docs": ["raf", "rad"],
        "type": "cross_doc",
        "questions": [
            "Como o fogo se relaciona com o desmatamento?",
            "Quais biomas foram mais afetados em 2024?",
            "Dados de terras indígenas têm maior fogo ou desmatamento?",
            "Qual a metodologia do MapBiomas para monitoramento?",
            "Qual a relação entre áreas protegidas e desmatamento?",
            "Como os estados com maior fogo também têm desmatamento?"
        ]
    },
    "geral": {
        "name": "Geral (Todos os Dados)",
        "emoji": "🌍",
        "color": "#7C3AED",
        "doc_id": "all",
        "docs": [],  # Preenchido dinamicamente com todos os docs disponíveis
        "type": "all_docs",
        "questions": [
            "Resumo geral dos dados disponíveis no hub?",
            "Quais documentos estão disponíveis para consulta?",
            "Qual a cobertura temporal dos dados?",
            "Quais biomas estão representados nos dados?",
            "Como acessar todos os relatórios do MapBiomas?",
            "Quais são as principais métricas disponíveis?"
        ]
    }
}

def init_app_registry():
    """Inicializa o registry após DOCUMENTS estar definido."""
    if "raf" in DOCUMENTS:
        APP_REGISTRY["raf"]["docs"] = ["raf"]
    if "rad" in DOCUMENTS:
        APP_REGISTRY["rad"]["docs"] = ["rad"]
    if "relatorios_anuais" in DOCUMENTS:
        APP_REGISTRY["relatorios_anuais"]["docs"] = ["raf", "rad"]
    
    if "geral" in APP_REGISTRY:
        APP_REGISTRY["geral"]["docs"] = list(DOCUMENTS.keys())
    
    return APP_REGISTRY

# ── Gerenciamento de DEV_MODE e Chaves (Modo Desenvolvedor) ──────────────────────
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), ".env")

def _save_env_key(key_name: str, value: str) -> bool:
    """Salva uma chave no arquivo .env local. Retorna True se bem-sucedido."""
    if not DEV_MODE:
        return False
    if not value or len(value) < 10:
        return False
    try:
        lines = []
        if os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        key_exists = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key_name}="):
                new_lines.append(f"{key_name}={value}\n")
                key_exists = True
            else:
                new_lines.append(line)
        
        if not key_exists:
            new_lines.append(f"{key_name}={value}\n")
        
        with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        return True
    except Exception as e:
        print(f"[!] Erro ao salvar chave {key_name}: {e}")
        return False

def set_dev_mode(enabled: bool) -> bool:
    """Alterna o modo desenvolvedor. Retorna True se bem-sucedido."""
    global DEV_MODE
    if enabled:
        _save_env_key("DEV_MODE", "true")
        DEV_MODE = True
        return True
    else:
        _save_env_key("DEV_MODE", "false")
        DEV_MODE = False
        return False

# ── Chaves Google (Gemini — Embedding + Chat) ───────────────────────────
# Supports both new names (GOOGLE_API_KEY) and legacy (GOOGLE_API_KEY_0)
GOOGLE_API_KEY      = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY_0")
GOOGLE_API_KEY_ALT  = os.getenv("GOOGLE_API_KEY_ALT") or os.getenv("GOOGLE_API_KEY_1")
GOOGLE_API_KEY_ALT2 = os.getenv("GOOGLE_API_KEY_ALT2") or os.getenv("GOOGLE_API_KEY_2")

def _load_all_api_keys() -> list[str]:
    """Lista consolidada de chaves Gemini."""
    keys = []
    # Try new format first
    for key in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_ALT", "GOOGLE_API_KEY_ALT2"]:
        k = os.getenv(key)
        if k and len(k) > 20 and k not in keys:
            keys.append(k)
    # Try legacy format (_0, _1, _2...)
    if not keys:
        for i in range(10):
            k = os.getenv(f"GOOGLE_API_KEY_{i}")
            if k and len(k) > 20 and k not in keys:
                keys.append(k)
    return keys

ALL_API_KEYS = _load_all_api_keys()

# ── Chaves de Outros Provedores ────────────────────────────────────────────────
# Supports both new names and legacy (_0 suffix)
GROQ_API_KEY  = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_0")
JINA_API_KEY = os.getenv("JINA_API_KEY") or os.getenv("JINA_API_KEY_0")
HF_API_KEY   = os.getenv("HUGGINFACE_API_KEY") or os.getenv("HUGGINFACE_API_KEY_0") or os.getenv("HUGGINGFACE_API_KEY")
OPENCODE_API_KEY = os.getenv("OPENCODE_ZEN_API_KEY") or os.getenv("OPENCODE_API_KEY")

def _load_groq_keys() -> list[str]:
    """Descobre todas as chaves Groq disponíveis."""
    keys = []
    # Try new format first
    for key in ["GROQ_API_KEY"]:
        k = os.getenv(key)
        if k and len(k) > 10 and k not in keys:
            keys.append(k)
    # Try legacy format (_0, _1, _2...)
    if not keys:
        for i in range(10):
            k = os.getenv(f"GROQ_API_KEY_{i}")
            if k and len(k) > 10 and k not in keys:
                keys.append(k)
    return keys

ALL_GROQ_KEYS = _load_groq_keys()

# ── Modelos de Embedding ───────────────────────────────────────────────────────
EMBEDDING_MODEL = "models/gemini-embedding-001"  # default (legado/qa.py)

EMBEDDING_PROVIDERS = {
    "gemini": {
        "name":       "Google Gemini",
        "model_id":   "models/gemini-embedding-001",
        "dims":       768,
        "type":       "api",
        "key_env":    "GOOGLE_API_KEY",
        "render_ok":  True,
    },
    "jina": {
        "name":       "Jina AI v3",
        "model_id":   "jina-embeddings-v3",
        "dims":       1024,
        "type":       "api",
        "key_env":    "JINA_API_KEY",
        "render_ok":  True,
    },
    "huggingface": {
        "name":       "HuggingFace API",
        "model_id":   "sentence-transformers/all-MiniLM-L6-v2",
        "dims":       384,
        "type":       "api",
        "key_env":    "HUGGINFACE_API_KEY",
        "render_ok":  True,
    },
    "local": {
        "name":       "Local (offline)",
        "model_id":   "all-MiniLM-L6-v2",
        "dims":       384,
        "type":       "local",
        "key_env":    None,
        "render_ok":  False,   # RAM insuficiente no Render free
    },
}

# ── Modelos LLM ───────────────────────────────────────────────────────────────
LLM_MODELS = {
    # Groq (primário — mais rápido e com cota generosa)
    "groq-fast":  "llama-3.1-8b-instant",      # ultra rápido
    "groq":       "llama-3.3-70b-versatile",   # melhor qualidade
    # Gemini (fallback)
    "flash":      "gemini-2.0-flash",
    "pro":        "gemini-1.5-pro",
    # OpenCode Zen (Big Pickle - grátis)
    "bigpickle":  "big-pickle",
}

LLM_PROVIDERS = {
    "groq": {
        "name":      "Groq (Llama 3.3)",
        "model":     LLM_MODELS["groq"],
        "key_env":   "GROQ_API_KEY",
        "available": bool(GROQ_API_KEY),
        "render_ok": True,
    },
    "gemini": {
        "name":      "Google Gemini Flash",
        "model":     LLM_MODELS["flash"],
        "key_env":   "GOOGLE_API_KEY",
        "available": bool(GOOGLE_API_KEY),
        "render_ok": True,
    },
    "jina": {
        "name":      "Jina AI DeepSearch (10M Free)",
        "model":     "jina-deepsearch-v1",
        "key_env":   "JINA_API_KEY",
        "available": bool(JINA_API_KEY),
        "render_ok": True,
    },
    "bigpickle": {
        "name":      "Big Pickle (OpenCode Zen)",
        "model":     LLM_MODELS["bigpickle"],
        "key_env":   "OPENCODE_ZEN_API_KEY",
        "available": bool(OPENCODE_API_KEY),
        "render_ok": True,
    },
    "raw_chunks": {
        "name":      "Apenas Chunks (sem IA)",
        "model":     None,
        "key_env":   None,
        "available": True,
        "render_ok": True,
    },
}

# ── Parâmetros RAG ─────────────────────────────────────────────────────────────
CHUNK_SIZE    = 700
CHUNK_OVERLAP = 100
TOP_K         = 8

# ── Documentos Registrados ────────────────────────────────────────────────────
# Nota: no futuro será migrado para docs.json dinâmico.
# Por ora mantém retrocompatibilidade com qa.py e guardian.py.
DOCUMENTS = {
    "raf": {
        "name":     "Relatório Anual do Fogo",
        "short":    "RAF",
        "emoji":    "🔥",
        "color":    "#E8503A",
        "pdf":      os.path.join("docs", "raf", "RAF2024.pdf"),
        "logo":     os.path.join("ui", "assets", "logos", "logomarca-mapbiomas_fogo_raf.png"),
        "chunks":   os.path.join("docs", "raf", "assets", "chunks", "chunks.json"),
        "embeddings": {
            "gemini": {
                "index":    os.path.join("docs", "raf", "assets", "embeddings", "gemini-embedding-001", "faiss.index"),
                "meta":     os.path.join("docs", "raf", "assets", "embeddings", "gemini-embedding-001", "meta.json"),
                "model_id": "models/gemini-embedding-001",
                "dims":     768,
            },
            # Novos providers são adicionados aqui conforme gerados via Hub
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
        "chunks":   os.path.join("docs", "rad", "assets", "chunks", "chunks.json"),
        "embeddings": {
            "gemini": {
                "index":    os.path.join("docs", "rad", "assets", "embeddings", "gemini-embedding-001", "faiss.index"),
                "meta":     os.path.join("docs", "rad", "assets", "embeddings", "gemini-embedding-001", "meta.json"),
                "model_id": "models/gemini-embedding-001",
                "dims":     768,
            },
        },
        "prompt_role": "assistente especializado no Relatório Anual do Desmatamento (RAD) do MapBiomas",
        "app": os.path.join("apps", "rad_chatbot", "app.py")
    }
}

# Inicializa registry APÓS DOCUMENTS estar definido
init_app_registry()

HUB_CONFIG = {
    "title":    "Vector Hub Factory",
    "subtitle": "Documentos Científicos Prontos para IA",
    "github":   "https://github.com/wallyboy22/vector-hub-factory",
    "dev_mode": DEV_MODE,
}

# Registry de apps nativos - configurado em memória pelo servidor
# Use /factory/apps endpoint para ver a configuração atual