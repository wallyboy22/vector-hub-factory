import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Gerar embeddings (genérico)")
    parser.add_argument("--chunks", required=True, help="Caminho do chunks.json")
    parser.add_argument("--model", default="gemini", choices=["gemini"], help="Modelo de embedding")
    parser.add_argument("--output-dir", required=True, help="Diretorio de saida")
    parser.add_argument("--api-key", help="Chave da API (opcional)")
    args = parser.parse_args()

    if args.model == "gemini":
        script = "02_01_embed_gemini.py"
    else:
        print(f"Modelo '{args.model}' ainda nao implementado.")
        sys.exit(1)

    cmd = [
        sys.executable,
        script,
        "--chunks", args.chunks,
        "--output-dir", args.output_dir
    ]
    if args.api_key:
        cmd.extend(["--api-key", args.api_key])

    result = subprocess.run(cmd, cwd=__file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()