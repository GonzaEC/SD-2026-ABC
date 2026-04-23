import json
from unittest.mock import Mock
from consumidor import procesar
from consumidor_dlq import auditar_fallido


def test_flujo_dlq_completo():
    # Simulamos canal principal
    ch_main = Mock()
    method_main = Mock()
    method_main.delivery_tag = "tag-main"

    # Mensaje con error (debería ir a DLQ)
    msg_error = {
        "id": 2,
        "contenido": "error",
        "error": True
    }

    body = json.dumps(msg_error).encode()

    # Procesamiento en consumidor principal
    procesar(ch_main, method_main, None, body)

    # Verificamos que se rechazó correctamente
    ch_main.basic_nack.assert_called_once_with(
        delivery_tag="tag-main",
        requeue=False
    )

    # Simulamos que Rabbit lo manda a DLQ
    ch_dlq = Mock()
    method_dlq = Mock()
    method_dlq.delivery_tag = "tag-dlq"

    auditar_fallido(ch_dlq, method_dlq, None, body)

    # Verificamos que DLQ lo procesa
    ch_dlq.basic_ack.assert_called_once_with(
        delivery_tag="tag-dlq"
    )