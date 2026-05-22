"""
Operador de Sobel Master-Worker con tolerancia a fallos - Proceso Distribuido
========================================
Aplica el operador de Sobel a fragmentos de una imagen y las unifica para detección de bordes.

Uso:
    python ProcesoPrincipalM.py <PATH_IMAGEN> <PATH_OUTPUT>

Ejemplo:
    python ProcesoPrincipalM.py /TP3/Hit1/FondoCristiano.jpg output.jpg
"""

import sys
import os
import subprocess
from PIL import Image
from fastapi import FastAPI
import requests
import uvicorn
import threading
import os
import logging
import sys
from PIL import Image
import io
import pika
import json
from splitter import Splitter
from joiner import Joiner
import time
from pathlib import Path
import queue
from dotenv import load_dotenv
from pathlib import Path
import socket

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
TERRAFORM_DIR = "./terraform"
TIMEOUT = 20
tareas = {}
cola_publicaciones = queue.Queue()
workers = 0



os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "ProcesoPrincipalM.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

app = FastAPI()
@app.get("/health")
def health():
    return {
        "splitter": "running",
        "joiner": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9013)

def build_output_path(input_path: str) -> str:
    """Genera el nombre de salida agregando '_sobel' antes de la extensión."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_sobel{ext if ext else '.png'}"




def terraform_init():
    
    logging.info("iniciando Terraform")

    subprocess.run(
        ["terraform", "init"],
        cwd=TERRAFORM_DIR,
        check=True
    )


def crear_workers(cantidad_workers):
    
    logging.info(f"Creando {cantidad_workers} workers...")

    subprocess.run(
        [
            "terraform",
            "apply",
            "-auto-approve",
            "-var",
            f"worker_count={cantidad_workers}"
        ],
        cwd=TERRAFORM_DIR,
        check=True
    )

    logging.info("Workers creados")


def destruir_workers():

    logging.info("Destruyendo workers...")

    subprocess.run(
        [
            "terraform",
            "destroy",
            "-auto-approve"
        ],
        cwd=TERRAFORM_DIR,
        check=True
    )

    logging.info("Workers destruidos")


def obtener_ips_workers():

    resultado = subprocess.check_output(
        [
            "terraform",
            "output",
            "-json"
        ],
        cwd=TERRAFORM_DIR
    )

    data = json.loads(resultado)

    ips = data["worker_ips"]["value"]

    return ips

def obtener_ip_rabbit():

    resultado = subprocess.check_output(
        [
            "terraform",
            "output",
            "-json"
        ],
        cwd=TERRAFORM_DIR
    )

    data = json.loads(resultado)

    ip = data["rabbitmq_ip"]["value"]

    return ip


def esperar_workers(ips, timeout=500):

    inicio = time.time()

    workers_ok = set()

    while True:

        for ip in ips:

            if ip in workers_ok:
                continue

            try:

                url = f"http://{ip}:8000/health"

                response = requests.get(
                    url,
                    timeout=5
                )

                if response.status_code == 200:

                    logging.info(f"Worker activo: {ip}")

                    workers_ok.add(ip)

            except Exception:

                logging.info(f"Worker no disponible todavía: {ip}")

        if len(workers_ok) == len(ips):

            logging.info("Todos los workers están listos")

            return True

        if time.time() - inicio > timeout:

            raise TimeoutError("Timeout esperando workers")

        time.sleep(5)

def esperar_rabbit(host, port=5672, timeout=300):

    inicio = time.time()

    while True:

        try:

            with socket.create_connection((host, port), timeout=5):

                logging.info("RabbitMQ disponible")

                return

        except Exception as e:

            logging.info(f"RabbitMQ no disponible: {e}")

        if time.time() - inicio > timeout:

            raise TimeoutError("Timeout esperando RabbitMQ")

        time.sleep(5)

def main(): 
    # ── Validar argumentos ───────────────────────────────────────────────────
    if len(sys.argv) < 2:
        log.info(__doc__)
        sys.exit(1)
    
    input_path  = Path(sys.argv[1]).resolve()
    output_path = sys.argv[2] if len(sys.argv) >= 3 else build_output_path(input_path)
    
    
    if not input_path.is_file():
        log.info(f"[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)
    
    threading.Thread(target=iniciar_api, daemon=True).start()
    # ── Procesar ─────────────────────────────────────────────────────────────
    log.info(f"Leyendo imagen:  {input_path}")
    image = Image.open(input_path)
    log.info(f"Tamaño:          {image.size[0]}×{image.size[1]} px  |  Modo: {image.mode}")

    
    try:
        terraform_init()

        crear_workers(3)

        ips = obtener_ips_workers()

        logging.info(f"IPs workers: {ips}")

        esperar_workers(ips)

        workers = len(ips)
        rabbitmq_ip = obtener_ip_rabbit()
        os.environ["RABBITMQ_HOST"] = rabbitmq_ip

        esperar_rabbit(rabbitmq_ip)

        #iniciamos el splitter 
        splitter = Splitter(tareas, cola_publicaciones, workers)
        threading.Thread(target=splitter_publicar, daemon=True).start()

        #iniciamos el joiner
        joiner = Joiner(tareas,output_path)
        joinerThread = threading.Thread(target=joiner.main,  daemon=False)
        joinerThread.start()
        #iniciamos el loop del proceso principal
        threading.Thread(target=loop, daemon=True).start()

        #iniciamos el splitter
        splitter.procesar(image)
        joinerThread.join()
    except KeyboardInterrupt:
        log.info("Interrupcion por teclado, cerrando...")
    finally:
        destruir_workers()
        
    
    

def loop():
    while True:
        for i, t in list(tareas.items()):
            if t["estado"] == "pendiente" and time.monotonic() - t["t0"] > TIMEOUT:
                log.info("[Splitter] se detecto fallo en un worker")
                t["t0"] = time.monotonic()
                log.info(f"[Splitter] Reenviando tarea {i}")
        time.sleep(1)

def splitter_publicar():
    #establecemos la conexion del splitter con rabbitMQ
    credencial= pika.PlainCredentials(os.environ["RABBITMQ_USER"],
    os.environ["RABBITMQ_PASS"])
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=os.environ["RABBITMQ_HOST"],
                                port = 5672,
                                credentials=credencial)
    )
    
    channel = connection.channel()
    # Declarar la cola (durable=True para que sobreviva reinicios)
    channel.queue_declare(queue='tareas', durable=True)

    while True:
        try:
            payload = cola_publicaciones.get(timeout=1)

            channel.basic_publish(
                    exchange='',           # exchange vacío = direct a la cola
                    routing_key='tareas',  # nombre de la cola destino
                    body=json.dumps(payload),
                    properties=pika.BasicProperties(
                        delivery_mode=2,   # mensaje persistente (sobrevive reinicios)
                    )
                )
            
            log.info(f"[Splitter] Enviado a Worker")
        except queue.Empty:
            pass
        
    

if __name__ == '__main__':
    main()