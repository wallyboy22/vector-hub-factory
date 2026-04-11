import pdfplumber
import re
import os

def extract_pdf(path: str) -> list[dict]:
    """Extrai texto de cada página do PDF."""
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
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    return text

if __name__ == "__main__":
    import argparse
    from src.config import REPORTS
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="raf", choices=REPORTS.keys())
    args = parser.parse_args()
    
    cfg = REPORTS[args.report]
    docs = extract_pdf(cfg["pdf"])
    if docs:
        print(f"[{cfg['short']}] Páginas extraídas: {len(docs)}")
        print(f"Amostra (página 1):\n{docs[0]['text'][:200]}")
