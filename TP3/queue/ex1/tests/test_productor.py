import pika
from unittest.mock import MagicMock
 
 
def publicar_tareas(channel):
    channel.queue_declare(queue='tareas', durable=True)
    for i in range(1, 11):
        mensaje = f"Tarea #{i}: procesar item {i}"
        channel.basic_publish(
            exchange='',
            routing_key='tareas',
            body=mensaje,
            properties=pika.BasicProperties(delivery_mode=2)
        )
 
 
def test_publica_10_mensajes():
    channel = MagicMock()
    publicar_tareas(channel)
    assert channel.basic_publish.call_count == 10
 
 
def test_declara_cola_durable():
    channel = MagicMock()
    publicar_tareas(channel)
    channel.queue_declare.assert_called_once_with(queue='tareas', durable=True)