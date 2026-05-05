import queue
from unittest.mock import MagicMock
 
 
# Cola en memoria que hace de RabbitMQ
_cola = queue.Queue()
 
 
def publicar_tareas(channel):
    for i in range(1, 11):
        channel.basic_publish(body=f"Tarea #{i}: procesar item {i}")
 
 
def procesar_mensaje(ch, method, properties, body):
    body.decode()
    ch.basic_ack(delivery_tag=method.delivery_tag)
 
 
def test_flujo_completo_10_mensajes():
    cola = queue.Queue()
 
    # Productor llena la cola
    channel_mock = MagicMock()
    channel_mock.basic_publish.side_effect = lambda body: cola.put(body.encode())
    publicar_tareas(channel_mock)
 
    assert cola.qsize() == 10
 
    # Consumidor vacía la cola
    ch = MagicMock()
    method = MagicMock()
    procesados = 0
    while not cola.empty():
        body = cola.get()
        procesar_mensaje(ch, method, None, body)
        procesados += 1
 
    assert procesados == 10
    assert cola.empty()
