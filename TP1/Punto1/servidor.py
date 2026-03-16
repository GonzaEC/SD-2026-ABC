import socket
import logging
import os
from fastapi import FastAPI
import threading
import uvicorn

# -------------------
# Crear carpeta logs si no existe
# -------------------
os.makedirs("logs", exist_ok=True)

# -------------------
# Configuración de logging
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/hit1.log"),  # logs en disco
        logging.StreamHandler()                # logs en memoria / consola
    ]
)

# -------------------
# Variables TCP
# -------------------
HOST = '0.0.0.0'  # accesible desde cualquier IP
PUERTO = 333

# Estado del servicio para el endpoint
estado_servicio = {
    "Servidor TCP": "Detenido",
    "Cliente TCP": "No ejecutado"
}

# -------------------
# FastAPI
# -------------------
app = FastAPI()

@app.get("/status")
def status():
    """Endpoint público que devuelve el estado de los servicios."""
    return estado_servicio

# -------------------
# Servidor TCP
# -------------------
def iniciar_servidor():
    global estado_servicio
    estado_servicio["Servidor TCP"] = "Iniciando"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PUERTO))
    s.listen(1)
    logging.info(f"Servidor TCP esperando conexión en {HOST}:{PUERTO}...")

    conexion, direccion = s.accept()
    logging.info(f"Conectado con: {direccion}")

    mensaje = conexion.recv(1024).decode("utf-8")
    logging.info(f"Mensaje del cliente: {mensaje}")

    respuesta = "Hola A (cliente), soy B (servidor)."
    conexion.send(respuesta.encode())
    logging.info(f"Respuesta enviada: {respuesta}")

    conexion.close()
    s.close()

    estado_servicio["Servidor TCP"] = "OK"
    return mensaje, respuesta

# -------------------
# Ejecutar FastAPI y TCP en paralelo
# -------------------
def main():
    # FastAPI en un thread separado
    api_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000),
        daemon=True
    )
    api_thread.start()

    # Servidor TCP
    iniciar_servidor()

if __name__ == "__main__":
    main()