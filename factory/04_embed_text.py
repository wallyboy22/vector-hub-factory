import argparse
import os
import sys

from google import genai


def load_api_key():
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", "references", "mapbiomas-chat", "refference", ".env")
    load_dotenv(env_path)
    return os.getenv("GOOGLE_API_KEY")


EMBEDDING_MODEL = "models/gemini-embedding-001"


def embed_text(text: str, api_key: str) -> list[float]:
    client = genai.Client(api_key=api_key)
    resp = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config={"task_type": "RETRIEVAL_DOCUMENT"}
    )
    return list(resp.embeddings[0].values)


def main():
    parser = argparse.ArgumentParser(description="Embedding de texto demo")
    parser.add_argument("--text", required=True, help="Texto para embedding")
    parser.add_argument("--model", default="gemini", help="Modelo (gemini)")
    parser.add_argument("--api-key", help="Chave da API (opcional)")
    args = parser.parse_args()
    
    api_key = args.api_key or load_api_key()
    if not api_key:
        print("Erro: GOOGLE_API_KEY nao encontrada.")
        sys.exit(1)
    
    vector = embed_text(args.text, api_key)
    print(f"Dimensão: {len(vector)}")
    print(f"Primeiros 10 valores: {vector[:10]}")
    print(f"Modelo usado: {EMBEDDING_MODEL}")


if __name__ == "__main__":
    main()