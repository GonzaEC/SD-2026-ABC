import json
from unittest.mock import Mock
from consumidor import procesar


def test_procesa_mensaje_ok():
    ch = Mock()
    method = Mock()
    method.delivery_tag = "tag1"

    body = json.dumps({
        "id": 1,
        "contenido": "ok",
        "error": False
    }).encode()

    procesar(ch, method, None, body)

    ch.basic_ack.assert_called_once_with(delivery_tag="tag1")
    ch.basic_nack.assert_not_called()


def test_procesa_mensaje_error_va_a_dlq():
    ch = Mock()
    method = Mock()
    method.delivery_tag = "tag2"

    body = json.dumps({
        "id": 2,
        "contenido": "error",
        "error": True
    }).encode()

    procesar(ch, method, None, body)

    ch.basic_nack.assert_called_once_with(
        delivery_tag="tag2",
        requeue=False
    )
    ch.basic_ack.assert_not_called()