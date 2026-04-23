"""
Publicador - Patrón Pub/Sub con exchange FANOUT

Este programa envía eventos de "nuevo_bloque" a un exchange fanout.
El exchange se encarga de duplicar el mensaje y enviarlo a todas
las colas vinculadas (una por cada suscriptor).
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
# LOGGING
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "publicador.log")),
        logging.StreamHandler()
    ]
)
logging.getLogger("pika").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

# -------------------------
# FASTAPI
# -------------------------
app = FastAPI()

@app.get("/health")
def health():
    return {
        "servicio": "publicador_fanout",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9100)

EXCHANGE = 'fanout_test'

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    # Conexión a RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    # Declaración del exchange tipo fanout
    # fanout => ignora routing_key y envía el mensaje a TODAS las colas
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type='fanout'
    )

    log.info("[PUBLICADOR] Enviando eventos...")
    # print("[PUBLICADOR] Enviando eventos...\n")

    # Enviar 5 eventos de ejemplo
    for i in range(1, 6):
        mensaje = {
            "evento": "nuevo_bloque",
            "numero": i
        }

        # Publicación del mensaje
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key='',  # no se usa en fanout
            body=json.dumps(mensaje)
        )

        log.info(f"[PUBLICADOR] Enviado: {mensaje}")
        #print(f"[PUBLICADOR] Enviado: {mensaje}")
        time.sleep(1)

    connection.close()
    #print("\n[PUBLICADOR] Finalizado.")
    log.info("[PUBLICADOR] Finalizado.")

if __name__ == '__main__':
    main()