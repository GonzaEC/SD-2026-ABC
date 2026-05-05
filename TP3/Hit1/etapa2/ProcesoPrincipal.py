"""
Operador de Sobel Master-Worker  - Proceso Distribuido
========================================
Aplica el operador de Sobel a fragmentos de una imagen y las unifica para detección de bordes.

Uso:
    python ProcesoPrincipal.py <PATH_IMAGEN> <PATH_OUTPUT>

Ejemplo:
    python ProcesoPrincipal.py /TP3/Hit1/FondoCristiano.jpg output.jpg
"""
import sys
import os
import subprocess
from joiner import main
from splitter import main
import logging
import threading
from fastapi import FastAPI
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "ProcesoPrincipal.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

app = FastAPI()
@app.get("/health")
def health():
    return {
        "splitter": "running",
        "joiner": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9012)

def build_output_path(input_path: str) -> str:
    """Genera el nombre de salida agregando '_sobel' antes de la extensión."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_sobel{ext if ext else '.png'}"

def main(): 
    # ── Validar argumentos ───────────────────────────────────────────────────
    if len(sys.argv) < 2:
        log.info(__doc__)
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else build_output_path(input_path)

    if not os.path.isfile(input_path):
        log.info(f"[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)
    threading.Thread(target=iniciar_api, daemon=True).start()

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