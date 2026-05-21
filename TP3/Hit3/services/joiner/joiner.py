"""
Hit3 - Joiner Service
Consume resultados de 'resultados_joiner' (cola bound al fanout exchange).
Cuando recibe todos los fragmentos de un job, reconstruye la imagen y la guarda en Redis.

Cambio respecto a Hit1/Hit2:
  - Consume de 'resultados_joiner' (suscripto al fanout 'resultados_exchange')
    en lugar de la cola 'resultado' directa.
  - Guarda el resultado en Redis keyed por job_id.
"""

import pika
import time
import threading
import os
import logging
import json
import base64
import io
import redis
from fastapi import FastAPI
import uvicorn
from PIL import Image

RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_USER = os.environ["RABBITMQ_USER"]
RABBITMQ_PASS = os.environ["RABBITMQ_PASS"]
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

BACKOFF_DELAYS = [1, 2, 4, 8, 30]

LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "joiner.log")),
    ],
)
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# Almacena fragmentos en memoria por job_id: { job_id: [msg1, msg2, ...] }
fragmentos_por_job: dict[str, list] = {}

app = FastAPI()


@app.get("/health")
def health():
    return {"servicio": "joiner", "status": "running"}


def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9001)


def conectar_rabbit():
    for delay in BACKOFF_DELAYS:
        try:
            credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=5672, credentials=credenciales
                )
            )
            log.info("[Joiner] Conectado a RabbitMQ.")
            return conn
        except pika.exceptions.AMQPConnectionError:
            log.warning(f"[Joiner] RabbitMQ no disponible, reintentando en {delay}s...")
            time.sleep(delay)
    while True:
        try:
            credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=5672, credentials=credenciales
                )
            )
        except pika.exceptions.AMQPConnectionError:
            log.warning("[Joiner] RabbitMQ no disponible, reintentando en 30s...")
            time.sleep(30)


def calcular_height(fragmentos: list) -> int:
    total = 0
    for f in fragmentos:
        img_bytes = base64.b64decode(f["resultado"])
        img = Image.open(io.BytesIO(img_bytes))
        total += img.height
    return total


def reconstruir_imagen(fragmentos: list) -> str:
    """Reconstruye la imagen final ordenando los fragmentos por índice."""
    fragmentos_ordenados = sorted(fragmentos, key=lambda f: f["indice"])

    primer_img_bytes = base64.b64decode(fragmentos_ordenados[0]["resultado"])
    primer_img = Image.open(io.BytesIO(primer_img_bytes))

    total_height = calcular_height(fragmentos_ordenados)
    resultado = Image.new("L", (primer_img.width, total_height))

    y_actual = 0
    for f in fragmentos_ordenados:
        img_bytes = base64.b64decode(f["resultado"])
        img = Image.open(io.BytesIO(img_bytes))
        resultado.paste(img, (0, y_actual))
        y_actual += img.height

    buffer = io.BytesIO()
    resultado.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def procesar_resultado(ch, method, properties, body):
    mensaje = json.loads(body)
    job_id = mensaje.get("job_id", "unknown")
    indice = mensaje["indice"]
    total = mensaje["fragmentos"]

    log.info(f"[Joiner] Fragmento {indice}/{total-1} recibido para job {job_id}")

    if job_id not in fragmentos_por_job:
        fragmentos_por_job[job_id] = []
    fragmentos_por_job[job_id].append(mensaje)

    if len(fragmentos_por_job[job_id]) == total:
        log.info(f"[Joiner] Job {job_id} completo. Reconstruyendo imagen...")
        imagen_b64 = reconstruir_imagen(fragmentos_por_job[job_id])

        # Guardar resultado en Redis para que el backend pueda servirlo
        redis_client.set(f"job:{job_id}:result", imagen_b64)
        redis_client.set(f"job:{job_id}:status", "completed")

        del fragmentos_por_job[job_id]
        log.info(f"[Joiner] Job {job_id} guardado en Redis.")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    while True:
        try:
            connection = conectar_rabbit()
            channel = connection.channel()

            # La cola resultados_joiner ya fue creada por setup.py
            channel.queue_declare(queue="resultados_joiner", durable=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue="resultados_joiner",
                on_message_callback=procesar_resultado,
                auto_ack=False,
            )

            log.info("[Joiner] Esperando resultados en 'resultados_joiner'...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            log.warning("[Joiner] Conexión perdida, reconectando...")
        except Exception as e:
            log.error(f"[Joiner] Error inesperado: {e}")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("[Joiner] Detenido.")
