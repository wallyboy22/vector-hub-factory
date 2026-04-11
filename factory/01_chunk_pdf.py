import argparse
import json
import os
import re

import pdfplumber


def extract_pdf(path: str) -> list[dict]:
    docs = []
    if not os.path.exists(path):
        print(f"Erro: PDF não encontrado em {path}")
        return []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text = _clean(text)
            if text.strip():
                docs.append({"text": text, "page": i + 1})
    return docs


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_doc(text: str, page_num: int, chunk_size: int, overlap: int) -> list[dict]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        piece = words[i : i + chunk_size]
        if len(piece) < 20:
            continue
        chunks.append({
            "content": " ".join(piece),
            "page": page_num,
            "chunk_id": f"p{page_num}_c{len(chunks)}"
        })
    return chunks


def chunk_all(docs: list[dict], chunk_size: int, overlap: int) -> list[dict]:
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_doc(doc["text"], doc["page"], chunk_size, overlap))
    return all_chunks


def save_chunks(chunks: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Chunk PDF em texto")
    parser.add_argument("--pdf", required=True, help="Caminho do PDF")
    parser.add_argument("--output", required=True, help="Caminho de saída do chunks.json")
    parser.add_argument("--chunk-size", type=int, default=700, help="Tamanho do chunk")
    parser.add_argument("--overlap", type=int, default=100, help="Sobreposição")
    args = parser.parse_args()

    docs = extract_pdf(args.pdf)
    if not docs:
        return

    chunks = chunk_all(docs, args.chunk_size, args.overlap)
    save_chunks(chunks, args.output)
    print(f"OK {len(chunks)} chunks gerados em {args.output}")


if __name__ == "__main__":
    main()