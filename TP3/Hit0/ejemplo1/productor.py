"""
Ejemplo 1 - Message Queue (Punto a Punto)
Productor: envía 10 tareas numeradas a la cola 'tareas'.
"""

import pika
import time
from fastapi import FastAPI
import uvicorn
import threading
import os
import logging

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

app = FastAPI()
@app.get("/health")
def health():
    return {
        "servicio": "productor",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9000)

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    # Conectar al broker
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Declarar la cola (durable=True para que sobreviva reinicios)
    channel.queue_declare(queue='tareas', durable=True)

    log.info("[Productor] Enviando tareas...")
    #print("[Productor] Enviando 10 tareas a la cola 'tareas'...")

    for i in range(1, 11):
        mensaje = f"Tarea #{i}: procesar item {i}"
        channel.basic_publish(
            exchange='',           # exchange vacío = direct a la cola
            routing_key='tareas',  # nombre de la cola destino
            body=mensaje,
            properties=pika.BasicProperties(
                delivery_mode=2,   # mensaje persistente (sobrevive reinicios)
            )
        )
        log.info(f"[Productor] Enviado: {mensaje}")
        #print(f"[Productor] Enviado: '{mensaje}'")
        time.sleep(0.2)  # pequeña pausa para visualizar el envío

    connection.close()
    log.info("[Productor] Todos los mensajes enviados.")
    #print("[Productor] Todos los mensajes enviados. Conexión cerrada.")

if __name__ == '__main__':
    main()
