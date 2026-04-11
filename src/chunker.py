import json
import os
from src.config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_doc(doc: dict) -> list[dict]:
    words = doc["text"].split()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        piece = words[i : i + CHUNK_SIZE]
        if len(piece) < 20:
            continue
        chunks.append({
            "content": " ".join(piece),
            "page": doc["page"],
            "chunk_id": f"p{doc['page']}_c{len(chunks)}"
        })
    return chunks

def chunk_all(docs: list[dict]) -> list[dict]:
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_doc(doc))
    return all_chunks

def save_chunks(chunks: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    from src.config import REPORTS
    from src.ingest import extract_pdf
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="raf", choices=REPORTS.keys())
    args = parser.parse_args()
    
    cfg = REPORTS[args.report]
    docs = extract_pdf(cfg["pdf"])
    if docs:
        chunks = chunk_all(docs)
        save_chunks(chunks, cfg["chunks"])
        print(f"[{cfg['short']}] Chunks gerados: {len(chunks)}")
