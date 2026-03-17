import socket
import logging
import os

# -------------------
# Carpeta de logs relativa al script
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# -------------------
# Logging
# -------------------
logging.basicConfig(
    level=logging.INFO,  # Solo INFO y superior
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit1.log")),
        logging.StreamHandler()
    ]
)

HOST = '127.0.0.1'
PUERTO = 333

# Estado del servicio
estado_servicio = {
    "Servidor TCP": "No ejecutado",
    "Cliente TCP": "Detenido"
}

def iniciar_cliente():
    global estado_servicio
    estado_servicio["Cliente TCP"] = "Iniciando"

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PUERTO))
    logging.info("Conectado con el servidor")

    mensaje = "hola!!!"
    cliente.send(mensaje.encode('utf-8'))
    logging.info(f"Mensaje enviado: {mensaje}")

    datos = cliente.recv(1024).decode('utf-8')
    logging.info(f"Mensaje recibido del servidor: {datos}")

    cliente.close()
    estado_servicio["Cliente TCP"] = "OK"

    return datos

if __name__ == "__main__":
    iniciar_cliente()