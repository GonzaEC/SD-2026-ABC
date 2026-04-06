import sys
import json
import requests
import logging
import os

#El cliente es el que manda pedidos al servidor

# Creo la carpeta de logs y defino como se van a guardar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "cliente.log")),
        logging.StreamHandler()
    ]
)

URL_SERVIDOR = "http://127.0.0.1:7685"

# Funcion principal, arma y envia la tarea
def enviar_tarea(tipo, calculo, parametros, adicional, imagen):
    """
    Envía una tarea al servidor.
    
    tipo: GET / POST / METODOS
    calculo: tipo de operación (suma, resta, etc)
    parametros: lista de números (string JSON)
    adicional: info extra (no usado)
    imagen: nombre de imagen docker
    """

    # Validar parámetros, los transformo en formaton json
    try:
        parametros = json.loads(parametros) if parametros else []
    except:
        logging.error("Parametros mal formados. Deben ser JSON válido. Ej: [2,3]")
        return

    try:
        adicional = json.loads(adicional) if adicional else []
    except:
        adicional = []

    # Armo la tarea
    tarea = {
        "calculo": calculo,
        "parametros": parametros,
        "adicional": adicional,
        "imagen": imagen
    }

    try:
        # Envio tarea al servidor
        if tipo == "POST":
            response = requests.post(
                f"{URL_SERVIDOR}/getRemoteTask",
                json=tarea,
                timeout=10
            )

        # Manda datos por URL
        elif tipo == "GET":
            response = requests.get(
                f"{URL_SERVIDOR}/getRemoteTask",
                params=tarea,
                timeout=10
            )
        
        #Obtiene los metodos que soporta el servidor
        elif tipo == "METODOS":
            response = requests.get(
                f"{URL_SERVIDOR}/getMetodos",
                params={"imagen": imagen},
                timeout=10
            )

        else:
            logging.error("Tipo de solicitud inválido")
            return

        # Convierte la respuesta del servidor a json
        try:
            resultado = response.json()
        except:
            resultado = {"error": response.text}

        logging.info(f"Respuesta servidor: {resultado}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error de conexión: {e}")

if __name__ == "__main__":

    """
    Uso:
    python cliente.py POST suma "[2,3]" "[]" servicio-tarea:1.0
    python cliente.py METODOS servicio-tarea:1.0
    """

    if len(sys.argv) < 2:
        print("Uso incorrecto")
        sys.exit(1)

    tipo = sys.argv[1]

    if tipo == "METODOS":
        if len(sys.argv) != 3:
            print("Uso: python cliente.py METODOS <imagen>")
            sys.exit(1)

        enviar_tarea(tipo, None, None, None, sys.argv[2])

    else:
        if len(sys.argv) != 6:
            print("Uso: python cliente.py POST suma \"[2,3]\" \"[]\" servicio-tarea:1.0")
            sys.exit(1)

        enviar_tarea(
            tipo,
            sys.argv[2],
            sys.argv[3],
            sys.argv[4],
            sys.argv[5]
        )