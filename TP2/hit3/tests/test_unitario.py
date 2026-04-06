
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import threading
from unittest.mock import patch, MagicMock
from bully import BullyNode

# -------------------
# Configuración común
# -------------------

def crear_nodo(node_id, peers):
    return BullyNode(node_id=node_id, peers=peers, heartbeat_interval=5, timeout=1)

PEERS_NODO1 = [{"id": 2, "url": "http://nodo2:8000"}, {"id": 3, "url": "http://nodo3:8000"}]
PEERS_NODO2 = [{"id": 1, "url": "http://nodo1:8000"}, {"id": 3, "url": "http://nodo3:8000"}]
PEERS_NODO3 = [{"id": 1, "url": "http://nodo1:8000"}, {"id": 2, "url": "http://nodo2:8000"}]

# -------------------
# Tests de inicialización
# -------------------

def test_nodo_arranca_sin_coordinador():
    """Al crear un nodo, no debe haber coordinador asignado todavía."""
    nodo = crear_nodo(1, PEERS_NODO1)
    assert nodo.coordinator_id is None

def test_nodo_arranca_sin_eleccion_en_curso():
    """Al crear un nodo, no debe haber una elección en curso."""
    nodo = crear_nodo(1, PEERS_NODO1)
    assert nodo.in_election is False

def test_nodo_conoce_sus_peers():
    """El nodo debe tener correctamente cargada la lista de peers."""
    nodo = crear_nodo(1, PEERS_NODO1)
    assert len(nodo.peers) == 2
    assert nodo.peers[0]["id"] == 2
    assert nodo.peers[1]["id"] == 3

# -------------------
# Tests de helpers
# -------------------

def test_peers_con_mayor_id():
    """El nodo 1 debe ver a nodo2 y nodo3 como peers con mayor ID."""
    nodo = crear_nodo(1, PEERS_NODO1)
    mayores = nodo.peers_with_higher_id()
    assert len(mayores) == 2
    assert all(p["id"] > 1 for p in mayores)

def test_peers_con_mayor_id_nodo3():
    """El nodo 3 no debe tener peers con mayor ID — es el de mayor ID."""
    nodo = crear_nodo(3, PEERS_NODO3)
    mayores = nodo.peers_with_higher_id()
    assert len(mayores) == 0

def test_get_peer_url_existente():
    """Debe retornar la URL correcta de un peer conocido."""
    nodo = crear_nodo(1, PEERS_NODO1)
    assert nodo.get_peer_url(2) == "http://nodo2:8000"

def test_get_peer_url_inexistente():
    """Debe retornar None si el peer no existe."""
    nodo = crear_nodo(1, PEERS_NODO1)
    assert nodo.get_peer_url(99) is None

# -------------------
# Tests de receive_coordinator
# -------------------

def test_receive_coordinator_actualiza_lider():
    """Al recibir COORDINATOR, el nodo debe actualizar su coordinador."""
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.receive_coordinator(3)
    assert nodo.coordinator_id == 3

def test_receive_coordinator_reemplaza_lider_anterior():
    """Si ya había un coordinador, debe reemplazarlo."""
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.receive_coordinator(3)
    nodo.receive_coordinator(2)
    assert nodo.coordinator_id == 2

# -------------------
# Tests de elección — mockeando requests
# -------------------

@patch("bully.requests.post")
def test_eleccion_nodo3_se_proclama_coordinador(mock_post):
    """
    Nodo 3 no tiene peers con mayor ID.
    Al iniciar elección debe proclamarse coordinador y avisar a todos.
    """
    mock_post.return_value = MagicMock(status_code=200)
    nodo = crear_nodo(3, PEERS_NODO3)
    nodo.start_election()
    assert nodo.coordinator_id == 3

@patch("bully.requests.post")
def test_eleccion_nodo1_espera_si_hay_respuesta_ok(mock_post):
    """
    Nodo 1 inicia elección. Nodo 2 y 3 responden OK.
    Nodo 1 debe esperar y NO proclamarse coordinador.
    """
    mock_post.return_value = MagicMock(status_code=200)
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.start_election()
    # Nodo 1 no debe ser coordinador porque recibió OK de alguien mayor
    assert nodo.coordinator_id != 1

@patch("bully.requests.post")
def test_eleccion_cuando_todos_los_peers_caidos(mock_post):
    """
    Si todos los peers con mayor ID están caídos (no responden),
    el nodo debe proclamarse coordinador.
    """
    mock_post.side_effect = Exception("Connection refused")
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.start_election()
    assert nodo.coordinator_id == 1

# -------------------
# Tests de heartbeat
# -------------------

@patch("bully.requests.get")
def test_ping_coordinador_vivo(mock_get):
    """Si el coordinador responde 200, ping_coordinator debe retornar True."""
    mock_get.return_value = MagicMock(status_code=200)
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.coordinator_id = 2
    assert nodo.ping_coordinator() is True

@patch("bully.requests.get")
def test_ping_coordinador_caido(mock_get):
    """Si el coordinador no responde, ping_coordinator debe retornar False."""
    mock_get.side_effect = Exception("Connection refused")
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.coordinator_id = 2
    assert nodo.ping_coordinator() is False

def test_ping_sin_coordinador():
    """Si no hay coordinador asignado, ping_coordinator debe retornar False."""
    nodo = crear_nodo(1, PEERS_NODO1)
    nodo.coordinator_id = None
    assert nodo.ping_coordinator() is False

# -------------------
# Tests de concurrencia
# -------------------

def test_no_dos_elecciones_en_paralelo():
    """Si ya hay una elección en curso, no debe iniciarse otra."""
    nodo = crear_nodo(3, PEERS_NODO3)
    nodo.in_election = True  # simular que ya hay una elección
    
    llamadas = []

    original = nodo.become_coordinator
    def mock_become():
        llamadas.append(1)
        original()
    nodo.become_coordinator = mock_become

    nodo.start_election()
    assert len(llamadas) == 0  # no debe haber llamado a become_coordinator