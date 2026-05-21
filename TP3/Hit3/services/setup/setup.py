"""
Hit3 - Setup de infraestructura RabbitMQ
Crea todos los exchanges, queues y bindings necesarios:
  - DLX (Dead Letter Exchange) para fragmentos fallidos
  - DLQ tareas_muertos
  - Colas de espera para retry con exponential backoff (1s, 2s, 4s, 8s, 30s)
  - Exchange fanout para Pub/Sub de resultados
  - Colas de resultados para joiner y monitor
"""

import pika
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

RETRY_DELAYS_MS = [1000, 2000, 4000, 8000, 30000]


def conectar():
    while True:
        try:
            credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            return pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credenciales)
            )
        except Exception as e:
            print(f"[Setup] Esperando RabbitMQ... {e}")
            time.sleep(3)


def setup():
    connection = conectar()
    channel = connection.channel()

    # ── Exchange principal para tareas ────────────────────────────────────────
    channel.exchange_declare(
        exchange="tareas_exchange",
        exchange_type="direct",
        durable=True,
    )
    print("[Setup] Exchange 'tareas_exchange' creado.")

    # ── DLX: Dead Letter Exchange para fragmentos fallidos ────────────────────
    channel.exchange_declare(
        exchange="sobel_dlx",
        exchange_type="direct",
        durable=True,
    )
    print("[Setup] Exchange DLX 'sobel_dlx' creado.")

    # ── DLQ: cola donde llegan los fragmentos que fallaron ────────────────────
    channel.queue_declare(queue="tareas_muertos", durable=True)
    channel.queue_bind(
        queue="tareas_muertos",
        exchange="sobel_dlx",
        routing_key="fragmento_fallido",
    )
    print("[Setup] DLQ 'tareas_muertos' creada y enlazada a sobel_dlx.")

    # ── Cola principal de tareas con DLX configurado ──────────────────────────
    # Si un worker hace NACK(requeue=False), el mensaje va a sobel_dlx → tareas_muertos
    channel.queue_declare(
        queue="tareas",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "sobel_dlx",
            "x-dead-letter-routing-key": "fragmento_fallido",
        },
    )
    channel.queue_bind(
        queue="tareas",
        exchange="tareas_exchange",
        routing_key="tarea",
    )
    print("[Setup] Cola 'tareas' creada con DLX configurado.")

    # ── Colas de espera para retry con exponential backoff ────────────────────
    # Estrategia sin plugin delayed: TTL + DLX que devuelve a tareas_exchange.
    # Cuando expira el TTL, el mensaje vuelve a la cola principal.
    for delay_ms in RETRY_DELAYS_MS:
        delay_s = delay_ms // 1000
        nombre = f"tareas_espera_{delay_s}s"

        channel.queue_declare(
            queue=nombre,
            durable=True,
            arguments={
                "x-message-ttl": delay_ms,
                "x-dead-letter-exchange": "tareas_exchange",
                "x-dead-letter-routing-key": "tarea",
            },
        )
        print(f"[Setup] Cola de espera '{nombre}' creada (TTL={delay_ms}ms).")

    # ── Exchange fanout para Pub/Sub de resultados ────────────────────────────
    # Cuando un worker completa un fragmento, publica aquí.
    # Tanto el joiner como el monitor reciben la notificación.
    channel.exchange_declare(
        exchange="resultados_exchange",
        exchange_type="fanout",
        durable=True,
    )
    print("[Setup] Exchange fanout 'resultados_exchange' creado.")

    # Cola del joiner (reconstrucción de imagen)
    channel.queue_declare(queue="resultados_joiner", durable=True)
    channel.queue_bind(queue="resultados_joiner", exchange="resultados_exchange")
    print("[Setup] Cola 'resultados_joiner' enlazada al fanout.")

    # Cola del monitor (observabilidad / dashboard)
    channel.queue_declare(queue="resultados_monitor", durable=True)
    channel.queue_bind(queue="resultados_monitor", exchange="resultados_exchange")
    print("[Setup] Cola 'resultados_monitor' enlazada al fanout.")

    connection.close()
    print("\n[Setup] OK COMPLETO")


if __name__ == "__main__":
    setup()
