import pika
import json
import time

EXCHANGE = "fanout_test"

def test_fanout_entrega_a_todos():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type='fanout')

    # Crear 3 colas (simulan 3 nodos)
    colas = []
    for _ in range(3):
        result = channel.queue_declare(queue='', exclusive=True)
        cola = result.method.queue
        channel.queue_bind(exchange=EXCHANGE, queue=cola)
        colas.append(cola)

    # Mensaje de prueba
    mensaje = {"evento": "test", "numero": 99}

    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key='',
        body=json.dumps(mensaje)
    )

    time.sleep(0.5)  # darle tiempo a Rabbit

    recibidos = []

    for cola in colas:
        method, _, body = channel.basic_get(queue=cola, auto_ack=True)
        assert body is not None
        recibidos.append(json.loads(body))

    connection.close()

    #TODOS recibieron el mismo mensaje
    assert len(recibidos) == 3
    assert all(m["numero"] == 99 for m in recibidos)