import json
from unittest.mock import Mock
from consumidor import procesar
from consumidor_dlq import auditar_fallido


def test_flujo_dlq_completo():

    # =========================
    # 1. Consumidor principal
    # =========================
    ch_main = Mock()
    method_main = Mock()
    method_main.delivery_tag = "tag-main"

    msg_error = {
        "id": 2,
        "contenido": "error",
        "error": True
    }

    body = json.dumps(msg_error).encode()

    procesar(ch_main, method_main, None, body)

    ch_main.basic_nack.assert_called_once_with(
        delivery_tag="tag-main",
        requeue=False
    )

    # =========================
    # 2. DLQ consumer
    # =========================
    ch_dlq = Mock()
    method_dlq = Mock()
    method_dlq.delivery_tag = "tag-dlq"

    auditar_fallido(ch_dlq, method_dlq, None, body)

    ch_dlq.basic_ack.assert_called_once_with(
        delivery_tag="tag-dlq"
    )