from fastapi import FastAPI, Request
import uvicorn
import time
import logging
import os
import subprocess
import json
import requests
import threading  # [HIT3]
from bully import BullyNode  # [HIT3]

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
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit3.log")),
        logging.StreamHandler()
    ]
)

# -------------------
# [HIT3] Configuración del nodo desde variables de entorno
# -------------------
NODE_ID = int(os.environ.get("NODE_ID", 1))


def parse_peers(raw: str) -> list[dict]:
    peers = []
    if not raw:
        return peers
    for entry in raw.split(";"):
        parts = entry.strip().split(",")
        if len(parts) == 2:
            peers.append({"id": int(parts[0]), "url": parts[1]})
    return peers

PEERS_RAW = os.environ.get("PEERS", "")
PEERS = parse_peers(PEERS_RAW)

# -------------------
# Estado del servicio
# -------------------
estado_servicio = {"Servidor": "Iniciado"}

payload = {
    "calculo": "vacio",
    "parametros": "vacio",
    "adicional": {
        "redondeo": -1,
        "absoluto": False
    },
    "imagen": "imagen docker"
}

app = FastAPI()
tiempoInicio = time.time()
logging.info(f"Servidor iniciado — Nodo {NODE_ID}")
estado_servicio["Servidor"] = "OK"

# -------------------
# [HIT3] Inicializar y arrancar Bully al levantar la app
# -------------------
bully_node = BullyNode(node_id=NODE_ID, peers=PEERS)

@app.on_event("startup")
async def startup_event():
    bully_node.start()
    logging.info(f"[HIT3] BullyNode iniciado para nodo {NODE_ID} con peers: {PEERS}")

# -------------------
# [HIT3] Endpoints del protocolo Bully
# -------------------

@app.post("/bully/election")
async def recibir_election(request: Request):
    """
    Otro nodo inició una elección. Si nuestro ID es mayor, respondemos OK
    y lanzamos nuestra propia elección en background.
    """
    body = await request.json()
    sender_id = body.get("sender_id")
    logging.info(f"[HIT3] ELECTION recibido de nodo {sender_id}")

    if NODE_ID > sender_id:
        threading.Thread(target=bully_node.start_election, daemon=True).start()
        return {"status": "OK", "from": NODE_ID}
    
    return {"status": "IGNORADO", "from": NODE_ID}

@app.post("/bully/coordinator")
async def recibir_coordinator(request: Request):
    """
    Alguien se proclamó coordinador. Actualizamos nuestro estado local.
    """
    body = await request.json()
    coordinator_id = body.get("coordinator_id")
    bully_node.receive_coordinator(coordinator_id)
    logging.info(f"[HIT3] COORDINATOR recibido: nodo {coordinator_id} es el líder")
    return {"status": "ACK"}

@app.get("/bully/status")
def estado_bully():
    """Ver el estado de la elección desde afuera."""
    return {
        "node_id": NODE_ID,
        "coordinator_id": bully_node.coordinator_id,
        "in_election": bully_node.in_election,
        "peers": PEERS
    }

# -------------------
# Endpoints originales del Hit #1 (sin cambios)
# -------------------

@app.get("/getRemoteTask")
async def ejecutarTareaRemota(calculo, parametros, adicional, imagen):
    payload["calculo"] = calculo
    payload["parametros"] = parametros
    payload[imagen] = imagen
    logging.info(f"[GET] Nueva tarea — nodo {NODE_ID}: {payload}")
    procesoActual = subprocess.run(
        ["docker", "run", "-d", "--network", "red_docker", "-i", "--name", "servicio-tarea", "-p", "8132:8132", imagen],
        capture_output=True, text=True
    )
    if procesoActual.returncode != 0:
        procesoActual = subprocess.run(
            ["docker", "start", "servicio-tarea"],
            capture_output=True, text=True
        )
        if procesoActual.returncode != 0:
            return {"estado": "error", "detalle": procesoActual.stderr}

    time.sleep(2)
    peticion = requests.post("http://servicio-tarea:8132/ejecutarTarea", json=payload, stream=True)
    subprocess.run(["docker", "stop", "servicio-tarea"], capture_output=True, text=True)
    try:
        return peticion.json()
    except:
        return {"estado": "error", "detalle": peticion.text}


@app.post("/getRemoteTask")
async def ejecutarTareaRemotaPost(peticion: Request):
    payload = await peticion.json()
    imagen = payload["imagen"]
    logging.info(f"[POST] Nueva tarea — nodo {NODE_ID}: {payload}")
    procesoActual = subprocess.run(
        ["docker", "run", "-d", "--network", "red_docker", "-i", "--name", "servicio-tarea", "-p", "8132:8132", imagen],
        capture_output=True, text=True
    )
    if procesoActual.returncode != 0:
        procesoActual = subprocess.run(
            ["docker", "start", "servicio-tarea"],
            capture_output=True, text=True
        )
        if procesoActual.returncode != 0:
            return {"estado": "error", "detalle": procesoActual.stderr}

    time.sleep(2)
    peticion = requests.post("http://servicio-tarea:8132/ejecutarTarea", json=payload, stream=True)
    subprocess.run(["docker", "stop", "servicio-tarea"], capture_output=True, text=True)
    try:
        return peticion.json()
    except:
        return {"estado": "error", "detalle": peticion.text}


@app.get("/health")
def estado_Actual():
    tiempoActual = time.time() - tiempoInicio
    return {
        "uptime": tiempoActual,
        "Estado": estado_servicio["Servidor"],
        "node_id": NODE_ID,                          # [HIT3]
        "coordinator_id": bully_node.coordinator_id  # [HIT3]
    }


@app.get("/getMetodos")
async def obtenerMetodos(imagen):
    logging.info("Solicitando métodos disponibles")
    procesoActual = subprocess.run(
        ["docker", "run", "-d", "--network", "red_docker", "-i", "--name", "servicio-tarea", "-p", "8132:8132", imagen],
        capture_output=True, text=True
    )
    if procesoActual.returncode != 0:
        procesoActual = subprocess.run(
            ["docker", "start", "servicio-tarea"],
            capture_output=True, text=True
        )
        if procesoActual.returncode != 0:
            return {"estado": "error", "detalle": procesoActual.stderr}

    time.sleep(2)
    peticion = requests.get("http://servicio-tarea:8132/getMetodos", stream=True)
    subprocess.run(["docker", "stop", "servicio-tarea"], capture_output=True, text=True)
    try:
        return peticion.json()
    except:
        return {"estado": "error", "detalle": peticion.text}