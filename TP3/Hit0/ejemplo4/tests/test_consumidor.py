from unittest.mock import MagicMock
import json
import consumidor


def test_consumidor_procesa_ok(monkeypatch):
    channel = MagicMock()

    # forzar éxito
    monkeypatch.setattr(consumidor, "simular_procesamiento", lambda: True)

    body = json.dumps({
        "id": 1,
        "descripcion": "test",
        "intentos": 0
    }).encode()

    method = MagicMock()
    method.delivery_tag = "tag"

    consumidor.procesar_mensaje(channel, method, None, body)

    # debe hacer ACK
    channel.basic_ack.assert_called_once()


def test_consumidor_hace_retry(monkeypatch):
    channel = MagicMock()

    # forzar fallo
    monkeypatch.setattr(consumidor, "simular_procesamiento", lambda: False)

    body = json.dumps({
        "id": 1,
        "descripcion": "test",
        "intentos": 0
    }).encode()

    method = MagicMock()
    method.delivery_tag = "tag"

    consumidor.procesar_mensaje(channel, method, None, body)

    # debe reencolar + ack
    assert channel.basic_publish.called
    channel.basic_ack.assert_called_once()


def test_consumidor_envia_a_dlq(monkeypatch):
    channel = MagicMock()

    # forzar fallo
    monkeypatch.setattr(consumidor, "simular_procesamiento", lambda: False)

    body = json.dumps({
        "id": 1,
        "descripcion": "test",
        "intentos": 3  # último intento
    }).encode()

    method = MagicMock()
    method.delivery_tag = "tag"

    consumidor.procesar_mensaje(channel, method, None, body)

    # debe mandar a DLQ
    calls = channel.basic_publish.call_args_list

    assert any(call.kwargs.get("exchange") == "retry_dlx" for call in calls)