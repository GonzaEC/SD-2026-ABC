"""
Hit3 - Sobel Worker
Consume fragmentos de la cola 'tareas', aplica el operador de Sobel,
y publica el resultado al exchange fanout 'resultados_exchange'.

Patrones implementados:
  - DLQ: si el procesamiento falla, NACK(requeue=False) → fragmento va a tareas_muertos
  - Exponential backoff: reconexión a RabbitMQ con delays 1s, 2s, 4s, 8s, 30s
  - Pub/Sub: resultado publicado al fanout → joiner y monitor reciben notificación
"""

import pika
import time
import threading
import os
import logging
import json
import base64
import io
from fastapi import FastAPI
import uvicorn
from PIL import Image
from sobel import sobel

RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_USER = os.environ["RABBITMQ_USER"]
RABBITMQ_PASS = os.environ["RABBITMQ_PASS"]
WORKER_ID = os.getenv("WORKER_ID", "unknown")

BACKOFF_DELAYS = [1, 2, 4, 8, 30]

LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, f"worker-{os.getenv('WORKER_ID', 'unknown')}.log")),
    ],
)
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

app = FastAPI()


@app.get("/health")
def health():
    return {"servicio": WORKER_ID, "status": "running"}


def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def conectar_rabbit():
    """Conecta a RabbitMQ con exponential backoff (1s, 2s, 4s, 8s, 30s)."""
    ultimo_error = None
    for delay in BACKOFF_DELAYS:
        try:
            credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=5672, credentials=credenciales
                )
            )
            log.info(f"[Worker {WORKER_ID}] Conectado a RabbitMQ.")
            return conn
        except pika.exceptions.AMQPConnectionError as e:
            ultimo_error = e
            log.warning(
                f"[Worker {WORKER_ID}] RabbitMQ no disponible, reintentando en {delay}s..."
            )
            time.sleep(delay)
    # Si agotó todos los reintentos, seguir intentando con el delay máximo
    while True:
        try:
            credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=5672, credentials=credenciales
                )
            )
            log.info(f"[Worker {WORKER_ID}] Conectado a RabbitMQ.")
            return conn
        except pika.exceptions.AMQPConnectionError:
            log.warning(
                f"[Worker {WORKER_ID}] RabbitMQ no disponible, reintentando en 30s..."
            )
            time.sleep(30)


def publicar_resultado(mensaje_resultado: dict):
    """Publica el resultado al exchange fanout para joiner y monitor."""
    conn = conectar_rabbit()
    ch = conn.channel()
    ch.basic_publish(
        exchange="resultados_exchange",
        routing_key="",  # fanout ignora routing_key
        body=json.dumps(mensaje_resultado),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conn.close()


def procesar_mensaje(ch, method, properties, body):
    if method.redelivered:
        log.info(f"[Worker {WORKER_ID}] Mensaje reenviado detectado.")

    try:
        mensaje = json.loads(body)
        indice = mensaje["indice"]
        job_id = mensaje.get("job_id", "unknown")

        log.info(
            f"[Worker {WORKER_ID}] Procesando fragmento {indice} del job {job_id}"
        )

        datos = base64.b64decode(mensaje["imagen"])
        imagen = Image.open(io.BytesIO(datos))
        resultado = sobel(imagen)

        buffer = io.BytesIO()
        resultado.save(buffer, format="PNG")
        img_bytes = base64.b64encode(buffer.getvalue()).decode()

        mensaje_resultado = {
            "job_id": job_id,
            "indice": indice,
            "resultado": img_bytes,
            "fragmentos": mensaje["fragmentos"],
        }

        # Pub/Sub: publica al fanout → joiner y monitor reciben la notificación
        publicar_resultado(mensaje_resultado)

        log.info(
            f"[Worker {WORKER_ID}] Fragmento {indice} procesado y publicado al fanout."
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        # DLQ: si el procesamiento falla, NACK sin requeue → va a tareas_muertos
        log.error(
            f"[Worker {WORKER_ID}] Error procesando fragmento: {e}. Enviando a DLQ."
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    while True:
        try:
            connection = conectar_rabbit()
            channel = connection.channel()

            channel.queue_declare(
                queue="tareas",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "sobel_dlx",
                    "x-dead-letter-routing-key": "fragmento_fallido",
                },
            )

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue="tareas",
                on_message_callback=procesar_mensaje,
                auto_ack=False,
            )

            log.info(f"[Worker {WORKER_ID}] Esperando fragmentos en 'tareas'...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            log.warning(f"[Worker {WORKER_ID}] Conexión perdida, reconectando...")
        except Exception as e:
            log.error(f"[Worker {WORKER_ID}] Error inesperado: {e}")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info(f"[Worker {WORKER_ID}] Detenido.")
