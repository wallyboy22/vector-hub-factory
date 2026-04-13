import os
import sys

# Adicionar ROOT ao sys.path para importar config.py corretamente
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import time
import requests
import faiss
import json
from config import DOCUMENTS, ALL_API_KEYS

class AppGuardian:
    """Agente de saúde e auto-recuperação para o Vector Hub Factory."""
    
    def __init__(self):
        self.health_history = []
        self.last_check = 0

    def check_system_integrity(self):
        """Verifica se todos os componentes vitais estão no lugar."""
        status = {"ready": True, "issues": []}
        
        # 1. Verificar chaves
        if not ALL_API_KEYS:
            status["ready"] = False
            status["issues"].append("Nenhuma chave de API detectada no arquivo .env")
            
        # 2. Verificar índices e metadados
        for key, cfg in DOCUMENTS.items():
            idx_path = cfg["embeddings"]["gemini"]["index"]
            meta_path = cfg["embeddings"]["gemini"]["meta"]
            
            if not os.path.exists(idx_path):
                status["ready"] = False
                status["issues"].append(f"Índice FAISS ausente para {key}: {idx_path}")
            else:
                try:
                    # Tenta carregar o header do arquivo faiss para ver se não está corrompido
                    faiss.read_index(idx_path)
                except Exception as e:
                    status["ready"] = False
                    status["issues"].append(f"Índice FAISS corrompido para {key}: {str(e)}")

            if not os.path.exists(meta_path):
                status["ready"] = False
                status["issues"].append(f"Metadados JSON ausentes para {key}: {meta_path}")
        
        return status

    def check_localhost(self, url="http://localhost:8000"):
        """Verifica se o servidor local está respondendo e saudável."""
        try:
            resp = requests.get(f"{url}/health", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                print(f"  [GUARDIÃO] Localhost: ✓ Online (v{data.get('version')})")
                return True
            else:
                print(f"  [GUARDIÃO] Localhost: ! Erro {resp.status_code}")
        except Exception:
            print("  [GUARDIÃO] Localhost: ✗ Offline")
        return False

    def run_smoke_test(self, api_url="http://localhost:8000"):
        """Tenta fazer uma pergunta real ao sistema para garantir que tudo funciona."""
        try:
            # Esperar o servidor subir se necessário
            time.sleep(2)
            resp = requests.post(f"{api_url}/search", 
                               json={"question": "teste de pulso", "report": "raf"},
                               timeout=10)
            if resp.status_code == 200:
                print("  [GUARDIÃO] Smoke Test: ✓ Backend respondendo corretamente.")
                return True
            else:
                print(f"  [GUARDIÃO] Smoke Test: ✗ Erro {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"  [GUARDIÃO] Smoke Test: ✗ Falha de conexão: {e}")
        return False

def perform_auto_repair():
    """Tenta corrigir problemas comuns automaticamente."""
    print("[GUARDIÃO] Analisando ambiente para auto-reparo...")
    # Se houver problemas que podem ser automatizados no futuro, entram aqui.
    # Ex: reindexar se o arquivo estiver faltando e o chunks.json existir.
    pass

if __name__ == "__main__":
    guardian = AppGuardian()
    report = guardian.check_system_integrity()
    if report["ready"]:
        print("✓ TUDO PRONTO: Sistema íntegro.")
    else:
        print("✗ PROBLEMAS DETECTADOS:")
        for issue in report["issues"]:
            print(f"  - {issue}")
