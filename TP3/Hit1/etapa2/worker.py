"""
Ejemplo 1 - Message Queue (Punto a Punto)
Consumidor: recibe tareas de la cola 'tareas' y las procesa.

Uso:
  python consumidor.py          → consumidor sin identificador
  python consumidor.py A        → consumidor identificado como "A"
  python consumidor.py B        → consumidor identificado como "B"

Levantar 2 instancias en terminales distintas para observar round-robin:
  Terminal 1: python consumidor.py A
  Terminal 2: python consumidor.py B
  Luego ejecutar el productor y observar cómo se distribuyen los mensajes.
"""

import pika
import time
import sys
from fastapi import FastAPI
import uvicorn
import threading
import os
import logging
import json
import base64
from PIL import Image
import io
from sobel import sobel

# -------------------------
# LOGGING (MEMORIA + DISCO)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
mensaje_actual = {
        "indice": "indice",
        "resultado": "bytes de imagen resultado",
        "fragmentos": 0
    }

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "consumidor.log")),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

# -------------------------
# FASTAPI
# -------------------------
app = FastAPI()
WORKER_ID = os.getenv("sobel-worker", "unknown")
@app.get("/health")
def health():
    return {
        "servicio": WORKER_ID,
        "status": "running",
        "rabbitmq": "connected"
    }

def iniciar_api():
    puerto = 8000
    uvicorn.run(app, host="0.0.0.0", port=puerto)





def procesar_mensaje(ch, method, properties, body):
    mensaje = json.loads(body)
    log.info(f"[Worker {WORKER_ID}] Recibido: {mensaje}")
    
    #procesar sobel
    indice = mensaje["indice"]
    datos = base64.b64decode(mensaje["imagen"])
    imagen = Image.open(io.BytesIO(datos))
    resultado = sobel(imagen)
    log.info(f"[Worker {WORKER_ID}] Procesado: indice=%s fragmentos=%s imagen_bytes=%s",
            indice,
            mensaje["fragmentos"],
            len(mensaje["imagen"]))
    
    
    #luego se envia el resultado por la cola de resultados
    mensaje_actual["indice"] = indice
    mensaje_actual["resultado"] =  resultado
    mensaje_actual["fragmentos"] = mensaje["fragmentos"]
    
    # Conectar al broker
    connection = conectar_rabbit()
    channel2 = connection.channel()

    # Declarar la cola (durable=True para que sobreviva reinicios)
    channel2.queue_declare(queue='resultado', durable=True)

    log.info(f"[Worker {WORKER_ID}] Enviando resultados...")
    buffer = io.BytesIO()
    mensaje_actual["resultado"].save(buffer, format="PNG")
    img_bytes = base64.b64encode(buffer.getvalue()).decode()
    # ── Enviar Resultado ─────────────────────────────────────────────────────────────
    mensaje_actual["resultado"] = img_bytes
    

    
    channel2.basic_publish(
        exchange='',           # exchange vacío = direct a la cola
        routing_key='resultado',  # nombre de la cola destino
        body=json.dumps(mensaje_actual),
        properties=pika.BasicProperties(
            delivery_mode=2,   # mensaje persistente (sobrevive reinicios)
        )
    )
    log.info(f"[Worker {WORKER_ID}] Enviado a Joiner: {mensaje_actual}")
    # Confirmar que el mensaje fue procesado correctamente (ACK manual)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    
    
def conectar_rabbit():
    while True:
        try:
            credencial= pika.PlainCredentials("sobel_user", "sobel_pass")
            connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq',
                                  port = 5672,
                                  credentials=credencial)
            )
            log.info("Conectado a rabbitmq")
            return connection

        except pika.exceptions.AMQPConnectionError:
            log.info("rabbitmq no disponible, reintentando...")
            time.sleep(5)

def main():
    threading.Thread(target=iniciar_api, daemon=True).start()

    connection = conectar_rabbit()
    channel = connection.channel()

    # Declarar la misma cola que el productor (idempotente)
    channel.queue_declare(queue='tareas', durable=True)

    # prefetch_count=1: no enviar más de 1 mensaje a este worker hasta recibir ACK
    # Esto asegura distribución justa (fair dispatch) entre múltiples consumidores
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue='tareas',
        on_message_callback=procesar_mensaje,
        auto_ack=False  # ACK manual para mayor control 
        #en caso de que este worker caiga el splitter envia a otro worker la t
    )
    
    
    
    log.info(f"[Worker {WORKER_ID}] Health: http://sobel-worker:{8000}/health")
    
    log.info(f"[Worker {WORKER_ID}] Esperando mensajes...")
   
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info(f"[Worker {WORKER_ID}] Detenido.")
        
