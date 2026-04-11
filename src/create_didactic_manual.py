import faiss
import json
import os
from src.config import REPORTS

def create_didactic_manual():
    print("Gerando manual didático consolidado...")
    manual = {
        "titulo": "Manual Didático de Embeddings - MapBiomas (IPAM)",
        "conceitos_chave": {
            "o_que_sao_embeddings": "Representações matemáticas de pedaços de texto. Cada texto do PDF é 'traduzido' para uma lista de números que a IA consegue entender.",
            "dimensoes": 768,
            "dimensoes_explicacao": "O modelo Google Gemini Embedding-001 usa 768 números para descrever cada trecho de texto. Pense nisso como 768 'coordenadas' que definem o significado exato de uma frase em um mapa mental gigante da IA.",
            "similaridade_vetorial": "Quando você faz uma pergunta, o chatbot converte sua pergunta em um vetor e procura, usando o FAISS, quais vetores dos relatórios estão mais 'perto' (matematicamente similares) da sua dúvida."
        },
        "indices_ativos": []
    }

    for key, cfg in REPORTS.items():
        index_path = cfg["index"]
        if os.path.exists(index_path):
            idx = faiss.read_index(index_path)
            manual["indices_ativos"].append({
                "id_relatorio": key.upper(),
                "nome_oficial": cfg["name"],
                "total_de_blocos_de_texto": idx.ntotal,
                "tamanho_cada_vetor": idx.d,
                "diretorio_dos_dados": os.path.dirname(index_path),
                "resumo": f"Este índice contém {idx.ntotal} trechos do {cfg['name']} processados e prontos para busca inteligente."
            })
    
    output_meta = "data/manual_didatico_embeddings.json"
    with open(output_meta, 'w', encoding='utf-8') as f:
        json.dump(manual, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Manual gerado com sucesso em {output_meta}!")

if __name__ == "__main__":
    create_didactic_manual()
