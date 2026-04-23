"""
Ejemplo 1 - Message Queue (Punto a Punto)
Consumidor: recibe tareas de la cola 'tareas' y las procesa.

Uso:
  python consumidor.py          → consumidor sin identificador
  python consumidor.py A        → consumidor identificado como "A"
  python consumidor.py B        → consumidor identificado como "B"

Levantar 2 instancias en terminales distintas para observar round-robin:
  Terminal 1: python consumidor.py A
  Terminal 2: python consumidor.py B
  Luego ejecutar el productor y observar cómo se distribuyen los mensajes.
"""

import pika
import time
import sys
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
# FASTAPI
# -------------------------
app = FastAPI()

@app.get("/health")
def health():
    return {
        "servicio": f"consumidor_{WORKER_ID}",
        "status": "running",
        "rabbitmq": "connected"
    }

def iniciar_api():
    puerto = 8000 + int(WORKER_ID)
    uvicorn.run(app, host="0.0.0.0", port=puerto)

# Identificador opcional para distinguir instancias
WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "?"

def procesar_mensaje(ch, method, properties, body):
    mensaje = body.decode()
    log.info(f"[Consumidor {WORKER_ID}] Recibido: {mensaje}")
    # print(f"[Consumidor {WORKER_ID}] Recibido: '{mensaje}'")

    # Simular trabajo (tiempo de procesamiento)
    time.sleep(1)
    log.info(f"[Consumidor {WORKER_ID}] Procesado: {mensaje}")
    #print(f"[Consumidor {WORKER_ID}]  Procesado: '{mensaje}'")

    # Confirmar que el mensaje fue procesado correctamente (ACK manual)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Declarar la misma cola que el productor (idempotente)
    channel.queue_declare(queue='tareas', durable=True)

    # prefetch_count=1: no enviar más de 1 mensaje a este worker hasta recibir ACK
    # Esto asegura distribución justa (fair dispatch) entre múltiples consumidores
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue='tareas',
        on_message_callback=procesar_mensaje,
        auto_ack=False  # ACK manual para mayor control
    )

    log.info(f"[Consumidor {WORKER_ID}] Health: http://localhost:{8000 + int(WORKER_ID)}/health")
    #print(f"[Consumidor {WORKER_ID}] Health: http://localhost:{8000 + int(WORKER_ID)}/health")
    log.info(f"[Consumidor {WORKER_ID}] Esperando mensajes...")
    #print(f"[Consumidor {WORKER_ID}] Esperando mensajes...")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info(f"[Consumidor {WORKER_ID}] Detenido.")
        #print(f"\n[Consumidor {WORKER_ID}] Detenido.")
