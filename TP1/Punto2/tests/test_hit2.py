import threading
import time
from servidor import iniciar_servidor
from cliente import iniciar_cliente
from queue import Queue

def test_reconexion_cliente():
    """Prueba de integración cliente-servidor TCP"""

    respuesta_cliente = Queue()
    intentosReconexion = Queue()
    # Llamo al cliente mediante un thread sin iniciar el servidor y obtengo la respuesta y sus intentos de reconexion
    cliente_thread = threading.Thread(target=iniciar_cliente,args=(respuesta_cliente,intentosReconexion))
    cliente_thread.start()
    #  espera para que el cliente inicialice y trate de reconectarse
    time.sleep(3)

    # Levanto servidor en un thread para no bloquear
    server_thread = threading.Thread(target=iniciar_servidor)
    server_thread.start()
    cliente_thread.join()

    #  espera para que el servidor inicialice y obtener resultados
    time.sleep(1)
    respuesta = respuesta_cliente.get(timeout=10)
    intentos = intentosReconexion.get(timeout=10)
    # Verifico que la respuesta del servidor sea correcta
    assert "Hola A" in respuesta
    # Verifico que el cliente haya intentado reconectarse
    assert intentos > 0
    

