"""
Test end-to-end del pipeline Sobel sobre el stack local (docker-compose).

Prerrequisito: stack levantado con docker-compose up -d
Uso:          python test_e2e.py [ruta_imagen]

Si no se pasa imagen, genera una sintética de 60x30px.
"""

import sys
import io
import time
import base64
import requests
from PIL import Image

BACKEND = "http://localhost:8080"
TIMEOUT_SEGUNDOS = 60


def crear_imagen_sintetica() -> bytes:
    img = Image.new("RGB", (60, 30))
    pix = img.load()
    for y in range(30):
        for x in range(60):
            pix[x, y] = (x * 4, y * 8, 128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
    # 1. Health check del backend
    print("1. Verificando health del backend...")
    r = requests.get(f"{BACKEND}/health", timeout=5)
    r.raise_for_status()
    print(f"   ✓ {r.json()}")

    # 2. Cargar imagen
    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as f:
            imagen_bytes = f.read()
        nombre = sys.argv[1]
    else:
        imagen_bytes = crear_imagen_sintetica()
        nombre = "sintetica.png"
    print(f"2. Imagen: {nombre} ({len(imagen_bytes)} bytes)")

    # 3. Enviar imagen al backend
    print("3. Enviando imagen al pipeline...")
    r = requests.post(
        f"{BACKEND}/process",
        files={"file": (nombre, imagen_bytes, "image/png")},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    job_id = data["job_id"]
    print(f"   ✓ Job ID: {job_id}  ({data['fragmentos']} fragmentos)")

    # 4. Polling del resultado
    print(f"4. Esperando resultado (max {TIMEOUT_SEGUNDOS}s)...")
    inicio = time.time()
    while time.time() - inicio < TIMEOUT_SEGUNDOS:
        r = requests.get(f"{BACKEND}/result/{job_id}", timeout=5)
        r.raise_for_status()
        estado = r.json()

        if estado["status"] == "completed":
            print(f"   ✓ Completado en {time.time()-inicio:.1f}s")
            break

        print(f"   ... status={estado['status']}, esperando 2s")
        time.sleep(2)
    else:
        print(f"   ✗ Timeout después de {TIMEOUT_SEGUNDOS}s")
        sys.exit(1)

    # 5. Descargar imagen resultado
    r = requests.get(f"{BACKEND}/result/{job_id}/image", timeout=10)
    r.raise_for_status()
    salida = "resultado_sobel.png"
    with open(salida, "wb") as f:
        f.write(r.content)

    # 6. Verificar que es una imagen válida en escala de grises
    img_resultado = Image.open(io.BytesIO(r.content))
    assert img_resultado.mode == "L", f"Modo inesperado: {img_resultado.mode}"
    print(f"5. ✓ Imagen guardada: {salida}  ({img_resultado.size[0]}x{img_resultado.size[1]}px, modo={img_resultado.mode})")
    print("\n¡Pipeline completo OK!")


if __name__ == "__main__":
    main()
