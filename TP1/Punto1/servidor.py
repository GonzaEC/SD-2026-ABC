import socket
import logging
import os
from fastapi import FastAPI
import threading
import uvicorn

# -------------------
# Carpeta de logs relativa al script
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# -------------------
# Configuración de logging
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit1.log")),
        logging.StreamHandler()
    ]
)

# -------------------
# Variables TCP
# -------------------
HOST = '0.0.0.0'
PUERTO = 333

# Estado del servicio
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
    # Ejecutar FastAPI en un thread con log_level="warning"
    api_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning"),
        daemon=True
    )
    api_thread.start()

    # Ejecutar servidor TCP
    iniciar_servidor()

if __name__ == "__main__":
    main()