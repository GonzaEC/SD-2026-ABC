"""
Suscriptor - Patrón Pub/Sub con exchange FANOUT (Kubernetes)

Cada pod representa un nodo distinto.
Todos reciben los mismos mensajes del exchange FANOUT.

En Kubernetes:
- Se usa hostname del pod para identificar nodo
- RabbitMQ se accede por service "rabbitmq"
"""

import pika
import json
import threading
import os
import logging
from fastapi import FastAPI
import uvicorn
import time

# -------------------------
# CONFIG K8S
# -------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
EXCHANGE = "fanout_test"

# Identidad del pod (Kubernetes)
NODO = os.getenv("HOSTNAME", "nodo")

# Puerto dinámico solo para health check
PUERTO = 8000

# -------------------------
# LOGGING
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f"{NODO}.log")),
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
    return {
        "servicio": NODO,
        "status": "running",
        "rabbitmq": RABBITMQ_HOST
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=PUERTO)

# -------------------------
# CONEXIÓN CON RETRY
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
# CALLBACK
# -------------------------
def callback(ch, method, properties, body):
    mensaje = json.loads(body)
    log.info(f"[{NODO}] Recibido: {mensaje}")

# -------------------------
# MAIN
# -------------------------
def main():
    threading.Thread(target=iniciar_api, daemon=True).start()
    time.sleep(5)
    connection = conectar()
    channel = connection.channel()

    # Exchange FANOUT
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="fanout"
    )

    # Cola exclusiva por pod
    result = channel.queue_declare(queue="", exclusive=True)
    cola = result.method.queue

    # Bind al exchange
    channel.queue_bind(
        exchange=EXCHANGE,
        queue=cola
    )

    log.info(f"[{NODO}] Esperando mensajes...")

    channel.basic_consume(
        queue=cola,
        on_message_callback=callback,
        auto_ack=True
    )

    channel.start_consuming()

if __name__ == "__main__":
    main()