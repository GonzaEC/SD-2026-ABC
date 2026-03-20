import threading
import time
import json
import os
import pytest
from nodo import cliente, servidor, log_evento, logs

# --- FIXTURES ---

@pytest.fixture(scope="module")
def server_setup():
    """Levanta el servidor una sola vez para los tests de integración"""
    ip = "127.0.0.1"
    puerto = 7000
    hilo_server = threading.Thread(
        target=servidor,
        args=(ip, puerto),
        daemon=True
    )
    hilo_server.start()
    time.sleep(1) 
    return ip, puerto

@pytest.fixture
def limpiar_logs():
    """Fixture opcional para limpiar la lista de logs antes de cada test"""
    logs.clear()
    yield

# --- TESTS DE LOGS ---

def test_log_memoria(limpiar_logs):
    log_evento("test json")
    assert len(logs) > 0

def test_log_archivo():
    log_evento("test archivo json")
    ruta = os.path.join("log", "nodo_json.log")
    assert os.path.exists(ruta)

# --- TESTS DE JSON ---

def test_json_serializacion():
    msj = {
        "tipo": "saludo",
        "mensaje": "hola"
    }
    serializado = json.dumps(msj)
    deserializado = json.loads(serializado)
    
    assert msj == deserializado

# --- TESTS DE INTEGRACIÓN ---

def test_cliente_servidor_json(server_setup):
    ip, puerto = server_setup
    try:
        cliente(ip, puerto)
    except Exception as e:
        pytest.fail(f"La conexión cliente-servidor falló: {e}")