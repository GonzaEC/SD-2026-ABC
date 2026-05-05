import json
from unittest.mock import MagicMock, patch
 
DELAYS = [1, 2, 4, 8]
MAX_INTENTOS = 4
 
def enviar_retry(channel, msg, intento):
    delay = DELAYS[intento - 1]
    msg["intentos"] = intento
    channel.basic_publish(exchange='', routing_key=f"cola_espera_{delay}s", body=json.dumps(msg))
 
def enviar_dlq(channel, msg):
    channel.basic_publish(exchange='retry_dlx', routing_key='muerto', body=json.dumps(msg))
 
def callback(ch, method, properties, body, procesar_ok_fn):
    msg = json.loads(body.decode())
    intento = msg.get("intentos", 0) + 1
    if procesar_ok_fn():
        ch.basic_ack(method.delivery_tag)
    else:
        if intento < MAX_INTENTOS:
            enviar_retry(ch, msg, intento)
        else:
            enviar_dlq(ch, msg)
        ch.basic_ack(method.delivery_tag)
 
def test_mensaje_exitoso_envia_ack():
    ch, method = MagicMock(), MagicMock()
    body = json.dumps({"id": 1, "intentos": 0}).encode()
    callback(ch, method, None, body, procesar_ok_fn=lambda: True)
    ch.basic_ack.assert_called_once()
 
def test_fallo_bajo_max_va_a_retry():
    ch, method = MagicMock(), MagicMock()
    body = json.dumps({"id": 1, "intentos": 0}).encode()
    callback(ch, method, None, body, procesar_ok_fn=lambda: False)
    args = ch.basic_publish.call_args.kwargs
    assert "cola_espera" in args["routing_key"]
 
def test_fallo_en_max_intento_va_a_dlq():
    ch, method = MagicMock(), MagicMock()
    body = json.dumps({"id": 1, "intentos": MAX_INTENTOS - 1}).encode()
    callback(ch, method, None, body, procesar_ok_fn=lambda: False)
    args = ch.basic_publish.call_args.kwargs
    assert args["exchange"] == "retry_dlx"