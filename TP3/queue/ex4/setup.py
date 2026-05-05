"""
Ejemplo 4 - Retry con Exponential Backoff
Setup: crea toda la infraestructura de colas necesaria para el retry.

Estrategia (sin plugin delayed): usar colas de espera con TTL.
Para cada delay (1s, 2s, 4s, 8s) se crea una cola intermedia con TTL.
Cuando el TTL expira, el mensaje vuelve a la cola principal (vía DLX).

Infraestructura:
  - cola_trabajo         → cola principal donde se procesan los mensajes
  - cola_espera_1s       → TTL 1000ms, expira → cola_trabajo
  - cola_espera_2s       → TTL 2000ms, expira → cola_trabajo
  - cola_espera_4s       → TTL 4000ms, expira → cola_trabajo
  - cola_espera_8s       → TTL 8000ms, expira → cola_trabajo
  - cola_muertos_retry   → DLQ final para mensajes que agotaron reintentos
"""
import pika
import os
import time

# Usar variable de entorno K8S
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

DELAYS_MS = [1000, 2000, 4000, 8000]

# Retry de conexion
def conectar():
    while True:
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
        except Exception as e:
            print("[Setup] Esperando RabbitMQ...", e)
            time.sleep(3)

def setup():
    connection = conectar()
    channel = connection.channel()

    # Exchange principal
    channel.exchange_declare(
        exchange='retry_exchange',
        exchange_type='direct',
        durable=True
    )
    print("[Setup] Exchange 'retry_exchange' creado.")

    # DLX
    channel.exchange_declare(
        exchange='retry_dlx',
        exchange_type='direct',
        durable=True
    )
    print("[Setup] Exchange DLX 'retry_dlx' creado.")

    # DLQ final
    channel.queue_declare(queue='cola_muertos_retry', durable=True)
    channel.queue_bind(
        queue='cola_muertos_retry',
        exchange='retry_dlx',
        routing_key='muerto'
    )
    print("[Setup] DLQ creada.")

    # cola principal
    channel.queue_declare(queue='cola_trabajo', durable=True)
    channel.queue_bind(
        queue='cola_trabajo',
        exchange='retry_exchange',
        routing_key='trabajo'
    )
    print("[Setup] cola_trabajo creada.")

    # colas de espera
    for delay_ms in DELAYS_MS:
        delay_s = delay_ms // 1000
        nombre = f'cola_espera_{delay_s}s'

        channel.queue_declare(
            queue=nombre,
            durable=True,
            arguments={
                'x-message-ttl': delay_ms,
                'x-dead-letter-exchange': 'retry_exchange',
                'x-dead-letter-routing-key': 'trabajo',
            }
        )

        print(f"[Setup] {nombre} creada")

    connection.close()
    print("\n[Setup] OK COMPLETO")

if __name__ == "__main__":
    setup()