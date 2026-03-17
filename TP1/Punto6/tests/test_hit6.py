import threading
import time
import  requests
from nodoC import main
from nodoD import iniciar_servidor
from queue import Queue
HOST = "127.0.0.1"
PUERTO = 8000
def test_servidor_responde_cliente():
    """Prueba de integración cliente-servidor TCP"""
    
    # Levanto servidor nodo D en un thread para no bloquear
    server_thread = threading.Thread(target=iniciar_servidor,args=(HOST,PUERTO), daemon=True)
    server_thread.start()
    
    # Pequeña espera para que el servidor del nodo D se inicialice
    time.sleep(1)

    respuesta_cliente1 = Queue()
    respuesta_cliente2 = Queue()
    respuesta_cliente3 = Queue()

    #solicito el estado del nodo D
    peticion = requests.get("http://"  + str(HOST) + ":" + str(PUERTO) +"/health")
    
    #verifico que el nodo D este activo 
    assert "<Response [200]>" in str(peticion)

    #Levanto tres nodo C y obtengo las respuestas de comunicacion de cada uno 
    nodoC1_thread =  threading.Thread(target=main,args=(HOST,PUERTO,respuesta_cliente1), daemon=True)
    nodoC2_thread =  threading.Thread(target=main,args=(HOST,PUERTO,respuesta_cliente2), daemon=True)
    nodoC3_thread =  threading.Thread(target=main,args=(HOST,PUERTO,respuesta_cliente3), daemon=True)
    nodoC1_thread.start()
    nodoC2_thread.start()
    nodoC3_thread.start()

    # Verifico que la respuesta entre nodos sea correcta
    while not respuesta_cliente1.empty:
        assert "Hola A" in respuesta_cliente1.get()
    while not respuesta_cliente2.empty:
        assert "Hola A" in respuesta_cliente1.get()
    while not respuesta_cliente3.empty:
        assert "Hola A" in respuesta_cliente1.get()
    
    