"""
Ejemplo 1 - Message Queue (Punto a Punto)
Consumidor: recibe tareas de la cola 'tareas' y las procesa.

En Kubernetes:
- Se despliegan 2 réplicas del consumidor.
- RabbitMQ distribuye automáticamente los mensajes entre ambas instancias.
- Cada mensaje es procesado exactamente por un solo consumidor.

Características implementadas:
- ACK manual para confirmar procesamiento exitoso.
- prefetch_count=1 para fair dispatch (round-robin equilibrado).
- Reintento automático hasta que RabbitMQ esté disponible.
- Endpoint /health para verificación de estado.
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
        logging.FileHandler(os.path.join(LOG_DIR, "consumidor.log")),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

# -------------------------
# VARIABLES DE ENTORNO
# -------------------------
# RabbitMQ será accedido por el nombre del Service de Kubernetes
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# HOSTNAME identifica automáticamente cada pod consumidor
WORKER_ID = os.getenv("HOSTNAME", "?")

# -------------------------
# FASTAPI - HEALTH CHECK
# -------------------------
app = FastAPI()

@app.get("/health")
def health():
    return {
        "servicio": f"consumidor_{WORKER_ID}",
        "status": "running",
        "rabbitmq": RABBITMQ_HOST
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# -------------------------
# PROCESAMIENTO DE MENSAJES
# -------------------------
def procesar_mensaje(ch, method, properties, body):
    mensaje = body.decode()
    log.info(f"[Consumidor {WORKER_ID}] Recibido: {mensaje}")

    # Simular tiempo de trabajo
    time.sleep(1)

    log.info(f"[Consumidor {WORKER_ID}] Procesado: {mensaje}")

    # Confirmar a RabbitMQ que el mensaje fue procesado correctamente
    ch.basic_ack(delivery_tag=method.delivery_tag)

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

    # Fair dispatch: un mensaje a la vez por consumidor hasta ACK
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue='tareas',
        on_message_callback=procesar_mensaje,
        auto_ack=False
    )

    log.info(f"[Consumidor {WORKER_ID}] Esperando mensajes...")
    channel.start_consuming()

if __name__ == '__main__':
    main()