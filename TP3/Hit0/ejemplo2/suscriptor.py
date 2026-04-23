"""
Suscriptor - Patrón Pub/Sub con exchange FANOUT

Cada instancia de este programa representa un nodo distinto.
Cada nodo crea su propia cola exclusiva y se vincula al exchange.

IMPORTANTE:
- Ejecutar 3 instancias en terminales distintas:
    python suscriptor.py nodo1
    python suscriptor.py nodo2
    python suscriptor.py nodo3

Cada suscriptor recibirá TODOS los mensajes publicados.
"""

import pika
import json
import sys
import threading
import os
import logging

from fastapi import FastAPI
import uvicorn

EXCHANGE = 'fanout_test'

# Identificador del nodo (ej: nodo1, nodo2, nodo3)
NODO = sys.argv[1] if len(sys.argv) > 1 else "nodo"

# Extraer número del nodo (nodo1 → 1)
try:
    NUM_NODO = int(NODO.replace("nodo", ""))
except:
    NUM_NODO = 1  # fallback

PUERTO = 8000 + NUM_NODO

# LOGGING
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f"{NODO}.log")),
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
        "servicio": NODO,
        "status": "running",
        "exchange": EXCHANGE
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=PUERTO)

def procesar_mensaje(body, nodo):
    mensaje = json.loads(body)
    return f"[{nodo}] Recibido: {mensaje}"

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    # Conexión a RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    # Declarar el mismo exchange que el publicador
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type='fanout'
    )

    # Crear cola exclusiva (una por suscriptor)
    # queue='' => nombre automático
    # exclusive=True => se elimina al cerrar el proceso
    result = channel.queue_declare(queue='', exclusive=True)
    cola = result.method.queue

    # Vincular cola al exchange
    channel.queue_bind(
        exchange=EXCHANGE,
        queue=cola
    )

    # Función que procesa cada mensaje recibido
    def callback(ch, method, properties, body):
        resultado = procesar_mensaje(body, NODO)
        log.info(resultado)

    # Consumidor
    channel.basic_consume(
        queue=cola,
        on_message_callback=callback,
        auto_ack=True
    )

    #print(f"[{NODO}] Esperando mensajes...\n")
    log.info(f"[{NODO}] Health: http://localhost:{PUERTO}/health")
    log.info(f"[{NODO}] Esperando mensajes...\n")

    # Espera infinita de mensajes
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        #print(f"\n[{NODO}] Desconectado.")
        log.info(f"[{NODO}] Desconectado.")