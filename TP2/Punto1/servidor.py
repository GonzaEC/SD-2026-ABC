from fastapi import FastAPI, Request
import uvicorn
import time
import logging
import os
import subprocess
import json
import requests

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

# Estado del servicio
estado_servicio = {
    "Servidor": "Iniciado",
}

payload = {
    "calculo": "vacio",
    "parametros": "vacio",
    "adicional": {
    "redondeo": -1,
    "absoluto": False
    },
    "imagen": "imagen docker"
}
adicional = {
    "redondeo": -1,
    "absoluto": False
}
app = FastAPI()
tiempoInicio = time.time()
logging.info(f"Se inicio correctamente el servidor")
estado_servicio["Servidor"] = "OK"
    
@app.get("/getRemoteTask")
async def ejecutarTareaRemota(calculo,parametros,redondeo,absoluto,imagen):
    payload["calculo"] = calculo
    payload["parametros"] = parametros
    payload["imagen"] = imagen
    adicional["redondeo"] = int(redondeo)
    if(absoluto == "True"):
        adicional["absoluto"] = True 
    else:
        adicional["absoluto"] = False
    
    payload["adicional"] = adicional
    logging.info(f"Se esta procesando una nueva tarea mediante GET: %s",payload)
    procesoActual = subprocess.run(
        ["docker","run","-d","--network","red_docker","-i","--name","servicio-tarea" ,"-p","8132:8132",imagen],
        capture_output=True,
        text=True
    )
    if procesoActual.returncode != 0:
                #En caso que el contenedor ya este en uso pero en estado exited simplemente lo inicia
        procesoActual = subprocess.run(
        ["docker","start","servicio-tarea"],
        capture_output=True,
        text=True
        )
        if procesoActual.returncode != 0:
            return {"estado": "error", "detalle": procesoActual.stderr}
    
    time.sleep(2)
    peticion = requests.post("http://servicio-tarea:8132/ejecutarTarea",json=payload, stream = True)
    procesoActual = subprocess.run(
        ["docker","stop","servicio-tarea"],
        capture_output=True,
        text=True
    )
    try:
        return peticion.json()
    except:
        return {
            "estado": "error",
            "detalle": peticion.text 
        }

@app.post("/getRemoteTask")
async def ejecutarTareaRemota(peticion: Request):
    payload = await peticion.json()
    imagen = payload["imagen"]
    logging.info(f"Se esta procesando una nueva tarea mediante POST: %s",payload)
    procesoActual = subprocess.run(
        ["docker","run","-d","--network","red_docker","-i","--name","servicio-tarea" ,"-p","8132:8132",imagen],
        capture_output=True,
        text=True
    )
    if procesoActual.returncode != 0:
                #En caso que el contenedor ya este en uso pero en estado exited simplemente lo inicia
        procesoActual = subprocess.run(
        ["docker","start","servicio-tarea"],
        capture_output=True,
        text=True
        )
        if procesoActual.returncode != 0:
            return {"estado": "error", "detalle": procesoActual.stderr}
    time.sleep(2)
    peticion = requests.post("http://servicio-tarea:8132/ejecutarTarea",json=payload, stream = True)
    procesoActual = subprocess.run(
        ["docker","stop","servicio-tarea"],
        capture_output=True,
        text=True
    )
    try:
        return peticion.json()
    except:
        return {
            "estado": "error",
            "detalle": peticion.text 
        }


@app.get("/health")
def estado_Actual():
    tiempoActual = time.time() - tiempoInicio
    estado = {
        "uptime": tiempoActual,
        "Estado": estado_servicio["Servidor"]
    }
    return estado

@app.get("/getMetodos")
async def obtenerMetodos(imagen):
    logging.info(f"Se estan solicitando los metodos")
    procesoActual = subprocess.run(
        ["docker","run","-d","--network","red_docker","-i","--name","servicio-tarea" ,"-p","8132:8132",imagen],
        capture_output=True,
        text=True
    )
    if procesoActual.returncode != 0:
        #En caso que el contenedor ya este en uso pero en estado exited simplemente lo inicia
        procesoActual = subprocess.run(
        ["docker","start","servicio-tarea"],
        capture_output=True,
        text=True
        )
        if procesoActual.returncode != 0:
            return {"estado": "error", "detalle": procesoActual.stderr}
    
    time.sleep(2)
    peticion = requests.get("http://servicio-tarea:8132/getMetodos", stream = True)
    procesoActual = subprocess.run(
        ["docker","stop","servicio-tarea"],
        capture_output=True,
        text=True
    )
    try:
        return peticion.json()
    except:
        return {
            "estado": "error",
            "detalle": peticion.text 
        }
