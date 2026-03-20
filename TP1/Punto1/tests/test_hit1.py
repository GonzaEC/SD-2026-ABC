import threading
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from servidor import iniciar_servidor
from cliente import iniciar_cliente

def test_servidor_responde_cliente():
    """Prueba de integración cliente-servidor TCP"""
    
    # Levanto servidor en un thread para no bloquear
    server_thread = threading.Thread(target=iniciar_servidor, daemon=True)
    server_thread.start()
    
    # Pequeña espera para que el servidor se inicialice
    time.sleep(1)
    
    # Llamo al cliente y obtengo la respuesta
    respuesta_cliente = iniciar_cliente()
    
    # Verifico que la respuesta del servidor sea correcta
    assert "Hola A" in respuesta_cliente