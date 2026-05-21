"""
Fixtures compartidos para tests unitarios e integración de Hit3.
"""

import io
import os
import math
import tempfile
import pytest
from PIL import Image

# Configurar variables de entorno ANTES de que cualquier servicio se importe.
# LOG_DIR en /tmp evita errores de permisos en CI (los servicios crean /app/logs al importarse).
_tmp_logs = os.path.join(tempfile.gettempdir(), "sobel-test-logs")
os.makedirs(_tmp_logs, exist_ok=True)
os.environ.setdefault("LOG_DIR", _tmp_logs)
os.environ.setdefault("RABBITMQ_HOST", "localhost")
os.environ.setdefault("RABBITMQ_USER", "user")
os.environ.setdefault("RABBITMQ_PASS", "password")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("WORKER_ID", "test-worker")
os.environ.setdefault("SPLIT_HOST", "split")
os.environ.setdefault("SPLIT_PORT", "9000")


@pytest.fixture
def imagen_pequena():
    """Imagen RGB 10x10 con degradado simple — suficiente para verificar Sobel."""
    img = Image.new("RGB", (10, 10))
    pixels = img.load()
    for y in range(10):
        for x in range(10):
            v = int(255 * x / 9)
            pixels[x, y] = (v, v, v)
    return img


@pytest.fixture
def imagen_blanca():
    """Imagen completamente blanca — Sobel debe dar magnitud 0 en todo interior."""
    return Image.new("RGB", (20, 20), color=(255, 255, 255))


@pytest.fixture
def imagen_negro_blanco():
    """Mitad izquierda negra, mitad derecha blanca — borde vertical en el centro."""
    img = Image.new("L", (20, 10))
    pixels = img.load()
    for y in range(10):
        for x in range(20):
            pixels[x, y] = 255 if x >= 10 else 0
    return img


@pytest.fixture
def fragmento_base64(imagen_pequena):
    """Fragmento de imagen codificado en base64 — simula mensaje de RabbitMQ."""
    import base64
    buf = io.BytesIO()
    imagen_pequena.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
