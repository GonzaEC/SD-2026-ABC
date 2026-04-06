import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from docker import app

client = TestClient(app)

def test_suma():
    response = client.post("/ejecutarTarea", json={
        "calculo": "suma",
        "parametros": [2, 3]
    })
    assert response.status_code == 200
    assert response.json()["resultado"] == 5


def test_resta():
    response = client.post("/ejecutarTarea", json={
        "calculo": "resta",
        "parametros": [5, 2]
    })
    assert response.json()["resultado"] == 3


def test_division_por_cero():
    response = client.post("/ejecutarTarea", json={
        "calculo": "division",
        "parametros": [5, 0]
    })
    assert "error" in response.json()


def test_parametros_invalidos():
    response = client.post("/ejecutarTarea", json={
        "calculo": "suma",
        "parametros": "no es lista"
    })
    assert "error" in response.json()