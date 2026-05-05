import json
from unittest.mock import MagicMock
 
def callback(ch, method, properties, body):
    return json.loads(body)
 
def test_callback_parsea_mensaje():
    mensaje = {"evento": "nuevo_bloque", "numero": 3}
    resultado = callback(None, None, None, json.dumps(mensaje).encode())
    assert resultado == mensaje
 
def test_callback_lee_numero_correcto():
    mensaje = {"evento": "nuevo_bloque", "numero": 5}
    resultado = callback(None, None, None, json.dumps(mensaje).encode())
    assert resultado["numero"] == 5
 