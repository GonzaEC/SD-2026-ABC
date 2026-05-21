"""
Genera imágenes de prueba de distintos tamaños para el load testing.
Crea PNGs en escala de grises con ruido aleatorio para que el filtro Sobel
tenga trabajo real que hacer.
"""
import os
import struct
import zlib
import math
import random

SIZES = {
    "1KB":   1 * 1024,
    "10KB":  10 * 1024,
    "100KB": 100 * 1024,
    "1MB":   1 * 1024 * 1024,
    "10MB":  10 * 1024 * 1024,
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "images")


def make_png(width: int, height: int) -> bytes:
    """Genera un PNG en escala de grises con ruido aleatorio."""
    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        body = chunk_type + data
        checksum = struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        return length + body + checksum

    signature = b"\x89PNG\r\n\x1a\n"

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    ihdr = png_chunk(b"IHDR", ihdr_data)

    raw_rows = []
    for _ in range(height):
        row = bytes([0] + [random.randint(0, 255) for _ in range(width)])
        raw_rows.append(row)
    compressed = zlib.compress(b"".join(raw_rows), level=1)
    idat = png_chunk(b"IDAT", compressed)

    iend = png_chunk(b"IEND", b"")

    return signature + ihdr + idat + iend


def dimensions_for_target_size(target_bytes: int):
    """Calcula dimensiones aproximadas para alcanzar el tamaño objetivo.
    Un PNG sin comprimir de WxH px (escala de grises) ocupa ~W*H bytes de datos raw.
    Con compresión level=1 y ruido aleatorio la compresión es mínima (~1:1).
    """
    pixels = target_bytes
    side = max(1, int(math.sqrt(pixels)))
    return side, side


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for label, target in SIZES.items():
        w, h = dimensions_for_target_size(target)
        png_bytes = make_png(w, h)

        # Ajuste fino: si salió muy chico, aumentar dimensiones
        while len(png_bytes) < target * 0.8:
            w = int(w * 1.1) + 1
            h = int(h * 1.1) + 1
            png_bytes = make_png(w, h)

        path = os.path.join(OUTPUT_DIR, f"{label}.png")
        with open(path, "wb") as f:
            f.write(png_bytes)
        print(f"{label}: {w}x{h}px → {len(png_bytes)/1024:.1f} KB  ({path})")


if __name__ == "__main__":
    main()
