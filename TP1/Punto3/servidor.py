import socket
HOST = '127.0.0.1'
PUERTO = 333

import socket
import logging
import os
from fastapi import FastAPI
import threading
import uvicorn
estadoV = {"valor": "vacio"}
# -------------------
# Variables TCP
# -------------------
HOST = '127.0.0.1'
PUERTO = 333

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
        logging.FileHandler(os.path.join(LOG_DIR, "hit3.log")),
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
def iniciar_servidor(estado):
    global estado_servicio
    estado_servicio["Servidor TCP"] = "Iniciando" 
    #Creo el socket
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocketServer.bind((HOST, PUERTO))
    SocketServer.listen(1)

    logging.info("Servidor esperando conexiones...")
    while True:
        estado["valor"] = "Servidor esperando conexiones..."
        try:
            conexion, direccion = SocketServer.accept()
            logging.info("Conectado con: %s", direccion)
            estado["valor"] =  "Conectado con cliente" 
            datos = conexion.recv(1024)

            if not datos:
                logging.info("El cliente cerro la conexión")
                conexion.close()
                continue

            mensaje = datos.decode("utf-8")
            logging.info("Mensaje del cliente: %s", mensaje)

            respuesta = "Hola A (cliente), soy B (servidor)"
            conexion.send(respuesta.encode("utf-8"))

            conexion.close()
            estado_servicio["Servidor TCP"] = "OK"
        except ConnectionResetError:
            logging.info("El cliente cerro la conexion")

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
    #se inicia vacio porque este valor es usado para los tests

if __name__ == "__main__":
    main()
    iniciar_servidor(estadoV)
    