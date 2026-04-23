"""
Ejemplo 4 - Retry con Exponential Backoff
Productor: envía tareas a la cola principal.
"""

import pika
import json
import time
import logging
import os
import threading
from fastapi import FastAPI
import uvicorn

# LOGGING
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "productor.log")),
        logging.StreamHandler()
    ]
)
logging.getLogger("pika").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

# HEALTH ENDPOINT
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "service": "productor"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=9001)

TAREAS = [
    {"id": 1, "descripcion": "Llamada a API externa"},
    {"id": 2, "descripcion": "Escritura en base de datos"},
    {"id": 3, "descripcion": "Procesamiento de imagen"},
    {"id": 4, "descripcion": "Envío de email"},
    {"id": 5, "descripcion": "Sincronización con servicio externo"},
]

def main():
    threading.Thread(target=run_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    log.info("[Productor] Enviando tareas a 'cola_trabajo'...\n")

    for tarea in TAREAS:
        # Agregar metadata de retry al mensaje
        tarea['intentos'] = 0
        tarea['max_intentos'] = 4

        body = json.dumps(tarea)
        channel.basic_publish(
            exchange='retry_exchange',
            routing_key='trabajo',
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        log.info(f"[Productor] Enviada: Tarea #{tarea['id']} - {tarea['descripcion']}")
        time.sleep(0.3)

    connection.close()
    log.info("[Productor] Fin envio")

if __name__ == '__main__':
    main()
