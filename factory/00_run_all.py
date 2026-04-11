import os
import subprocess
import sys


def main():
    root = os.path.dirname(__file__)
    docs_dir = os.path.join(root, "..", "docs")
    
    if not os.path.exists(docs_dir):
        print("Pasta docs/ nao encontrada.")
        return
    
    for doc_id in os.listdir(docs_dir):
        doc_path = os.path.join(docs_dir, doc_id)
        if not os.path.isdir(doc_path):
            continue
        
        chunks_path = os.path.join(doc_path, "data", "chunks", "chunks.json")
        pdf_path = os.path.join(doc_path, f"{doc_id}.pdf")
        embeddings_dir = os.path.join(doc_path, "data", "embeddings", "gemini-embedding-001")
        index_path = os.path.join(embeddings_dir, "faiss.index")
        
        if not os.path.exists(pdf_path):
            print(f"[{doc_id}] PDF nao encontrado: {pdf_path}")
            continue
        
        if not os.path.exists(chunks_path):
            print(f"[{doc_id}] Gerando chunks...")
            cmd = [
                sys.executable,
                os.path.join(root, "01_chunk_pdf.py"),
                "--pdf", pdf_path,
                "--output", chunks_path
            ]
            subprocess.run(cmd, cwd=root)
        else:
            print(f"[{doc_id}] Chunks ja existem.")
        
        if not os.path.exists(index_path):
            print(f"[{doc_id}] Gerando embeddings...")
            cmd = [
                sys.executable,
                os.path.join(root, "02_01_embed_gemini.py"),
                "--chunks", chunks_path,
                "--output-dir", os.path.join(doc_path, "data", "embeddings")
            ]
            subprocess.run(cmd, cwd=root)
        else:
            print(f"[{doc_id}] Embeddings ja existem.")
    
    print("OK Processamento completo.")


if __name__ == "__main__":
    main()