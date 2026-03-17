import socket
import logging
import os
from fastapi import FastAPI
import threading
import uvicorn

# -------------------
# Variables TCP
# -------------------
HOST = '127.0.0.1'
PUERTO = 333

# -------------------
# Carpeta de logs relativa al script
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# -------------------
# Configuración de logging
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit2.log")),
        logging.StreamHandler()
    ]
)

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
    #Creo el socket
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Asocio al socket la IP y Puerto
    SocketServer.bind((HOST, PUERTO))

    #Escucho conexiones
    SocketServer.listen(1)
    logging.info("Servidor esperando conexión...")

    #Acepto conexion
    conexion, direccion = SocketServer.accept()
    logging.info("Conectado con: %s", direccion)

    #Recibo mensaje
    mensaje = conexion.recv(1024).decode("UTF-8")
    logging.info("Mensaje del cliente: %s", mensaje)

    #Respondo saludo
    respuesta = "Hola A (cliente), soy B (servidor)."
    conexion.send(respuesta.encode())

    #Cierro conexion
    conexion.close()
    SocketServer.close()
    estado_servicio["Servidor TCP"] = "OK"

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

    

if __name__ == "__main__":
    main()
    iniciar_servidor()