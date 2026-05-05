import json
import pika
from unittest.mock import MagicMock
 
TAREAS = [
    {"id": 1, "descripcion": "Llamada a API externa"},
    {"id": 2, "descripcion": "Escritura en DB"},
    {"id": 3, "descripcion": "Procesamiento imagen"},
    {"id": 4, "descripcion": "Envio email"},
    {"id": 5, "descripcion": "Sync externo"},
]
 
def publicar_tareas(channel):
    for tarea in TAREAS:
        tarea["intentos"] = 0
        tarea["max_intentos"] = 4
        channel.basic_publish(
            exchange='retry_exchange',
            routing_key='trabajo',
            body=json.dumps(tarea),
            properties=pika.BasicProperties(delivery_mode=2)
        )
 
def test_publica_5_tareas():
    channel = MagicMock()
    publicar_tareas(channel)
    assert channel.basic_publish.call_count == 5
 
def test_tareas_con_intentos_en_cero():
    channel = MagicMock()
    publicar_tareas(channel)
    for call in channel.basic_publish.call_args_list:
        body = json.loads(call.kwargs["body"])
        assert body["intentos"] == 0
        assert body["max_intentos"] == 4
 