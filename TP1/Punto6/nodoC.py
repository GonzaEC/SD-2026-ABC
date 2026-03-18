import socket
import time
import threading 
import sys
import json
import requests
import logging
import os
from fastapi import FastAPI
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
        logging.FileHandler(os.path.join(LOG_DIR, "hit6.log")),
        logging.StreamHandler()
    ]
)

# Estado del servicio
estado_servicio = {
    "Servidor TCP": "No ejecutado",
    "Cliente TCP": "Detenido"
}

# -------------------
# FastAPI
# -------------------
app = FastAPI()

@app.get("/status")
def status():
    """Endpoint público que devuelve el estado de los servicios."""
    return estado_servicio

def cliente(IP, PUERTO,respuestaC): 
    global estado_servicio

    estado_servicio["Cliente TCP"] = "Iniciando"
    logging.info("[CLIENTE - Nodo C] Iniciando cliente...")
    while(True):
        try:
            cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            cliente.connect((IP,PUERTO))
            logging.info(f"Conectado con el servidor")
            msj = {
                "tipo": "saludo",
                "mensaje": "hola!!!"
                }
            msj = json.dumps(msj)
            cliente.send(msj.encode('utf-8'))
            logging.info(f"Mensaje enviado!!!")
            datos = cliente.recv(1024)
            datos = json.loads(datos.decode('utf-8'))
            logging.info(f"Mensaje recibido del servidor: %s",datos)
            respuestaC.put(datos)
            cliente.close()
            estado_servicio["Cliente TCP"] = "OK"
            break

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            logging.info("Conexión perdida. Reintentando en 3 segundos...")
            estado_servicio["Cliente TCP"] = "Reintentando conexion"

            time.sleep(3)

def servidor(IP,PUERTO):
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocketServer.bind((IP, PUERTO))
    SocketServer.listen(1)
    logging.info("Servidor esperando conexiones...")
    estado_servicio["Servidor TCP"] = "Iniciando"
    while True:
        
        try:
            conexion, direccion = SocketServer.accept()
            logging.info("Conectado con: %s", direccion)

            datos = conexion.recv(1024)

            if not datos:
                logging.info("El cliente cerro la conexión")
                conexion.close()
                continue

            mensaje = json.loads(datos.decode("utf-8"))
            logging.info("Mensaje del cliente: %s", mensaje)

           
            respuesta = {
                "tipo": "respuesta",
                "mensaje": "Hola A (cliente), soy B (servidor)"
                }
            respuesta = json.dumps(respuesta)
            conexion.send(respuesta.encode('utf-8'))

            conexion.close()
            estado_servicio["Servidor TCP"] = "OK"

        except ConnectionResetError:
            logging.info("El cliente cerro la conexion")

def main(ip_escuchaD, puerto_escuchaD, respuestaC):
    
    peticion = requests.get("http://" + str(ip_escuchaD) + ":" + str(puerto_escuchaD) + "/REGISTER", stream = True)
    socket = peticion.raw._connection.sock
    IP_nodo, Puerto_nodo = socket.getsockname()
    resultado = peticion.json()
    nodos = resultado["nodosDisponibles"]
    hilo_server = threading.Thread(target=servidor,args=(IP_nodo,Puerto_nodo))
    hilo_server.start()
    time.sleep(1) 
    for nodo in nodos:
        IP_Actual = nodo["ip"]
        Puerto_Actual = nodo["puerto"] 
        if(Puerto_Actual != Puerto_nodo):
            hilo_cliente = threading.Thread(target=cliente,args=(IP_Actual,Puerto_Actual,respuestaC))
            hilo_cliente.start()
            hilo_cliente.join()

if __name__ == "__main__":
    ip_escuchaD = sys.argv[1]
    puerto_escuchaD = int(sys.argv[2])
    main(ip_escuchaD, puerto_escuchaD, Queue()) #la cola ingresa vacia normalmente porque es utilizada para tests