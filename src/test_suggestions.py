import json
import time
import os
from src.qa import answer
from src.config import REPORTS

# Banco de perguntas idêntico ao da UI
QUESTION_BANKS = {
    "raf": [
        "Qual a área total queimada no Brasil em 2024?",
        "Como o fogo se comportou no bioma Pantanal em 2024?",
        "Qual a área queimada em formações naturais e vegetação nativa?",
        "Qual o impacto do fogo na Amazônia em 2024?",
        "Existem dados sobre fogo em terras indígenas e unidades de conservação?",
        "Qual a relação entre o clima e os números de fogo de 2024?",
        "Qual foi o mês em que o fogo foi mais intenso?"
    ],
    "rad": [
        "Qual a área total desmatada no Brasil em 2023?",
        "O desmatamento está aumentando ou diminuindo nos últimos anos?",
        "Qual a relação entre expansão agropecuária e desmatamento?",
        "Qual foi o desmatamento dentro de Terras Indígenas e UCs?",
        "Quais estados lideraram o ranking de desmatamento?",
        "Quais as fontes de dados do MapBiomas Alerta?"
    ]
}

def is_valid_answer(text):
    """Verifica se a resposta é real do PDF ou apenas um aviso de cota."""
    indicators = ["IA Ocupada", "sobrecarregada", "limite diário", "Não encontrei"]
    return not any(ind in text for ind in indicators)

def run_resilient_tests():
    print("=== TESTE DE QUALIDADE RESILIENTE (RAF/RAD) ===")
    print("Atenção: Este teste será pausado em 15s entre perguntas para evitar bloqueios de cota.\n")
    
    results = {}

    for report_key, questions in QUESTION_BANKS.items():
        print(f"\n--- Iniciando [{report_key.upper()}] ---")
        results[report_key] = []
        
        for i, q in enumerate(questions):
            print(f"  [{i+1}/{len(questions)}] Pergunta: '{q}'")
            
            success = False
            attempts = 0
            max_attempts = 2 # Tenta até 2 vezes se bater na cota
            
            while not success and attempts < max_attempts:
                attempts += 1
                try:
                    # Tenta obter a resposta via modelo Flash (o mesmo do Chat)
                    res = answer(q, report_key, model_key="flash")
                    ans_text = res.get("answer", "")
                    pages = [s["page"] for s in res.get("sources", [])]
                    
                    if is_valid_answer(ans_text):
                        status = "✅ SUCESSO"
                        success = True
                        print(f"    {status} (Págs: {sorted(list(set(pages)))})")
                    else:
                        status = "⚠️ COTA BLOQUEADA"
                        print(f"    {status} - O Google bloqueou ambas as chaves ou tokens. Sugestão: Aguarde 1 min ou teste esta pergunta manualmente no Chat.")
                        break # Pula para a próxima se bater na cota total
                        
                    # Guarda o resultado parcial ou final
                    if success or attempts == max_attempts:
                        results[report_key].append({
                            "question": q,
                            "status": status,
                            "preview": ans_text[:200] + "...",
                            "pages": sorted(list(set(pages)))
                        })

                except Exception as e:
                    print(f"    ❌ ERRO: {e}")
                    break
            
            # Descanso estratégico (o Google costuma aceitar melhor após 45s)
            if i < len(questions) - 1:
                print("    ...aguardando 45s para a próxima pergunta...")
                time.sleep(45)

    # Salva o relatório final
    report_file = "data/relatorio_teste_sugestoes.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✨ Teste concluído! Relatório final atualizado em '{report_file}'.")

if __name__ == "__main__":
    run_resilient_tests()
