
from unittest.mock import MagicMock 
 
def procesar_mensaje(ch, method, properties, body):
    mensaje = body.decode()
    ch.basic_ack(delivery_tag=method.delivery_tag)
    return mensaje
 
 
def test_procesar_mensaje_envia_ack():
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
 
    procesar_mensaje(ch, method, None, b"Tarea #1: procesar item 1")
 
    ch.basic_ack.assert_called_once_with(delivery_tag=1)
 
 
def test_procesar_mensaje_decodifica_body():
    ch = MagicMock()
    method = MagicMock()
 
    resultado = procesar_mensaje(ch, method, None, b"Tarea #1: procesar item 1")
 
    assert resultado == "Tarea #1: procesar item 1"