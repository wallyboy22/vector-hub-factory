import os
import sys
from dotenv import load_dotenv

# Add root to path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

load_dotenv(os.path.join(root, '.env'))

from google import genai
from config import ALL_API_KEYS

print(f"Loaded keys found: {len(ALL_API_KEYS)}")
print(f"Keys list: {[k[:10] + '...' for k in ALL_API_KEYS]}")

for i, k in enumerate(ALL_API_KEYS):
    client = genai.Client(api_key=k)
    try:
        # Test with a simple embedding request
        client.models.embed_content(
            model="models/gemini-embedding-001",
            contents="test",
            config={"task_type": "RETRIEVAL_QUERY"}
        )
        print(f"Key {i}: VALID")
    except Exception as e:
        print(f"Key {i}: INVALID or EXHAUSTED - {e}")
