"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Productor: envía mensajes a la cola principal, algunos con "error": true.
"""

import pika
import json
import logging
import os
import time
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
# FASTAPI (health check)
# -------------------------
app = FastAPI()

@app.get("/health")
def health():
    return {
        "servicio": "productor",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9000)

# -------------------------
# CONEXIÓN CON RETRY (K8S)
# -------------------------
def conectar():
    while True:
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
        except Exception as e:
            log.warning(f"RabbitMQ no disponible, reintentando... {e}")
            time.sleep(3)

# -------------------------
# MENSAJES
# -------------------------
MENSAJES = [
    {"id": 1, "contenido": "Transacción válida #1",    "error": False},
    {"id": 2, "contenido": "Transacción corrupta #2",  "error": True},
    {"id": 3, "contenido": "Transacción válida #3",    "error": False},
    {"id": 4, "contenido": "Registro inválido #4",     "error": True},
    {"id": 5, "contenido": "Transacción válida #5",    "error": False},
    {"id": 6, "contenido": "Dato malformado #6",       "error": True},
    {"id": 7, "contenido": "Transacción válida #7",    "error": False},
    {"id": 8, "contenido": "Transacción válida #8",    "error": False},
]

# -------------------------
# MAIN
# -------------------------
def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = conectar()
    channel = connection.channel()

    log.info("[Productor] Enviando mensajes a 'cola_principal'...")

    for msg in MENSAJES:
        body = json.dumps(msg)

        channel.basic_publish(
            exchange='',
            routing_key='cola_principal',
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        estado = "CON ERROR" if msg["error"] else "OK"
        log.info(f"[Productor] Enviado: ID={msg['id']}, {estado}")

        time.sleep(1)

    connection.close()
    log.info("[Productor] Todos los mensajes enviados.")

if __name__ == "__main__":
    main()