import socket
import time
import logging
import os
from queue import Queue

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
        logging.FileHandler(os.path.join(LOG_DIR, "hit2.log")),
        logging.StreamHandler()
    ]
)

host = '127.0.0.1'
puerto= 333

# Estado del servicio
estado_servicio = {
    "Servidor TCP": "No ejecutado",
    "Cliente TCP": "Detenido"
}

def iniciar_cliente(colaRespuesta,colaIntentos): 
    intentos = 0
    while(True):
        try:
            estado_servicio["Cliente TCP"] = "Iniciando"
            cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            cliente.connect((host,puerto))
            logging.info(f"Conectado con el servidor")
            mensaje = "hola!!!"
            cliente.send(mensaje.encode('utf-8'))
            logging.info(f"Mensaje enviado!!!")
            datos = cliente.recv(1024)
            logging.info(f"Mensaje recibido del servidor: %s",datos.decode('utf-8'))
            cliente.close()
            colaRespuesta.put(datos.decode('utf-8'))
            colaIntentos.put(intentos)
            estado_servicio["Cliente TCP"] = "OK"
            break

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            logging.info("Conexión perdida. Reintentando en 3 segundos...")
            estado_servicio["Cliente TCP"] = "Reintentando conexion"
            time.sleep(3)
            intentos += 1        
    

if __name__ == "__main__":
    iniciar_cliente(Queue(),Queue()) #Inicia vacio solo se usan colas para el testeo
