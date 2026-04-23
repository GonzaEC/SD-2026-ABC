from unittest.mock import MagicMock

import consumidor

def test_procesar_mensaje_ack():
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = 123

    body = b"Tarea de prueba"

    consumidor.procesar_mensaje(ch, method, None, body)

    # Verifica que hace ACK
    ch.basic_ack.assert_called_once_with(delivery_tag=123)