import time
import sys
import os 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from nodoD import app, nodos_activos, nodos_siguientes

client = TestClient(app)

def limpiar_estado():
    nodos_activos.clear()
    nodos_siguientes.clear()

def simular_cambio_ventana():
    global nodos_activos, nodos_siguientes
    nodos_activos.clear()
    nodos_activos.extend(nodos_siguientes)
    nodos_siguientes.clear()

def test_sistema_completo():

    # 1. Limpio estado inicial
    limpiar_estado()

    # 2. Registro nodos (simula nodos C registrándose en D)
    client.post("/REGISTER", json={"ip": "127.0.0.1", "puerto": 5001})
    client.post("/REGISTER", json={"ip": "127.0.0.1", "puerto": 5002})
    client.post("/REGISTER", json={"ip": "127.0.0.1", "puerto": 5003})

    # Todavía NO deben estar activos
    response = client.get("/nodos")
    assert response.json()["nodos"] == []

    # 3. Simulo paso de ventana (como si pasaran los 60s)
    simular_cambio_ventana()

    # 4. Ahora SÍ deben estar activos
    response = client.get("/nodos")
    nodos = response.json()["nodos"]

    assert len(nodos) == 3

    puertos = [n["puerto"] for n in nodos]
    assert 5001 in puertos
    assert 5002 in puertos
    assert 5003 in puertos

    # 5. Registro un nodo nuevo (debe ir a la SIGUIENTE ventana)
    client.post("/REGISTER", json={"ip": "127.0.0.1", "puerto": 6000})

    # Sigue sin aparecer en activos
    response = client.get("/nodos")
    nodos = response.json()["nodos"]

    puertos = [n["puerto"] for n in nodos]
    assert 6000 not in puertos

    # 6. Nuevo cambio de ventana
    simular_cambio_ventana()

    # 7. Ahora solo debería estar el nuevo nodo
    response = client.get("/nodos")
    nodos = response.json()["nodos"]

    assert len(nodos) == 1
    assert nodos[0]["puerto"] == 6000