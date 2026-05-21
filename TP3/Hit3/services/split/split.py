"""
Hit3 - Split Service
Divide una imagen en N fragmentos y los publica en tareas_exchange.
Se expone como API HTTP para que el backend pueda invocarlo.
"""

import pika
import time
import threading
import os
import logging
import json
import base64
import io
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from PIL import Image

RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_USER = os.environ["RABBITMQ_USER"]
RABBITMQ_PASS = os.environ["RABBITMQ_PASS"]
WORKERS = int(os.getenv("WORKERS", "3"))

BACKOFF_DELAYS = [1, 2, 4, 8, 30]

LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "split.log")),
    ],
)
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

app = FastAPI()


@app.get("/health")
def health():
    return {"servicio": "split", "status": "running"}


def conectar_rabbit():
    ultimo_error = None
    for delay in BACKOFF_DELAYS:
        try:
            credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=5672, credentials=credenciales
                )
            )
            return conn
        except pika.exceptions.AMQPConnectionError as e:
            ultimo_error = e
            log.warning(f"[Split] RabbitMQ no disponible, reintentando en {delay}s...")
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
            log.warning("[Split] RabbitMQ no disponible, reintentando en 30s...")
            time.sleep(30)


def dividir_y_publicar(imagen: Image.Image, job_id: str) -> int:
    """Divide la imagen en fragmentos y los publica en tareas_exchange."""
    height = imagen.height
    fragmento_height = height // WORKERS

    connection = conectar_rabbit()
    channel = connection.channel()

    channel.exchange_declare(
        exchange="tareas_exchange", exchange_type="direct", durable=True
    )

    for i in range(WORKERS):
        top = i * fragmento_height
        bottom = height if i == WORKERS - 1 else (i + 1) * fragmento_height

        fragmento = imagen.crop((0, top, imagen.width, bottom))
        buffer = io.BytesIO()
        fragmento.save(buffer, format="PNG")
        img_bytes = base64.b64encode(buffer.getvalue()).decode()

        mensaje = {
            "job_id": job_id,
            "indice": i,
            "imagen": img_bytes,
            "fragmentos": WORKERS,
        }

        channel.basic_publish(
            exchange="tareas_exchange",
            routing_key="tarea",
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        log.info(f"[Split] Fragmento {i}/{WORKERS-1} enviado para job {job_id}")

    connection.close()
    log.info(f"[Split] Job {job_id}: {WORKERS} fragmentos enviados.")
    return WORKERS


@app.post("/split")
async def split_endpoint(job_id: str, file: UploadFile = File(...)):
    try:
        datos = await file.read()
        imagen = Image.open(io.BytesIO(datos))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Imagen inválida: {e}")

    total = dividir_y_publicar(imagen, job_id)
    return {"job_id": job_id, "fragmentos": total}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
