import sys
import os
import subprocess
from joiner import main
from splitter import main

def build_output_path(input_path: str) -> str:
    """Genera el nombre de salida agregando '_sobel' antes de la extensión."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_sobel{ext if ext else '.png'}"

def main(): 
    # ── Validar argumentos ───────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else build_output_path(input_path)

    if not os.path.isfile(input_path):
        print(f"[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)

    #iniciamos el joiner
    procesoJoiner = subprocess.Popen(
        ["python", "joiner.py", output_path]
    )
    #iniciamos el splitter
    procesoSplitter = subprocess.Popen(
        ["python", "splitter.py", input_path]
    )


    
    

if __name__ == '__main__':
    main()