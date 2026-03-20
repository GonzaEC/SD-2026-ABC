import socket
import logging
import os
import time
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import threading
import uvicorn

# Logs en archivo
# Creo la carpeta log si no existe, y dentro el archivo hit1.log, limpio el archivo en cada ejecucion para que no se
# almacenen logs de las ejecuciones anteriores y evitar confusiones.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "hit1.log")
open(LOG_PATH, "w").close()

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

# Guardo el estado de los servicios para consultas posteriores
estado_servicio = {
    "Servidor TCP": "Detenido",
    "Cliente TCP": "No ejecutado"
}

# FastAPI
app = FastAPI()

# Devuelvo el estado del servicio
@app.get("/status")
def status():
    return estado_servicio

# Chequeo de funcionamiento
@app.get("/health")
def health():
    return {
        "estado": "OK",
        "servidor_tcp": estado_servicio["Servidor TCP"]
    }

# Consulta para obtener los logs en memoria
@app.get("/logs/memoria", response_class=PlainTextResponse)
def logs_memoria_endpoint():
    return "\n".join(logs_memoria[-20:])

# Consulta para obtener los logs en archivo
@app.get("/logs/archivo", response_class=PlainTextResponse)
def logs_archivo_endpoint():
    try:
        with open(LOG_PATH, "r") as f:
            return "".join(f.readlines()[-20:])
    except FileNotFoundError:
        return "No hay logs todavía"
    

# Cofiguracion de la conexion TCP para el servidor
HOST = '0.0.0.0'
PUERTO = 333

# Servidor TCP
def iniciar_servidor():
    global estado_servicio

    estado_servicio["Servidor TCP"] = "Iniciando"
    print("[SERVIDOR] Iniciando servidor TCP...")

    # Creo el socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Asocio IP y Puerto
    s.bind((HOST, PUERTO))
    # El servidor espera conexiones (maximo 1)
    s.listen(1)

    print(f"[SERVIDOR] Escuchando en {HOST}:{PUERTO}")
    log_evento(f"[SERVIDOR] Servidor TCP esperando conexion en {HOST}:{PUERTO}")

    # Acepto la conexion de un cliente
    conexion, direccion = s.accept()
    print(f"[SERVIDOR] Conectado con {direccion}")
    log_evento(f"[SERVIDOR] Conectado con: {direccion}")

    # Recibo el mensaje del cliente
    mensaje = conexion.recv(1024).decode("utf-8")
    print(f"[SERVIDOR] Mensaje recibido: {mensaje}")
    log_evento(f"[SERVIDOR] Mensaje del cliente: {mensaje}")

    # Envio respuesta al cliente
    respuesta = "Hola A (cliente), soy B (servidor)."
    conexion.send(respuesta.encode())
    print(f"[SERVIDOR] Respuesta enviada")
    log_evento(f"[SERVIDOR] Respuesta enviada: {respuesta}")

    # Cierro la conexion
    conexion.close()
    s.close()

    # Estado final del servidor
    estado_servicio["Servidor TCP"] = "OK"
    print("[SERVIDOR] Finalizado correctamente")

def main():
    # Levanto la api en otro hilo para poder correr la api y el servidor al mismo tiempo
    api_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning"),
        daemon=True
    )
    api_thread.start()

    iniciar_servidor()

if __name__ == "__main__":
    main()