"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Consumidor principal: procesa mensajes de 'cola_principal'.
- Si el mensaje tiene "error": false → ACK (procesado exitosamente)
- Si el mensaje tiene "error": true  → NACK sin requeue → va a la DLQ automáticamente
"""

import pika
import json
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
        logging.FileHandler(os.path.join(LOG_DIR, "consumidor.log")),
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
        "servicio": "consumidor_principal",
        "status": "running",
        "rabbitmq": "connected"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=8001)

def procesar(ch, method, properties, body):
    msg = json.loads(body.decode())
    log.info(f"\n[Consumidor] Recibido: {msg}")

    if msg.get("error"):
        log.warning(f"[Consumidor] Mensaje ID={msg['id']} tiene error. Rechazando a DLQ")

        # requeue=False: no volver a encolar aquí, el DLX lo redirige a la DLQ
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        log.info(f"[Consumidor] Mensaje ID={msg['id']} procesado correctamente.")

        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue='cola_principal',
        on_message_callback=procesar,
        auto_ack=False
    )

    log.info("[Consumidor ]Health: http://localhost:8001/health")
    log.info("[Consumidor] Escuchando 'cola_principal'. Ctrl+C para salir.")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n [Consumidor] Detenido. ")
