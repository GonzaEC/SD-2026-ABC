"""
Ejemplo 4 - Retry con Exponential Backoff
Consumidor con fallback a DLQ
"""

import pika
import json
import random
import time
import logging
import threading
import os
from fastapi import FastAPI
import uvicorn

# -------------------------
# KUBERNETES CONFIG
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
    return {"status": "ok", "service": "consumidor-retry"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8003)

# -------------------------
# CONFIG
# -------------------------
DELAYS = [1, 2, 4, 8]
MAX_INTENTOS = 4

# -------------------------
# SIMULACION FALLA
# -------------------------
def procesar_ok():
    return random.random() > 0.5

# -------------------------
# RETRY
# -------------------------
def enviar_retry(channel, msg, intento):
    delay = DELAYS[intento - 1]
    cola = f"cola_espera_{delay}s"

    msg["intentos"] = intento

    log.warning(f"[Retry] intento {intento} = espera {delay}s")

    channel.basic_publish(
        exchange='',
        routing_key=cola,
        body=json.dumps(msg),
        properties=pika.BasicProperties(delivery_mode=2)
    )

# -------------------------
# DLQ FINAL
# -------------------------
def enviar_dlq(channel, msg):
    log.error(f"[DLQ] mensaje {msg['id']} final")

    channel.basic_publish(
        exchange='retry_dlx',
        routing_key='muerto',
        body=json.dumps(msg),
        properties=pika.BasicProperties(delivery_mode=2)
    )

# -------------------------
# CONSUMO PRINCIPAL
# -------------------------
def callback(ch, method, properties, body):
    msg = json.loads(body.decode())

    intento = msg.get("intentos", 0) + 1

    log.info(f"[Task {msg['id']}] intento {intento}")

    if procesar_ok():
        log.info("OK")
        ch.basic_ack(method.delivery_tag)
    else:
        log.warning("FALLO")

        if intento < MAX_INTENTOS:
            enviar_retry(ch, msg, intento)
        else:
            enviar_dlq(ch, msg)

        ch.basic_ack(method.delivery_tag)

# -------------------------
# MAIN
# -------------------------
def main():
    threading.Thread(target=run_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )

    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue="cola_trabajo",
        on_message_callback=callback,
        auto_ack=False
    )

    log.info("[Consumidor] iniciado")
    channel.start_consuming()

if __name__ == "__main__":
    main()