import socket
import logging
import os
import time

# Logs en archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "hit1.log")

# Guardo logs en archvivo, con el formato fecha + mensaje.
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Logs en memoria
logs_memoria = []

# Con esta funcion guardo logs en memoria y archivo
def log_evento(mensaje):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{timestamp} - {mensaje}"
    logs_memoria.append(linea)
    logging.info(mensaje)

# Configuracion TCP para conectarme al servidor
HOST = '127.0.0.1'
PUERTO = 333

# Estado del sistema para monitoreo
estado_servicio = {
    "Servidor TCP": "No ejecutado",
    "Cliente TCP": "Detenido"
}

# Cliente TCP
def iniciar_cliente():
    global estado_servicio

    estado_servicio["Cliente TCP"] = "Iniciando"
    print("[CLIENTE] Iniciando cliente...")

    # Creo el socket y me conecto al servidor
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PUERTO))
    print("[CLIENTE] Conectado al servidor")
    log_evento("[CLIENTE] Conectado con el servidor")

    # Envio mensaje al servidor
    mensaje = "hola!!!"
    cliente.send(mensaje.encode('utf-8'))
    print(f"[CLIENTE] Mensaje enviado: {mensaje}")
    log_evento(f"[CLIENTE] Mensaje enviado: {mensaje}")

    # Recibo mensaje del servidor
    datos = cliente.recv(1024).decode('utf-8')

    print(f"[CLIENTE] Respuesta recibida: {datos}")
    log_evento(f"[CLIENTE] Mensaje recibido del servidor: {datos}")

    # Cierro el cliente
    cliente.close()
    estado_servicio["Cliente TCP"] = "OK"
    print("[CLIENTE] Finalizado correctamente")

    return datos

if __name__ == "__main__":
    iniciar_cliente()