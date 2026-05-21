"""
Hit3 - Backend Service
API HTTP que orquesta el pipeline de procesamiento Sobel:
  POST /process  → recibe imagen, genera job_id, la envía al split service,
                   guarda estado en Redis, retorna job_id al cliente.
  GET  /result/{job_id} → consulta Redis para el resultado.
  GET  /health   → health check.
"""

import os
import uuid
import httpx
import redis
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import uvicorn
import base64

SPLIT_HOST = os.getenv("SPLIT_HOST", "split")
SPLIT_PORT = os.getenv("SPLIT_PORT", "9000")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "backend.log")),
    ],
)
log = logging.getLogger(__name__)

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

app = FastAPI(title="Sobel Backend")


@app.get("/health")
def health():
    return {"servicio": "backend", "status": "running"}


@app.post("/process")
async def process(file: UploadFile = File(...)):
    """Recibe una imagen, la envía al split service y retorna un job_id."""
    job_id = str(uuid.uuid4())

    datos = await file.read()

    # Registrar el job en Redis como pendiente
    redis_client.set(f"job:{job_id}:status", "pending")

    # Enviar imagen al split service
    split_url = f"http://{SPLIT_HOST}:{SPLIT_PORT}/split?job_id={job_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            split_url,
            files={"file": (file.filename, datos, file.content_type)},
        )

    if response.status_code != 200:
        redis_client.delete(f"job:{job_id}:status")
        raise HTTPException(
            status_code=502, detail=f"Error en split service: {response.text}"
        )

    info = response.json()
    log.info(
        f"[Backend] Job {job_id} iniciado: {info['fragmentos']} fragmentos enviados."
    )

    return {"job_id": job_id, "fragmentos": info["fragmentos"], "status": "pending"}


@app.get("/result/{job_id}")
def result(job_id: str):
    """Consulta el estado y resultado de un job."""
    status = redis_client.get(f"job:{job_id}:status")
    if status is None:
        raise HTTPException(status_code=404, detail="Job no encontrado.")

    if status != "completed":
        return {"job_id": job_id, "status": status}

    imagen_b64 = redis_client.get(f"job:{job_id}:result")
    return {
        "job_id": job_id,
        "status": "completed",
        "imagen_base64": imagen_b64,
    }


@app.get("/result/{job_id}/image")
def result_image(job_id: str):
    """Devuelve la imagen resultado directamente como PNG."""
    status = redis_client.get(f"job:{job_id}:status")
    if status is None:
        raise HTTPException(status_code=404, detail="Job no encontrado.")
    if status != "completed":
        raise HTTPException(status_code=202, detail="Job en proceso.")

    imagen_b64 = redis_client.get(f"job:{job_id}:result")
    imagen_bytes = base64.b64decode(imagen_b64)
    return Response(content=imagen_bytes, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
