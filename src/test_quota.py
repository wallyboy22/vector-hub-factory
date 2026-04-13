from google import genai
import os
from dotenv import load_dotenv

load_dotenv('.env')
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

def test(model, task_type=None):
    try:
        if task_type:
             client.models.embed_content(model=model, contents="Oi", config={"task_type": task_type})
        else:
             client.models.generate_content(model=model, contents="Oi")
        return "✅ OK"
    except Exception as e:
        return f"❌ FALHOU: {e}"

print("--- TESTE DE COTAS (GOOGLE AI) ---")
print(f"Embedding (Busca): {test('models/gemini-embedding-001', 'RETRIEVAL_QUERY')}")
print(f"Flash (Cérebro 1): {test('models/gemini-flash-latest')}")
print(f"Pro (Cérebro 2):   {test('models/gemini-pro-latest')}")
