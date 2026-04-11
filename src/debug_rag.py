import json
import os
from src.qa import search, answer
from src.config import REPORTS

def debug_rag():
    print("=== DIAGNÓSTICO DE RECUPERAÇÃO (RAG) - RAF ===")
    
    chunks_path = REPORTS["raf"]["chunks"]
    with open(chunks_path, encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"✓ Base de conhecimento: {len(chunks)} chunks.")

    queries = [
        "Qual a relação entre o clima e os números de fogo de 2024?",
        "Qual a área queimada em formações naturais e vegetação nativa?"
    ]

    for query in queries:
        print(f"\n--- TESTANDO: '{query}' ---")
        
        # 1. Busca Semântica
        retrieved = search(query, "raf")
        if not retrieved:
            print("  ❌ NADA recuperado na busca semântica.")
        else:
            print(f"  ✓ Recuperados {len(retrieved)} trechos.")
            for i, r in enumerate(retrieved):
                print(f"    [{i+1}] Pág {r['page']}: {r['content'][:150]}...")

        # 2. Resposta da IA
        res = answer(query, "raf")
        print(f"  >> RESPOSTA: {res['answer'][:200]}...")

    # 3. Scan por termos de tabelas
    print("\n--- SCAN DE TABELAS (Termos específicos) ---")
    table_terms = ["tabela 9", "natural", "antrópico", "514.515.350"]
    for term in table_terms:
        found = [c for c in chunks if term.lower() in c['content'].lower()]
        print(f"  Termo '{term}': {len(found)} ocorrências.")

if __name__ == "__main__":
    debug_rag()
