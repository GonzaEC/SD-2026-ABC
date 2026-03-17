import socket
import logging
import os
import time

# -------------------
# Carpetas y paths
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "hit1.log")

# -------------------
# Logging SOLO archivo
# -------------------
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# -------------------
# Logs en memoria
# -------------------
logs_memoria = []

def log_evento(mensaje):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{timestamp} - {mensaje}"
    logs_memoria.append(linea)
    logging.info(mensaje)

# -------------------
# Config TCP
# -------------------
HOST = '127.0.0.1'
PUERTO = 333

estado_servicio = {
    "Servidor TCP": "No ejecutado",
    "Cliente TCP": "Detenido"
}

# -------------------
# Cliente TCP
# -------------------
def iniciar_cliente():
    global estado_servicio

    estado_servicio["Cliente TCP"] = "Iniciando"
    print("[CLIENTE] Iniciando cliente...")

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PUERTO))

    print("[CLIENTE] Conectado al servidor")
    log_evento("Conectado con el servidor")

    mensaje = "hola!!!"
    cliente.send(mensaje.encode('utf-8'))

    print(f"[CLIENTE] Mensaje enviado: {mensaje}")
    log_evento(f"Mensaje enviado: {mensaje}")

    datos = cliente.recv(1024).decode('utf-8')

    print(f"[CLIENTE] Respuesta recibida: {datos}")
    log_evento(f"Mensaje recibido del servidor: {datos}")

    cliente.close()

    estado_servicio["Cliente TCP"] = "OK"
    print("[CLIENTE] Finalizado correctamente")

    return datos

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    iniciar_cliente()