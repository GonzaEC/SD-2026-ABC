"""
Operador de Sobel - Proceso Distribuido
========================================
Aplica el operador de Sobel a una imagen para detección de bordes.

Uso:
    python splitter.py <imagen_entrada> [imagen_salida]

Ejemplo:
    python splitter.py foto.jpg foto_sobel.jpg
"""

import pika
import time
from fastapi import FastAPI
import uvicorn
import threading
import os
import logging
import sys
from PIL import Image
import io
import base64
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
WORKERS = 3
os.makedirs(LOG_DIR, exist_ok=True)
workers = []                    # Lista con todos los workers activos
lock_workers = threading.Lock() # Candado para la lista de workers
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
        "servicio": "splitter",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9000)





def main(): 
    # ── Validar argumentos ───────────────────────────────────────────────────
    if len(sys.argv) < 1:
        print(__doc__)
        sys.exit(1)

    input_path  = sys.argv[1]
    

    if not os.path.isfile(input_path):
        print(f"[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)
    
    
    # ── Procesar ─────────────────────────────────────────────────────────────
    print(f"Leyendo imagen:  {input_path}")
    image = Image.open(input_path)
    print(f"Tamaño:          {image.size[0]}×{image.size[1]} px  |  Modo: {image.mode}")
    threading.Thread(target=iniciar_api, daemon=True).start()

    # ── Dividir en partes ─────────────────────────────────────────────────────────────
    height = image.height
    fragmento_height = height // WORKERS
    # Conectar al broker
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Declarar la cola (durable=True para que sobreviva reinicios)
    channel.queue_declare(queue='tareas', durable=True)
    log.info("[Splitter] Enviando tareas...")
    # ── Obtener Fragmentos ─────────────────────────────────────────────────────────────
    for i in range(WORKERS):
        top = i * fragmento_height
        
        if i == WORKERS - 1:
            bottom = height
        else:
            bottom = (i + 1) * fragmento_height

        fragmento = image.crop((0, top, image.width, bottom))
        buffer = io.BytesIO()
        fragmento.save(buffer, format="PNG")
        img_bytes = base64.b64encode(buffer.getvalue()).decode()
        # ── Enviar Fragmentos ─────────────────────────────────────────────────────────────
        
        mensaje = {
            "indice": i,
            "imagen": img_bytes,
            "fragmentos": WORKERS,
        }
        channel.basic_publish(
            exchange='',           # exchange vacío = direct a la cola
            routing_key='tareas',  # nombre de la cola destino
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,   # mensaje persistente (sobrevive reinicios)
            )
        )
        log.info(f"[Splitter] Enviado a Worker: {i}")     

    connection.close()
    log.info("[Splitter] Todos los mensajes enviados.")
    

if __name__ == '__main__':
    main()
