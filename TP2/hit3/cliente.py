import time
import logging
import os
import ast
import sys
import requests

# -------------------
# Carpeta de logs
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit3_cliente.log")),
        logging.StreamHandler()
    ]
)

SERVIDOR_URL = os.environ.get("SERVIDOR_URL", "http://localhost:7685")

tarea = {
    "calculo": "vacio",
    "parametros": "vacio",
    "adicional": {
        "redondeo": -1,
        "absoluto": False
    },
    "imagen": "imagen docker"
}


def ver_estado_cluster():
    """[HIT3] Muestra el estado de cada nodo (quién es coordinador)."""
    for puerto in [8001, 8002, 8003]:
        try:
            r = requests.get(f"http://localhost:{puerto}/bully/status", timeout=2)
            data = r.json()
            logging.info(
                f"Nodo {data['node_id']} — coordinador: {data['coordinator_id']} — en elección: {data['in_election']}"
            )
        except Exception:
            logging.warning(f"Nodo en puerto {puerto} no responde")


def main(tipoSolicitud, calculo, parametros, adicional, imagen):
    tarea["calculo"] = calculo
    tarea["parametros"] = parametros
    tarea["imagen"] = imagen
    adicionalT = tarea["adicional"]

    if tipoSolicitud != "METODOS" and adicional:
        lista = ast.literal_eval(adicional)
        if len(lista) > 1:
            adicionalT["redondeo"] = lista[0]
            adicionalT["absoluto"] = lista[1]

    logging.info(f"[HIT3] Enviando solicitud {tipoSolicitud} al load balancer {SERVIDOR_URL}")

    ver_estado_cluster()

    try:
        if tipoSolicitud == "GET":
            peticion = requests.get(
                f"{SERVIDOR_URL}/getRemoteTask",
                params={
                    "calculo": calculo,
                    "parametros": parametros,
                    "adicional": adicional,
                    "imagen": imagen
                },
                stream=True
            )
        elif tipoSolicitud == "POST":
            peticion = requests.post(
                f"{SERVIDOR_URL}/getRemoteTask",
                json=tarea,
                stream=True
            )
        elif tipoSolicitud == "METODOS":
            peticion = requests.get(
                f"{SERVIDOR_URL}/getMetodos",
                params={"imagen": imagen},
                stream=True
            )
        else:
            logging.error(f"Tipo de solicitud desconocido: {tipoSolicitud}")
            return

        resultado = peticion.json()
        logging.info(f"Resultado: {resultado}")

    except Exception as e:
        logging.error(f"Error al conectar con el servidor: {e}")


if __name__ == "__main__":


    if len(sys.argv) == 2 and sys.argv[1] == "STATUS":
        ver_estado_cluster()
    elif len(sys.argv) == 6:
        tipoSolicitud = sys.argv[1]
        calculo = sys.argv[2]
        parametros = sys.argv[3]
        adicional = sys.argv[4]
        imagen = sys.argv[5]
        main(tipoSolicitud, calculo, parametros, adicional, imagen)
    elif len(sys.argv) == 3 and sys.argv[1] == "METODOS":
        main(sys.argv[1], None, None, None, sys.argv[2])
    else:
        print("Uso:")
        print("  python cliente.py GET <calculo> <parametros> <adicional> <imagen>")
        print("  python cliente.py POST <calculo> <parametros> <adicional> <imagen>")
        print("  python cliente.py METODOS <imagen>")
        print("  python cliente.py STATUS")