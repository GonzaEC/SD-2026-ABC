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

DELAYS_MS = [1000, 2000, 4000, 8000]  # delays en milisegundos

def setup():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Exchange principal (direct) - para enrutar mensajes
    channel.exchange_declare(
        exchange='retry_exchange',
        exchange_type='direct',
        durable=True
    )
    print("[Setup] Exchange 'retry_exchange' creado.")

    # Exchange DLX para la DLQ final
    channel.exchange_declare(
        exchange='retry_dlx',
        exchange_type='direct',
        durable=True
    )
    print("[Setup] Exchange DLX 'retry_dlx' creado.")

    # DLQ final: mensajes que agotaron todos los reintentos
    channel.queue_declare(queue='cola_muertos_retry', durable=True)
    channel.queue_bind(
        queue='cola_muertos_retry',
        exchange='retry_dlx',
        routing_key='muerto'
    )
    print("[Setup] DLQ 'cola_muertos_retry' creada.")

    # Cola principal de trabajo
    channel.queue_declare(queue='cola_trabajo', durable=True)
    channel.queue_bind(
        queue='cola_trabajo',
        exchange='retry_exchange',
        routing_key='trabajo'
    )
    print("[Setup] Cola principal 'cola_trabajo' creada.")

    # Colas de espera para cada delay
    for delay_ms in DELAYS_MS:
        delay_s = delay_ms // 1000
        nombre_cola = f'cola_espera_{delay_s}s'

        # La cola de espera tiene TTL fijo y cuando expira,
        # el mensaje va al exchange retry_exchange con routing_key 'trabajo'
        # → vuelve automáticamente a cola_trabajo
        channel.queue_declare(
            queue=nombre_cola,
            durable=True,
            arguments={
                'x-message-ttl': delay_ms,                  # TTL = delay deseado
                'x-dead-letter-exchange': 'retry_exchange',  # al expirar, va aquí
                'x-dead-letter-routing-key': 'trabajo',      # y con esta routing key
            }
        )
        print(f"[Setup] Cola de espera '{nombre_cola}' creada (TTL={delay_ms}ms).")

    connection.close()
    print("\n[Setup] Infraestructura completa. Ejecute productor.py y consumidor.py")

if __name__ == '__main__':
    setup()
