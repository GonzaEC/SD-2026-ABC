"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Setup infraestructura RabbitMQ + DLX
"""

import pika
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

def conectar():
    while True:
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
        except:
            time.sleep(3)

def setup():
    connection = conectar()
    channel = connection.channel()

    # DLX
    channel.exchange_declare(
        exchange='dlx_exchange',
        exchange_type='direct',
        durable=True
    )

    # DLQ
    channel.queue_declare(queue='cola_muertos', durable=True)
    channel.queue_bind(
        queue='cola_muertos',
        exchange='dlx_exchange',
        routing_key='mensajes_fallidos'
    )

    # cola principal con DLX
    channel.queue_declare(
        queue='cola_principal',
        durable=True,
        arguments={
            'x-dead-letter-exchange': 'dlx_exchange',
            'x-dead-letter-routing-key': 'mensajes_fallidos'
        }
    )

    connection.close()
    print("[Setup] DLQ configurada correctamente")

if __name__ == "__main__":
    setup()