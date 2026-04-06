import requests
import time

URL = "http://127.0.0.1:7685/getRemoteTask"

def test_ejecucion_completa():
    response = requests.post(URL, json={
        "calculo": "suma",
        "parametros": [2, 3],
        "adicional": [],
        "imagen": "servicio-tarea:1.0"
    })

    assert response.status_code == 200
    data = response.json()

    assert "timestamp" in data
    assert data["estado"] == "encolado"


def test_multiple_tareas():
    for i in range(5):
        response = requests.post(URL, json={
            "calculo": "suma",
            "parametros": [1, 2],
            "adicional": [],
            "imagen": "servicio-tarea:1.0"
        })

        assert response.status_code == 200