"""
Ejemplo 4 - Retry con Exponential Backoff
Consumidor: intenta procesar mensajes. Si falla (50% probabilidad), los
reencola con delay creciente. Después de 4 intentos fallidos → DLQ.

Secuencia de delays: 1s → 2s → 4s → 8s → DLQ
"""

import pika
import json
import random
import time
import logging
import threading
from fastapi import FastAPI
import uvicorn
import os

# LOGGING
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "consumidor.log")),
        logging.StreamHandler()
    ]
)
logging.getLogger("pika").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

# HEALTH ENDPOINT
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "service": "consumidor-retry"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8003)


# Delays en segundos para cada intento (exponential backoff)
DELAYS = [1, 2, 4, 8]
MAX_INTENTOS = 4

def simular_procesamiento():
    """Simula un procesamiento que falla con 50% de probabilidad."""
    return random.random() > 0.5  # True = éxito, False = fallo

def encolar_con_delay(channel, mensaje, intento_actual):
    """Publica el mensaje en la cola de espera correspondiente al intento."""
    delay_s = DELAYS[intento_actual - 1]
    cola_espera = f'cola_espera_{delay_s}s'

    mensaje['intentos'] = intento_actual

    log.info(f"[Retry] Reintento #{intento_actual}: esperando {delay_s}s en '{cola_espera}'")

    # Publicar en la cola de espera (sin pasar por el exchange)
    channel.basic_publish(
        exchange='',          # direct a la cola de espera
        routing_key=cola_espera,
        body=json.dumps(mensaje),
        properties=pika.BasicProperties(delivery_mode=2)
    )

def enviar_a_dlq(channel, mensaje):
    """Envía el mensaje a la DLQ final cuando se agotan los reintentos."""
    log.error(f"[DLQ] Tarea #{mensaje['id']} enviada a DLQ")

    channel.basic_publish(
        exchange='retry_dlx',
        routing_key='muerto',
        body=json.dumps(mensaje),
        properties=pika.BasicProperties(delivery_mode=2)
    )

def procesar_mensaje(ch, method, properties, body):
    mensaje = json.loads(body.decode())
    tarea_id = mensaje['id']
    intentos_previos = mensaje.get('intentos', 0)
    intento_actual = intentos_previos + 1

    log.info("========================================")
    log.info(f"[Task {tarea_id}], Intento #{intento_actual} de {MAX_INTENTOS}")

    # Simular el procesamiento
    exito = simular_procesamiento()

    if exito:
        log.info(f"[Task {tarea_id}] OK en intento #{intento_actual}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        log.warning(f"[Task {tarea_id}] FALLO en intento #{intento_actual}")

        if intento_actual < MAX_INTENTOS:
            # Hay reintentos disponibles → encolar con delay
            encolar_con_delay(ch, mensaje, intento_actual)
            # ACK para sacar de la cola principal (ya está en la cola de espera)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # Agotados todos los reintentos → DLQ
            log.error(f"Tarea #{tarea_id}: agotados {MAX_INTENTOS} intentos, va a DLQ")
            mensaje['intentos'] = intento_actual
            enviar_a_dlq(ch, mensaje)
            ch.basic_ack(delivery_tag=method.delivery_tag)

def consumidor_dlq(ch, method, properties, body):
    """Consumidor de la DLQ - registra los mensajes que no pudieron procesarse."""
    mensaje = json.loads(body.decode())
    log.error("========================================")
    log.error(f"[DLQ]    Mensaje muerto recibido:")
    log.error(f"[DLQ]    Tarea ID:    {mensaje['id']}")
    log.error(f"[DLQ]    Intentos:    {mensaje['intentos']}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    threading.Thread(target=run_api, daemon=True).start()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)

    # Consumidor principal
    channel.basic_consume(
        queue='cola_trabajo',
        on_message_callback=procesar_mensaje,
        auto_ack=False
    )

    # Consumidor DLQ (en el mismo proceso para simplificar)
    channel.basic_consume(
        queue='cola_muertos_retry',
        on_message_callback=consumidor_dlq,
        auto_ack=False
    )

    log.info("Consumidor activo. Escuchando 'cola_trabajo' y 'cola_muertos_retry'.")
    log.info("Delays configurados: 1s - 2s - 4s - 8s - DLQ")
    log.info("Probabilidad de fallo por intento: 50%")
    log.info("Ctrl+C para salir.\n")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        log.info("Consumidor detenido.")
        connection.close()

if __name__ == '__main__':
    main()
