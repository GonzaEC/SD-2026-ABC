import socket
import logging
import os
import time
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import threading
import uvicorn

# -------------------
# Carpetas y paths
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "hit1.log")

# Resetear log en cada ejecución
open(LOG_PATH, "w").close()

# -------------------
# Logging SOLO a archivo
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
# Variables TCP
# -------------------
HOST = '0.0.0.0'
PUERTO = 333

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
    return estado_servicio

@app.get("/health")
def health():
    return {
        "estado": "OK",
        "servidor_tcp": estado_servicio["Servidor TCP"]
    }

@app.get("/logs/memoria", response_class=PlainTextResponse)
def logs_memoria_endpoint():
    return "\n".join(logs_memoria[-20:])

@app.get("/logs/archivo", response_class=PlainTextResponse)
def logs_archivo_endpoint():
    try:
        with open(LOG_PATH, "r") as f:
            return "".join(f.readlines()[-20:])
    except FileNotFoundError:
        return "No hay logs todavía"

# -------------------
# Servidor TCP
# -------------------
def iniciar_servidor():
    global estado_servicio

    estado_servicio["Servidor TCP"] = "Iniciando"
    print("[SERVIDOR] Iniciando servidor TCP...")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PUERTO))
    s.listen(1)

    print(f"[SERVIDOR] Escuchando en {HOST}:{PUERTO}")
    log_evento(f"Servidor TCP esperando conexión en {HOST}:{PUERTO}")

    conexion, direccion = s.accept()

    print(f"[SERVIDOR] Conectado con {direccion}")
    log_evento(f"Conectado con: {direccion}")

    mensaje = conexion.recv(1024).decode("utf-8")

    print(f"[SERVIDOR] Mensaje recibido: {mensaje}")
    log_evento(f"Mensaje del cliente: {mensaje}")

    respuesta = "Hola A (cliente), soy B (servidor)."
    conexion.send(respuesta.encode())

    print(f"[SERVIDOR] Respuesta enviada")
    log_evento(f"Respuesta enviada: {respuesta}")

    conexion.close()
    s.close()

    estado_servicio["Servidor TCP"] = "OK"
    print("[SERVIDOR] Finalizado correctamente")

# -------------------
# Main
# -------------------
def main():
    api_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning"),
        daemon=True
    )
    api_thread.start()

    iniciar_servidor()

if __name__ == "__main__":
    main()