import pika
import time

COLA = "tareas_test"

def test_flujo_productor_consumidor():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()

    # Crear cola de test (separada para no mezclar con tu app)
    channel.queue_declare(queue=COLA, durable=False)

    mensaje = "mensaje_integracion"
    recibido = []

    # -------------------------
    # CONSUMIDOR
    # -------------------------
    def callback(ch, method, properties, body):
        recibido.append(body.decode())
        ch.basic_ack(delivery_tag=method.delivery_tag)
        ch.stop_consuming()  # cortar después de 1 mensaje

    channel.basic_consume(
        queue=COLA,
        on_message_callback=callback,
        auto_ack=False
    )

    # -------------------------
    # PRODUCTOR
    # -------------------------
    channel.basic_publish(
        exchange="",
        routing_key=COLA,
        body=mensaje
    )

    # Esperar consumo
    channel.start_consuming()

    connection.close()

    # -------------------------
    # ASSERT
    # -------------------------
    assert len(recibido) == 1
    assert recibido[0] == mensaje