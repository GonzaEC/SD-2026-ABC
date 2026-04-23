"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Productor: envía mensajes a la cola principal, algunos con "error": true.
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
        logging.FileHandler(os.path.join(LOG_DIR, "productor.log")),
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
        "servicio": "productor",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9000)

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

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    log.info("[Productor ]Enviando mensajes a 'cola_principal'...")

    for msg in MENSAJES:
        body = json.dumps(msg)
        channel.basic_publish(
            exchange='',
            routing_key='cola_principal',
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        estado = "CON ERROR" if msg["error"] else "OK"
        log.info(f"[Productor ]Enviado: ID={msg['id']}, {estado}")

    connection.close()
    log.info("[Productor ]Todos los mensajes enviados.")

if __name__ == '__main__':
    main()
