import socket
import time
import threading 
import sys
import json
import requests
import logging
import os
import ast

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

tarea = {
    "calculo": "vacio",
    "parametros": "vacio",
    "adicional": {
    "redondeo": -1,
    "absoluto": False
    },
    "imagen": "imagen docker"
}


def main(tipoSolicitud, calculo, parametros,adicional,imagen):
    tarea["calculo"] = calculo
    tarea["parametros"] = parametros
    tarea["imagen"] = imagen
    adicionalT = tarea["adicional"]
    if(tipoSolicitud != "METODOS"):
        lista = ast.literal_eval(adicional) #convierte el adicional tipo string a una lista para obtener los valores ingresados
        
        if(len(lista) > 1):
            adicionalT["redondeo"] = lista[0]
            adicionalT["absoluto"] = lista[1]
    logging.info("Nueva peticion de cliente")
    if(tipoSolicitud == "GET"):
        peticion = requests.get("http://localhost:7685/getRemoteTask",params= {
            "calculo":calculo,
            "parametros": parametros,
            "adicional": adicional,
            "imagen": imagen
        }, stream = True)
    if(tipoSolicitud == "POST"):
        peticion = requests.post("http://localhost:7685/getRemoteTask",json=tarea, stream = True)
    if(tipoSolicitud == "METODOS"):
        peticion = requests.get("http://localhost:7685/getMetodos",params= {"imagen":imagen}, stream = True)
    try:
        resultado = peticion.json()
    except:
        resultado = {
            "estado": "error",
            "detalle": peticion
        }
    logging.info(resultado)

if __name__ == "__main__":
    if(len(sys.argv) == 6):
        tipoSolicitud = sys.argv[1]
        calculo = sys.argv[2]
        parametros = sys.argv[3]
        adicional = sys.argv[4]
        imagen = sys.argv[5]
        main(tipoSolicitud,calculo,parametros,adicional,imagen) 
    if(sys.argv[1] == "METODOS"):
        main(sys.argv[1],None,None,None,sys.argv[2])
