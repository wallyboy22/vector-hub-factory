"""
discovery.py — Sistema de Descoberta Dinâmica de Índices
======================================================
Varre o sistema de arquivos para mapear índices gerados pela fábrica
que não estão no arquivo de configuração estático.
"""

import os
from config import DOCUMENTS, EMBEDDING_PROVIDERS

def discover_indices():
    """Varre a pasta docs/ para encontrar índices de embeddings e registrar em DOCUMENTS."""
    for key in list(DOCUMENTS.keys()):
        cfg = DOCUMENTS[key]
        if "embeddings" not in cfg: 
            cfg["embeddings"] = {}
        
        # Pasta de busca: docs/{key}/assets/embeddings/{provider_foldername}
        emb_base = os.path.join("docs", key, "assets", "embeddings")
        if os.path.exists(emb_base):
            for model_folder in os.listdir(emb_base):
                # Tenta mapear o folder para um provedor conhecido
                for p_id, p_info in EMBEDDING_PROVIDERS.items():
                    target_name = p_info["model_id"].replace("/", "-")
                    if target_name == model_folder:
                        idx_path = os.path.join(emb_base, model_folder, "faiss.index")
                        meta_path = os.path.join(emb_base, model_folder, "meta.json")
                        
                        # Se o índice existir e não estiver mapeado (ou se quisermos atualizar)
                        if os.path.exists(idx_path):
                            # Se já existe uma entrada gemini hardcoded, não sobrescrevemos
                            # a menos que seja o folder correto. 
                            # Aqui registramos dinamicamente.
                            cfg["embeddings"][p_id] = {
                                "index": idx_path,
                                "meta": meta_path,
                                "dims": p_info.get("dims", 768)
                            }
    # print(f"  [Discovery] Índices mapeados com sucesso.")
    return DOCUMENTS
