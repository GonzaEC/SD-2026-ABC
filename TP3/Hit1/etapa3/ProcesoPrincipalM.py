import sys
import os
import subprocess
from PIL import Image
from fastapi import FastAPI
import uvicorn
import threading
import os
import logging
import sys
from PIL import Image
import io
import pika
import json
from splitterM import SplitterM
from joinerM import JoinerM
import time
from pathlib import Path
import queue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
TIMEOUT = 30
tareas = {}
cola_publicaciones = queue.Queue()



os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "splitter.log")),
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

def build_output_path(input_path: str) -> str:
    """Genera el nombre de salida agregando '_sobel' antes de la extensión."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_sobel{ext if ext else '.png'}"



def main(): 
    # ── Validar argumentos ───────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_path  = Path(sys.argv[1]).resolve()
    output_path = sys.argv[2] if len(sys.argv) >= 3 else build_output_path(input_path)
    
    
    if not input_path.is_file():
        print(f"[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)
    
    
    # ── Procesar ─────────────────────────────────────────────────────────────
    print(f"Leyendo imagen:  {input_path}")
    image = Image.open(input_path)
    print(f"Tamaño:          {image.size[0]}×{image.size[1]} px  |  Modo: {image.mode}")
    
    try:
        #iniciamos el splitter 
        splitter = SplitterM(tareas, cola_publicaciones)
        threading.Thread(target=splitter_publicar, daemon=True).start()

        #iniciamos el joiner
        joiner = JoinerM(tareas,output_path)
        threading.Thread(target=joiner.main,  daemon=False).start()

        #iniciamos el loop del proceso principal
        threading.Thread(target=loop, daemon=True).start()

        #iniciamos el splitter
        splitter.procesar(image)
    except KeyboardInterrupt:
        log.info("Interrupcion por teclado, cerrando...")
    
    

def loop():
    while True:
        for i, t in list(tareas.items()):
            if t["estado"] == "pendiente" and time.monotonic() - t["t0"] > TIMEOUT:
                cola_publicaciones.put(t["payload"]) #se reenvia el fragmento
                t["t0"] = time.monotonic()
                log.info(f"[Splitter] Reenviando tarea {i}")
        time.sleep(1)

def splitter_publicar():
    #establecemos la conexion del splitter con rabbitMQ
    credencial= pika.PlainCredentials("sobel_user", "sobel_pass")
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost',
                                port = 5672,
                                credentials=credencial)
    )
    
    channel = connection.channel()
    # Declarar la cola (durable=True para que sobreviva reinicios)
    channel.queue_declare(queue='tareas', durable=True)

    while True:
        try:
            payload = cola_publicaciones.get(timeout=1)

            channel.basic_publish(
                    exchange='',           # exchange vacío = direct a la cola
                    routing_key='tareas',  # nombre de la cola destino
                    body=json.dumps(payload),
                    properties=pika.BasicProperties(
                        delivery_mode=2,   # mensaje persistente (sobrevive reinicios)
                    )
                )
            
            log.info(f"[Splitter] Enviado a Worker")
        except queue.Empty:
            pass
        
    

if __name__ == '__main__':
    main()