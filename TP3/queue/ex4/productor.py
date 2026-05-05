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

# -------------------------
# CONFIG KUBERNETES
# -------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# -------------------------
# LOGGING
# -------------------------
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

log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

# -------------------------
# FASTAPI
# -------------------------
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "service": "productor"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=9001)

# -------------------------
# CONEXIÓN ROBUSTA
# -------------------------
def conectar():
    while True:
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
        except Exception as e:
            log.warning(f"[Productor] Esperando RabbitMQ... {e}")
            time.sleep(3)

# -------------------------
# TAREAS
# -------------------------
TAREAS = [
    {"id": 1, "descripcion": "Llamada a API externa"},
    {"id": 2, "descripcion": "Escritura en DB"},
    {"id": 3, "descripcion": "Procesamiento imagen"},
    {"id": 4, "descripcion": "Envio email"},
    {"id": 5, "descripcion": "Sync externo"},
]

# -------------------------
# MAIN
# -------------------------
def main():
    threading.Thread(target=run_api, daemon=True).start()

    connection = conectar()
    channel = connection.channel()

    log.info("[Productor] Enviando tareas...")

    for tarea in TAREAS:
        tarea["intentos"] = 0
        tarea["max_intentos"] = 4

        channel.basic_publish(
            exchange='retry_exchange',
            routing_key='trabajo',
            body=json.dumps(tarea),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        log.info(f"[Productor] Enviada tarea {tarea['id']}")
        time.sleep(0.3)

    connection.close()
    log.info("[Productor] FIN")

if __name__ == "__main__":
    main()