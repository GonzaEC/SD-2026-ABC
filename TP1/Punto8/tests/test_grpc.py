import threading
import time
import pytest
from server import iniciar_grpc
from cliente import run

@pytest.fixture(scope="module")
def grpc_server():
    """Levanta el servidor gRPC automáticamente antes de los tests"""
    hilo_server = threading.Thread(target=iniciar_grpc, daemon=True)
    hilo_server.start()
    
    time.sleep(2) 
    
    yield hilo_server  
    
    print("\nServidor gRPC finalizado (thread daemonizado)")

def test_comunicacion_grpc(grpc_server):
    """Prueba la comunicación entre cliente y servidor"""
    response = run()

    assert response.tipo == "respuesta"
    assert response.mensaje == "Hola A (cliente), soy B (servidor)"