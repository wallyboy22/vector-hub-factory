from google import genai
import os
from dotenv import load_dotenv

# Carrega o .env
load_dotenv('refference/.env')
api_key = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)

print("[DEBUG] Listando modelos ativos na conta:")
try:
    for m in client.models.list():
        # Apenas imprime o nome técnico, sem emojis para evitar erros de encoding no Windows
        print(f"NAME:{m.name}")
except Exception as e:
    print(f"ERRO: {e}")
