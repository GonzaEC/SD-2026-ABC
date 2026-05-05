import json
import pika
from unittest.mock import MagicMock
 
EXCHANGE = "fanout_test"
 
def publicar_eventos(channel):
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
    for i in range(1, 6):
        mensaje = {"evento": "nuevo_bloque", "numero": i}
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key="",
            body=json.dumps(mensaje)
        )
 
def test_publica_5_eventos():
    channel = MagicMock()
    publicar_eventos(channel)
    assert channel.basic_publish.call_count == 5
 
def test_declara_exchange_fanout():
    channel = MagicMock()
    publicar_eventos(channel)
    channel.exchange_declare.assert_called_once_with(exchange=EXCHANGE, exchange_type="fanout")