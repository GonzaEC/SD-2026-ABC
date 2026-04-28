"""
Parte 2 - Joiner
Joiner: Recibe N partes resultado y las une.
"""

import pika
import time
from fastapi import FastAPI
import uvicorn
import threading
import os
import logging
import json
import base64
from PIL import Image
import io
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
N = 8
output_path = sys.argv[1]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "joiner.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

app = FastAPI()
@app.get("/health")
def health():
    return {
        "servicio": "joiner",
        "status": "running"
    }

def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=9001)
listaFragmentos = []
def calcularHeight(lista: list):
    resultado = 0
    for i in range(len(lista)):
        img_bytesActual = base64.b64decode(lista[i]["resultado"])
        imgActual = Image.open(io.BytesIO(img_bytesActual))
        resultado += imgActual.height
    return resultado
     
def joinResultado(ch, method, properties, body):
    mensaje = json.loads(body)
    log.info(f"[Joiner] Recibido: {mensaje}")
    
    #procesar fragmento
    listaFragmentos.append(mensaje)
    if(mensaje["fragmentos"] == len(listaFragmentos)):
        img_bytes = base64.b64decode(mensaje["resultado"])
        img = Image.open(io.BytesIO(img_bytes))
        result = Image.new("L", (img.width, calcularHeight(listaFragmentos)))
        y_actual = 0
        for i in range(len(listaFragmentos)):
            for j in range(len(listaFragmentos)):
                actual = listaFragmentos[j]
                if actual["indice"] == i:
                    img_bytesActual = base64.b64decode(actual["resultado"])
                    imgActual = Image.open(io.BytesIO(img_bytesActual))
                    result.paste(imgActual,(0,y_actual))
                    y_actual += imgActual.height
        result.save(output_path)
        log.info(f"[Joiner] Imagen guardada: {output_path}")
        print("¡Listo!")
        # Confirmar que el mensaje fue procesado correctamente (ACK manual)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        log.info(f"[Joiner] imagen en proceso")
    
    
    

def build_output_path(input_path: str) -> str:
        """Genera el nombre de salida agregando '_sobel' antes de la extensión."""
        base, ext = os.path.splitext(input_path)
        return f"{base}_sobel{ext if ext else '.png'}"

def main():

     
    threading.Thread(target=iniciar_api, daemon=True).start()

    # Conectar al broker
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Declarar la misma cola que el productor (idempotente)
    channel.queue_declare(queue='resultado', durable=True)

    # prefetch_count=1: no enviar más de 1 mensaje a este worker hasta recibir ACK
    # Esto asegura distribución justa (fair dispatch) entre múltiples consumidores
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue='resultado',
        on_message_callback=joinResultado,
        auto_ack=True  # ACK automatico
    )
    

    log.info(f"[Joiner] Esperando mensajes...")
   
    channel.start_consuming()
    

if __name__ == '__main__':
    main()
