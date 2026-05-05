"""
Publicador - Patrón Pub/Sub con exchange FANOUT (Kubernetes)

Este servicio publica eventos de "nuevo_bloque" en un exchange FANOUT.

En Kubernetes:
- RabbitMQ se accede por Service: "rabbitmq"
- El pod puede arrancar antes que RabbitMQ → se usa reintento de conexión
"""

import pika
import json
import time
import threading
import os
import logging
from fastapi import FastAPI
import uvicorn

# -------------------------
# CONFIG RABBITMQ (K8S)
# -------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
EXCHANGE = "fanout_test"

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
        logging.FileHandler(os.path.join(LOG_DIR, "publicador.log")),
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
        "servicio": "publicador_fanout",
        "status": "running",
        "rabbitmq": RABBITMQ_HOST
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9100)

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
# MAIN
# -------------------------
def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = conectar()
    channel = connection.channel()

    # Exchange FANOUT (broadcast a todos los suscriptores)
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="fanout"
    )

    log.info("[PUBLICADOR] Enviando eventos...")

    for i in range(1, 6):
        mensaje = {
            "evento": "nuevo_bloque",
            "numero": i
        }

        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key="",
            body=json.dumps(mensaje)
        )

        log.info(f"[PUBLICADOR] Enviado: {mensaje}")
        time.sleep(1)

    connection.close()
    log.info("[PUBLICADOR] Finalizado.")

if __name__ == "__main__":
    main()