import threading
import time
import os
import pytest
from nodo import log_evento, logs, servidor, cliente

# --- FIXTURES ---

@pytest.fixture
def limpiar_memoria_logs():
    """Limpia la lista global de logs antes de cada test"""
    logs.clear()
    yield

@pytest.fixture(scope="module")
def server_thread():
    """Levanta el servidor una vez para todo el módulo"""
    ip = "127.0.0.1"
    puerto = 6001
    hilo = threading.Thread(
        target=servidor,
        args=(ip, puerto),
        daemon=True
    )
    hilo.start()
    time.sleep(1)
    return ip, puerto

# --- TESTS DE LOGS ---

def test_log_en_memoria(limpiar_memoria_logs):
    log_evento("Test memoria")
    assert len(logs) > 0

def test_log_en_archivo():
    log_evento("Test archivo")
    
    ruta = os.path.join("log", "nodo.log")
    assert os.path.exists(ruta)

    with open(ruta, "r") as f:
        contenido = f.read()
    
    assert "Test archivo" in contenido

# --- TESTS DE INTEGRACIÓN ---

def test_cliente_servidor(server_thread):
    ip, puerto = server_thread
    
    try:
        cliente(ip, puerto)
    except Exception as e:
        pytest.fail(f"Error en la comunicación cliente-servidor: {e}")