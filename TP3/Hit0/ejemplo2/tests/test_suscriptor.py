import json
from suscriptor import procesar_mensaje

def test_suscriptor_procesa_mensaje():
    mensaje = {
        "evento": "nuevo_bloque",
        "numero": 1
    }

    body = json.dumps(mensaje).encode()

    resultado = procesar_mensaje(body, "nodo1")

    assert "nodo1" in resultado
    assert "nuevo_bloque" in resultado