import faiss
import json
import os
from src.config import REPORTS

def generate_didactic_files():
    for key, cfg in REPORTS.items():
        index_path = cfg["index"]
        meta_path = cfg["meta"]
        
        # Só gera se o índice já existir
        if os.path.exists(index_path) and os.path.exists(meta_path):
            print(f"Gerando arquivo didático para {key.upper()}...")
            
            # Carrega índice e metadados
            idx = faiss.read_index(index_path)
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            
            # Exporta 100% dos trechos (didático/completo)
            export_data = []
            
            for i in range(len(meta)):
                vector = idx.reconstruct(i).tolist()
                export_data.append({
                    "pagina": meta[i]["page"],
                    "trecho_texto": meta[i]["content"],
                    "vetor_embedding_768_dim": vector
                })
            
            # Caminho final na pasta do index
            output_dir = os.path.dirname(index_path)
            output_file = os.path.join(output_dir, f"{key.upper()}_didatico_embeddings.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Concluído: {output_file}")
        else:
            print(f"Aviso: Índice {key.upper()} não encontrado em {index_path}")

if __name__ == "__main__":
    generate_didactic_files()
