"""
Tests unitarios de la lógica de reconstrucción de imagen del joiner.
Verifican que los fragmentos se ordenen por índice y se combinen correctamente.
"""

import sys
import os
import io
import base64
import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/joiner"))
from joiner import reconstruir_imagen, calcular_height


def fragmento_base64_de(imagen: Image.Image) -> str:
    buf = io.BytesIO()
    imagen.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def crear_fragmento(indice: int, color: int, width=10, height=5) -> dict:
    img = Image.new("L", (width, height), color=color)
    return {
        "job_id": "test-job",
        "indice": indice,
        "resultado": fragmento_base64_de(img),
        "fragmentos": 3,
    }


class TestCalcularHeight:
    def test_suma_heights(self):
        fragmentos = [crear_fragmento(i, i * 80) for i in range(3)]
        total = calcular_height(fragmentos)
        assert total == 15  # 3 fragmentos × 5px

    def test_un_fragmento(self):
        fragmento = [crear_fragmento(0, 128)]
        assert calcular_height(fragmento) == 5


class TestReconstruirImagen:
    def test_dimension_correcta(self):
        fragmentos = [crear_fragmento(i, i * 80) for i in range(3)]
        b64 = reconstruir_imagen(fragmentos)
        img = Image.open(io.BytesIO(base64.b64decode(b64)))
        assert img.size == (10, 15)

    def test_orden_por_indice(self):
        """Fragmento 0 = negro, 1 = gris, 2 = blanco. Verificar orden vertical."""
        frag_0 = crear_fragmento(0, 0)    # negro arriba
        frag_1 = crear_fragmento(1, 128)  # gris en el medio
        frag_2 = crear_fragmento(2, 255)  # blanco abajo

        # Enviar desordenados
        resultado_b64 = reconstruir_imagen([frag_2, frag_0, frag_1])
        img = Image.open(io.BytesIO(base64.b64decode(resultado_b64)))

        pixel_top = img.getpixel((5, 2))     # zona del fragmento 0 (negro)
        pixel_bottom = img.getpixel((5, 12)) # zona del fragmento 2 (blanco)

        assert pixel_top < pixel_bottom

    def test_retorna_base64_valido(self):
        fragmentos = [crear_fragmento(i, 100) for i in range(2)]
        b64 = reconstruir_imagen(fragmentos)
        # No debe lanzar excepción al decodificar
        decoded = base64.b64decode(b64)
        img = Image.open(io.BytesIO(decoded))
        assert img.mode == "L"

    def test_un_fragmento(self):
        fragmento = [crear_fragmento(0, 200)]
        b64 = reconstruir_imagen(fragmento)
        img = Image.open(io.BytesIO(base64.b64decode(b64)))
        assert img.size == (10, 5)
