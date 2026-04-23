"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Consumidor DLQ: lee e imprime los mensajes que fallaron y fueron redirigidos
a la 'cola_muertos'. Permite auditoría, alertas o reprocesamiento manual.
"""

import pika
import json
import time
import logging
import os
from fastapi import FastAPI
import uvicorn
import threading

# LOGGING
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "dlq.log")),
        logging.StreamHandler()
    ]
)

logging.getLogger("pika").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

# FASTAPI
app = FastAPI()

@app.get("/health")
def health():
    return {
        "servicio": "consumidor_dlq",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=8002)


def auditar_fallido(ch, method, properties, body):
    msg = json.loads(body.decode())
    timestamp = time.strftime('%H:%M:%S')
    log.error("[DLQ Auditor] ===============================")
    log.error(f"[DLQ Auditor] Mensaje fallido: ID={msg['id']}, Contenido: {msg['contenido']}")
    log.error("[DLQ Auditor] ===============================")

    # ACK: el mensaje de auditoría fue procesado (no volver a encolar)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue='cola_muertos',
        on_message_callback=auditar_fallido,
        auto_ack=False
    )

    log.info("[DLQ Auditor ]Health: http://localhost:8002/health")
    log.info("[DLQ Auditor] Monitoreando 'cola_muertos' (DLQ). Ctrl+C para salir.\n")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n[DLQ Auditor] Detenido.")
