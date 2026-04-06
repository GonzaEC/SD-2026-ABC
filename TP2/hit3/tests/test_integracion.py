import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Seteamos variables de entorno ANTES de importar el servidor
os.environ["NODE_ID"] = "1"
os.environ["PEERS"] = "2,http://nodo2:8000;3,http://nodo3:8000"

from servidor import app

client = TestClient(app)

# -------------------
# Tests de /health
# -------------------

def test_health_retorna_200():
    """El endpoint /health debe responder 200."""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_contiene_campos_esperados():
    """El /health debe retornar uptime, Estado, node_id y coordinator_id."""
    response = client.get("/health")
    data = response.json()
    assert "uptime" in data
    assert "Estado" in data
    assert "node_id" in data
    assert "coordinator_id" in data

def test_health_node_id_correcto():
    """El node_id debe coincidir con la variable de entorno seteada."""
    response = client.get("/health")
    assert response.json()["node_id"] == 1

def test_health_estado_ok():
    """El estado del servidor debe ser OK."""
    response = client.get("/health")
    assert response.json()["Estado"] == "OK"

# -------------------
# Tests de /bully/status
# -------------------

def test_bully_status_retorna_200():
    """El endpoint /bully/status debe responder 200."""
    response = client.get("/bully/status")
    assert response.status_code == 200

def test_bully_status_contiene_campos():
    """El /bully/status debe retornar node_id, coordinator_id, in_election y peers."""
    response = client.get("/bully/status")
    data = response.json()
    assert "node_id" in data
    assert "coordinator_id" in data
    assert "in_election" in data
    assert "peers" in data

def test_bully_status_node_id_correcto():
    """El node_id en el status debe ser 1."""
    response = client.get("/bully/status")
    assert response.json()["node_id"] == 1

def test_bully_status_peers_cargados():
    """Los peers deben estar correctamente cargados desde la variable de entorno."""
    response = client.get("/bully/status")
    peers = response.json()["peers"]
    assert len(peers) == 2
    ids = [p["id"] for p in peers]
    assert 2 in ids
    assert 3 in ids

# -------------------
# Tests de /bully/election
# -------------------

def test_election_desde_nodo_menor_retorna_ok():
    """
    Si el sender_id es menor que NODE_ID (1), 
    no debería retornar OK porque nadie tiene ID menor que 1.
    """
    response = client.post("/bully/election", json={"sender_id": 0})
    assert response.status_code == 200
    assert response.json()["status"] == "OK"

def test_election_desde_nodo_mayor_retorna_ignorado():
    """
    Si el sender_id es mayor que NODE_ID,
    este nodo no puede ganar — retorna IGNORADO.
    """
    response = client.post("/bully/election", json={"sender_id": 2})
    assert response.status_code == 200
    assert response.json()["status"] == "IGNORADO"

def test_election_retorna_from_correcto():
    """El campo 'from' debe ser el NODE_ID de este nodo."""
    response = client.post("/bully/election", json={"sender_id": 0})
    assert response.json()["from"] == 1

# -------------------
# Tests de /bully/coordinator
# -------------------

def test_coordinator_actualiza_lider():
    """Al recibir COORDINATOR, el nodo debe actualizar su coordinator_id."""
    response = client.post("/bully/coordinator", json={"coordinator_id": 3})
    assert response.status_code == 200
    assert response.json()["status"] == "ACK"

def test_coordinator_se_refleja_en_status():
    """Después de recibir COORDINATOR, /bully/status debe mostrar el nuevo líder."""
    client.post("/bully/coordinator", json={"coordinator_id": 3})
    response = client.get("/bully/status")
    assert response.json()["coordinator_id"] == 3

def test_coordinator_se_refleja_en_health():
    """Después de recibir COORDINATOR, /health debe mostrar el nuevo líder."""
    client.post("/bully/coordinator", json={"coordinator_id": 3})
    response = client.get("/health")
    assert response.json()["coordinator_id"] == 3