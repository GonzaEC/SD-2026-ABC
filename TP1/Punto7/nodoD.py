from fastapi import FastAPI, Request
import time
import threading
import json
import logging
import os


app = FastAPI()
#Lista de nodos activos en la ventana actual
nodos_activos = []
#Lista de nodos registrados para la próxima ventana
nodos_siguientes = []
#Archivo donde se guardan los registros
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(BASE_DIR, "registro_nodos.json")

tiempoInicio = time.time()

logs_memoria = []

# Logs en archivo
# Creo la carpeta log si no existe, y dentro el archivo hit7.log, limpio el archivo en cada ejecucion para que no se
# almacenen logs de las ejecuciones anteriores y evitar confusiones.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "Logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "hit7.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filemode="w"  # reinicia en cada ejecución
)

logs_memoria = []

# Con esta funcion guardo logs en memoria y archivo
def log_evento(mensaje):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_linea = f"{timestamp} - {mensaje}"
    logs_memoria.append(log_linea)
    logging.info(mensaje)

# Inicializo el archivo JSON vacío al arrancar
def inicializar_archivo():
    datos = {
        "nodos_activos": [],
        "nodos_siguientes": []
    }
    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=4)


#Guardo el estado actual en un archivo JSON
def guardar_archivo():
    datos = {
        "nodos_activos": nodos_activos,
        "nodos_siguientes": nodos_siguientes
    }

    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=4)

# Hilo que controla las ventanas de inscripción
# Cada 60 segundos:
# los nodos_siguientes pasan a ser nodos_activos y se limpia la lista de siguientes
def controlar_ventanas():
    global nodos_activos, nodos_siguientes
    while True:
        time.sleep(60)
        print("[Nodo D] Nueva ventana de tiempo iniciada")
        log_evento("[Nodo D] Cambio de ventana")
        nodos_activos = nodos_siguientes
        nodos_siguientes = []
        guardar_archivo()


# Inicializo el JSON limpio al iniciar el nodo D
inicializar_archivo()

#Inicio el hilo que controla las ventanas
threading.Thread(target=controlar_ventanas, daemon=True).start()

@app.post("/REGISTER")
def registrar_nodo(nodo: dict):
    nodos_siguientes.append(nodo)
    print("[Nodo D] Nodo registrado para la próxima ventana")
    log_evento(f"[Nodo D] Nodo registrado: {nodo}")
    guardar_archivo()
    return {"mensaje": "[Nodo D] Registrado para la próxima ventana"}

@app.get("/status")
def status():
    estado = {
        "api": "OK",
        "registro": "OK",
        "ventanas": "OK",
        "nodos_activos": len(nodos_activos),
        "nodos_siguientes": len(nodos_siguientes)
    }
    return estado

@app.get("/health")
def estado_actual():
    tiempoActual = time.time() - tiempoInicio
    estado = {
        "estado": "OK",
        "nodos_activos": len(nodos_activos),
        "uptime": tiempoActual
    }
    return estado

@app.get("/nodos")
def obtener_nodos():
    # log_evento("[Nodo D] Consulta de nodos activos")
    return {"nodos": nodos_activos}

@app.get("/logs/memoria")
def obtener_logs_memoria():
    return {
        "logs": logs_memoria[-20:]  #
    }

@app.get("/logs/archivo")
def obtener_logs_archivo():
    try:
        with open(LOG_PATH, "r") as f:
            lineas = f.readlines()

        return {
            "logs": [line.strip() for line in lineas[-20:]]
        }

    except FileNotFoundError:
        return {"error": "Archivo de log no encontrado"}