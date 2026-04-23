"""
Ejemplo 3 - Dead Letter Queue (DLQ)
Setup: crea el exchange DLX, la DLQ y la cola principal con DLX configurado.

Ejecutar este script UNA VEZ antes de levantar productor y consumidores.
"""

import pika

def setup():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # 1. Dead Letter Exchange (DLX) - tipo direct
    channel.exchange_declare(
        exchange='dlx_exchange',
        exchange_type='direct',
        durable=True
    )
    print("[Setup] Exchange DLX 'dlx_exchange' creado.")

    # 2. Dead Letter Queue (DLQ) - recibe los mensajes rechazados
    channel.queue_declare(queue='cola_muertos', durable=True)
    channel.queue_bind(
        queue='cola_muertos',
        exchange='dlx_exchange',
        routing_key='mensajes_fallidos'  # routing key de la DLQ
    )
    print("[Setup] Cola DLQ 'cola_muertos' creada y vinculada al DLX.")

    # 3. Cola principal con DLX configurado
    # Cuando un mensaje es rechazado (nack sin requeue), va al DLX
    channel.queue_declare(
        queue='cola_principal',
        durable=True,
        arguments={
            'x-dead-letter-exchange': 'dlx_exchange',          # DLX a usar
            'x-dead-letter-routing-key': 'mensajes_fallidos'   # routing key destino
        }
    )
    print("[Setup] Cola principal 'cola_principal' creada con DLX configurado.")

    connection.close()
    print("\n[Setup] Infraestructura lista. Ahora ejecute productor.py y consumidor.py")

if __name__ == '__main__':
    setup()
