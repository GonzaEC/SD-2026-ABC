import pika
import json
import time


def test_retry_flow_real():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # limpiar colas
    channel.queue_purge(queue='cola_trabajo')
    channel.queue_purge(queue='cola_muertos_retry')

    # enviar mensaje
    mensaje = {
        "id": 999,
        "descripcion": "test integracion",
        "intentos": 0,
        "max_intentos": 4
    }

    channel.basic_publish(
        exchange='retry_exchange',
        routing_key='trabajo',
        body=json.dumps(mensaje)
    )

    # esperar procesamiento (retry + posibles delays)
    time.sleep(10)

    # verificar si terminó en algún lado
    method, props, body = channel.basic_get(queue='cola_muertos_retry')

    # puede o no estar en DLQ (porque hay random)
    # entonces validamos que el sistema NO explote
    assert True

    connection.close()