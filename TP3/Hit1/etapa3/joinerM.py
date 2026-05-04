"""
Parte 3 - Joiner Mejorado
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
app = FastAPI()
log = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)
listaFragmentos = []
# Conectar al broker
credencial= pika.PlainCredentials("sobel_user", "sobel_pass")
connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost',
                                    port = 5672,
                                    credentials=credencial)
    )
channel = connection.channel()

class JoinerM:
   

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(LOG_DIR, "joiner.log")),
            logging.StreamHandler()
        ]
    )
    

    
    @app.get("/health")
    def health():
        return {
            "servicio": "joiner",
            "status": "running"
        }

    def iniciar_api(self):
        uvicorn.run(app, host="0.0.0.0", port=9001)

    

    def __init__(self, tareas,output_path):
        self.tareas = tareas
        self.output_path = output_path

    def calcularHeight(self,lista: list):
        resultado = 0
        for i in range(len(lista)):
            img_bytesActual = base64.b64decode(lista[i]["resultado"])
            imgActual = Image.open(io.BytesIO(img_bytesActual))
            resultado += imgActual.height
        return resultado
        
    def joinResultado(self, ch, method, properties, body):
        mensaje = json.loads(body)
        log.info(f"[Joiner] Recibido: indice=%s fragmentos=%s resultado_bytes=%s",
                mensaje["indice"],
                mensaje["fragmentos"],
                len(mensaje["resultado"]))
        indice = mensaje["indice"]
        if(indice in self.tareas):
            self.tareas[indice]["estado"] = "completado" #se marca como tarea recibida
        #procesar fragmento
        listaFragmentos.append(mensaje)
        if all(t["estado"] == "completado" for t in self.tareas.values()):
            img_bytes = base64.b64decode(mensaje["resultado"])
            img = Image.open(io.BytesIO(img_bytes))
            result = Image.new("L", (img.width, self.calcularHeight(listaFragmentos)))
            y_actual = 0
            for i in range(len(listaFragmentos)):
                for j in range(len(listaFragmentos)):
                    actual = listaFragmentos[j]
                    if actual["indice"] == i:
                        img_bytesActual = base64.b64decode(actual["resultado"])
                        imgActual = Image.open(io.BytesIO(img_bytesActual))
                        result.paste(imgActual,(0,y_actual))
                        y_actual += imgActual.height
                        
            result.save(self.output_path)
            log.info(f"[Joiner] Imagen guardada: {self.output_path}")
            print("¡Listo!")
            
            
        else:
            log.info(f"[Joiner] imagen en proceso")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        
        



    def main(self):

        
        threading.Thread(target=self.iniciar_api, daemon=True).start()

        
        

        # Declarar la misma cola que el productor (idempotente)
        channel.queue_declare(queue='resultado', durable=True)

        # prefetch_count=1: no enviar más de 1 mensaje a este worker hasta recibir ACK
        # Esto asegura distribución justa (fair dispatch) entre múltiples consumidores
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(
            queue='resultado',
            on_message_callback=self.joinResultado,
            auto_ack=False  # ACK automatico
        )
        

        log.info(f"[Joiner] Esperando mensajes...")
        
        channel.start_consuming()
        
        

    if __name__ == '__main__':
        main()
