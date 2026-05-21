"""
Fixtures compartidos para tests unitarios e integración de Hit3.
"""

import io
import math
import pytest
from PIL import Image


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
