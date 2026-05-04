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
app = FastAPI()
os.makedirs(LOG_DIR, exist_ok=True)
workers = []                    # Lista con todos los workers activos
lock_workers = threading.Lock() # Candado para la lista de workers
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

class SplitterM:

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(LOG_DIR, "splitter.log")),
            logging.StreamHandler()
        ]
    )
    

    
    @app.get("/health")
    def health():
        return {
            "servicio": "splitter",
            "status": "running"
        }

    def iniciar_api(self):
        uvicorn.run(app, host="0.0.0.0", port=9000)



    def __init__(self, tareas, publicaciones):
            self.tareas = tareas        # referencia compartida
            self.publicaciones = publicaciones
    def procesar(self,imagen:Image): 
    
        threading.Thread(target=self.iniciar_api, daemon=True).start()

        # ── Dividir en partes ─────────────────────────────────────────────────────────────
        height = imagen.height
        fragmento_height = height // WORKERS
        # Conectar al broker
        
        log.info("[Splitter] Enviando tareas...")
        # ── Obtener Fragmentos ─────────────────────────────────────────────────────────────
        for i in range(WORKERS):
            top = i * fragmento_height
            
            if i == WORKERS - 1:
                bottom = height
            else:
                bottom = (i + 1) * fragmento_height

            fragmento = imagen.crop((0, top, imagen.width, bottom))
            buffer = io.BytesIO()
            fragmento.save(buffer, format="PNG")
            img_bytes = base64.b64encode(buffer.getvalue()).decode()
            # ── Enviar Fragmentos ─────────────────────────────────────────────────────────────
            
            mensaje = {
                "indice": i,
                "imagen": img_bytes,
                "fragmentos": WORKERS,
            }
            self.tareas[i] = {
                "t0": time.time(),
                "estado": "pendiente",
                "payload": mensaje
            }
            self.publicaciones.put(mensaje)     

        
        log.info("[Splitter] Todos los mensajes encolados.")
        

