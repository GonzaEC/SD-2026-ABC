"""
Tests unitarios del operador de Sobel.
Cubren: dimensiones de salida, tipo de imagen, magnitud en zonas uniformes
y detección de bordes en una imagen con transición abrupta.
"""

import sys
import os
import math
import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/worker"))
from sobel import sobel, to_grayscale, apply_kernel, KERNEL_GX, KERNEL_GY


class TestToGrayscale:
    def test_dimensiones(self, imagen_pequena):
        grid = to_grayscale(imagen_pequena)
        assert len(grid) == imagen_pequena.height
        assert len(grid[0]) == imagen_pequena.width

    def test_valores_en_rango(self, imagen_pequena):
        grid = to_grayscale(imagen_pequena)
        for row in grid:
            for val in row:
                assert 0 <= val <= 255

    def test_imagen_blanca_da_255(self, imagen_blanca):
        grid = to_grayscale(imagen_blanca)
        assert all(v == 255 for row in grid for v in row)


class TestApplyKernel:
    def test_kernel_cero_en_zona_uniforme(self):
        grid = [[128] * 5 for _ in range(5)]
        result = apply_kernel(grid, 2, 2, KERNEL_GX)
        assert result == pytest.approx(0.0)

    def test_clamp_en_borde(self):
        grid = [[0] * 5 for _ in range(5)]
        # No debe lanzar IndexError en los bordes
        apply_kernel(grid, 0, 0, KERNEL_GX)
        apply_kernel(grid, 4, 4, KERNEL_GY)


class TestSobel:
    def test_dimensiones_preservadas(self, imagen_pequena):
        resultado = sobel(imagen_pequena)
        assert resultado.size == imagen_pequena.size

    def test_modo_escala_grises(self, imagen_pequena):
        resultado = sobel(imagen_pequena)
        assert resultado.mode == "L"

    def test_imagen_uniforme_da_magnitud_baja(self, imagen_blanca):
        resultado = sobel(imagen_blanca)
        pixels = list(resultado.getdata())
        # Interior de imagen uniforme: bordes deberían estar cerca de 0
        interior = [
            resultado.getpixel((x, y))
            for y in range(2, imagen_blanca.height - 2)
            for x in range(2, imagen_blanca.width - 2)
        ]
        assert max(interior) == 0

    def test_borde_vertical_detectado(self):
        img = Image.new("L", (20, 10))
        pixels = img.load()
        for y in range(10):
            for x in range(20):
                pixels[x, y] = 255 if x >= 10 else 0
        resultado = sobel(img)
        val_centro = resultado.getpixel((10, 5))
        val_esquina = resultado.getpixel((0, 5))
        assert val_centro > val_esquina

    def test_valores_normalizados_en_rango(self, imagen_pequena):
        resultado = sobel(imagen_pequena)
        pixels = list(resultado.getdata())
        assert all(0 <= p <= 255 for p in pixels)
        assert max(pixels) == 255  # normalización lleva al máximo a 255

    def test_imagen_1x1(self):
        img = Image.new("RGB", (1, 1), color=(128, 128, 128))
        resultado = sobel(img)
        assert resultado.size == (1, 1)
        assert resultado.getpixel((0, 0)) == 0


# Fixtures importados de conftest.py (pytest los inyecta automáticamente)
def test_borde_vertical_detectado(imagen_negro_blanco):
    resultado = sobel(imagen_negro_blanco)
    val_centro = resultado.getpixel((10, 5))
    val_borde_iz = resultado.getpixel((1, 5))
    assert val_centro > val_borde_iz
