"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Consumidor principal:
- error: false → ACK
- error: true → NACK sin requeue → va a DLQ
"""

import pika
import json
import logging
import os
import threading
import time
from fastapi import FastAPI
import uvicorn

# -------------------------
# CONFIG K8S
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
        logging.FileHandler(os.path.join(LOG_DIR, "consumidor.log")),
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
        "servicio": "consumidor_principal",
        "status": "running",
        "rabbitmq": RABBITMQ_HOST
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=8001)

# -------------------------
# RETRY CONEXIÓN
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
# PROCESAMIENTO
# -------------------------
def procesar(ch, method, properties, body):
    msg = json.loads(body.decode())

    log.info(f"[Consumidor] Recibido: {msg}")

    if msg.get("error"):
        log.warning(f"[Consumidor] ERROR en ID={msg['id']} → enviando a DLQ")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        log.info(f"[Consumidor] OK ID={msg['id']} procesado")
        ch.basic_ack(delivery_tag=method.delivery_tag)

# -------------------------
# MAIN
# -------------------------
def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = conectar()
    channel = connection.channel()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue='cola_principal',
        on_message_callback=procesar,
        auto_ack=False
    )

    log.info("[Consumidor] Escuchando cola_principal...")
    channel.start_consuming()

if __name__ == "__main__":
    main()