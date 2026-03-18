from fastapi import FastAPI, Request
import uvicorn
import time
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
        logging.FileHandler(os.path.join(LOG_DIR, "hit6.log")),
        logging.StreamHandler()
    ]
)

# Estado del servicio
estado_servicio = {
    "Servidor": "Iniciado",
}

registro = []
app = FastAPI()
tiempoInicio = time.time()
def iniciar_servidor(IP,Puerto):
    uvicorn.run("nodoD:app",host=IP,port=Puerto,log_level="info")
    logging.info(f"Se inicio correctamente el nodo D")
    estado_servicio["Servidor"] = "OK"
    
@app.get("/REGISTER")
def registrarPrograma(peticion: Request):
    registro_actual = {
        "ip": peticion.client.host,
        "puerto": peticion.client.port
    }
    registro.append(registro_actual)
    logging.info(f"Se registro un nuevo nodo C")
    return {"nodosDisponibles": registro}

@app.get("/health")
def estado_Actual():
    tiempoActual = time.time() - tiempoInicio
    estado = {
        "Cantidad de nodos registrados": len(registro),
        "uptime": tiempoActual,
        "Estado": estado_servicio["Servidor"]
    }
    return estado

