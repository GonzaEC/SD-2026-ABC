import json
from unittest.mock import Mock
from consumidor_dlq import auditar_fallido


def test_dlq_procesa_mensaje():
    ch = Mock()
    method = Mock()
    method.delivery_tag = "tag-dlq"

    body = json.dumps({
        "id": 99,
        "contenido": "fallido"
    }).encode()

    auditar_fallido(ch, method, None, body)

    ch.basic_ack.assert_called_once_with(delivery_tag="tag-dlq")