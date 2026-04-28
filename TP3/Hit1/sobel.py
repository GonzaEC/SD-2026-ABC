"""
Operador de Sobel - Proceso Centralizado
========================================
Aplica el operador de Sobel a una imagen para detección de bordes.

Uso:
    python sobel.py <imagen_entrada> [imagen_salida]

Ejemplo:
    python sobel.py foto.jpg foto_sobel.jpg
"""

import sys
import os
import math
import time
from PIL import Image


# ─── Máscaras del operador de Sobel ───────────────────────────────────────────
# Detectan cambios de intensidad en dirección horizontal (Gx) y vertical (Gy)

KERNEL_GX = [
    [-1, 0, +1],
    [-2, 0, +2],
    [-1, 0, +1],
]

KERNEL_GY = [
    [-1, -2, -1],
    [ 0,  0,  0],
    [+1, +2, +1],
]

inicio = time.time()
def to_grayscale(image: Image.Image) -> list[list[int]]:
    """Convierte una imagen PIL a una matriz 2D de valores de gris (0–255)."""
    gray = image.convert("L")          # PIL convierte a luminancia
    width, height = gray.size
    pixels = gray.load()
    return [[pixels[x, y] for x in range(width)] for y in range(height)]


def apply_kernel(grid: list[list[int]], row: int, col: int,
                 kernel: list[list[int]]) -> float:
    """
    Aplica un kernel 3×3 a un píxel (row, col) de la grilla.
    Los bordes usan padding de replicación (clamp).
    """
    height = len(grid)
    width  = len(grid[0])
    total  = 0.0

    for ky in range(3):
        for kx in range(3):
            # Coordenadas del vecino, con clamp en los bordes
            ny = min(max(row + ky - 1, 0), height - 1)
            nx = min(max(col + kx - 1, 0), width  - 1)
            total += grid[ny][nx] * kernel[ky][kx]

    return total


def sobel(image: Image.Image) -> Image.Image:
    """
    Aplica el operador de Sobel a la imagen y devuelve la imagen de magnitud.

    Para cada píxel:
        Gx  = convolución con kernel horizontal
        Gy  = convolución con kernel vertical
        |G| = sqrt(Gx² + Gy²)    → normalizado a [0, 255]
    """
    
    grid   = to_grayscale(image)
    height = len(grid)
    width  = len(grid[0])

    # ── Calcular magnitudes ──────────────────────────────────────────────────
    magnitudes = []
    max_mag    = 0.0

    for row in range(height):
        row_mags = []
        for col in range(width):
            gx  = apply_kernel(grid, row, col, KERNEL_GX)
            gy  = apply_kernel(grid, row, col, KERNEL_GY)
            mag = math.sqrt(gx * gx + gy * gy)
            row_mags.append(mag)
            if mag > max_mag:
                max_mag = mag
        magnitudes.append(row_mags)

    # ── Normalizar a [0, 255] y construir imagen resultado ───────────────────
    result = Image.new("L", (width, height))
    pixels = result.load()
    scale  = 255.0 / max_mag if max_mag > 0 else 1.0

    for row in range(height):
        for col in range(width):
            pixels[col, row] = int(magnitudes[row][col] * scale)

    return result


def build_output_path(input_path: str) -> str:
    """Genera el nombre de salida agregando '_sobel' antes de la extensión."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_sobel{ext if ext else '.png'}"


def main():
    # ── Validar argumentos ───────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else build_output_path(input_path)

    if not os.path.isfile(input_path):
        print(f"[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)

    # ── Procesar ─────────────────────────────────────────────────────────────
    print(f"Leyendo imagen:  {input_path}")
    image = Image.open(input_path)
    print(f"Tamaño:          {image.size[0]}×{image.size[1]} px  |  Modo: {image.mode}")
    
    print("Aplicando operador de Sobel...")
    resultado = sobel(image)

    resultado.save(output_path)
    print(f"Imagen guardada: {output_path}")
    print("¡Listo!")
    fin = time.time()
    tiempo = fin - inicio
    print("tiempo ", tiempo )


if __name__ == "__main__":
    main()
