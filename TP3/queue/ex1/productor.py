"""
Ejemplo 1 - Message Queue (Punto a Punto)
Productor: envía 10 tareas numeradas a la cola 'tareas'.

En Kubernetes:
- El productor se ejecuta como un Job.
- Envía los 10 mensajes una única vez y finaliza.
- Los mensajes quedan persistidos en RabbitMQ hasta ser consumidos.

Características implementadas:
- Cola durable.
- Mensajes persistentes.
- Reintento automático hasta que RabbitMQ esté disponible.
- Endpoint /health para verificación de estado durante ejecución.
"""

import pika
import time
from fastapi import FastAPI
import uvicorn
import threading
import os
import logging

# -------------------------
# LOGGING (MEMORIA + DISCO)
# -------------------------
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

# -------------------------
# VARIABLES DE ENTORNO
# -------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# -------------------------
# FASTAPI - HEALTH CHECK
# -------------------------
app = FastAPI()

@app.get("/health")
def health():
    return {
        "servicio": "productor",
        "status": "running",
        "rabbitmq": RABBITMQ_HOST
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9000)

# -------------------------
# CONEXIÓN CON REINTENTO
# -------------------------
def conectar_con_reintento():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            return connection
        except Exception as e:
            log.warning(f"RabbitMQ no disponible, reintentando en 3 segundos... {e}")
            time.sleep(3)

# -------------------------
# MAIN
# -------------------------
def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = conectar_con_reintento()
    channel = connection.channel()

    # Declarar cola durable
    channel.queue_declare(queue='tareas', durable=True)

    log.info("[Productor] Enviando tareas...")

    for i in range(1, 11):
        mensaje = f"Tarea #{i}: procesar item {i}"

        channel.basic_publish(
            exchange='',
            routing_key='tareas',
            body=mensaje,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        log.info(f"[Productor] Enviado: {mensaje}")
        time.sleep(0.2)

    connection.close()
    log.info("[Productor] Todos los mensajes enviados.")

if __name__ == '__main__':
    main()