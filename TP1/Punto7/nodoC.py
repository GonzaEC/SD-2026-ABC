import socket
import time
import threading 
import sys
import json
import requests

def cliente(IP, PUERTO): 
    # Loop infinito para reintentar conexiones
    while(True):
        try:
            # Crep el socket y me conecto a otro nodo
            cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            cliente.connect((IP,PUERTO))
            print(f"[NODO C - Cliente] Conectado con el servidor")
            # Envio mensaje al otro nodo (servidor)
            msj = {
                "tipo": "saludo",
                "mensaje": "hola!!!"
                }
            msj = json.dumps(msj)
            cliente.send(msj.encode('utf-8'))
            print(f"[NODO C - Cliente] Mensaje enviado!!!")
            # Recibo mensaje de servidor
            datos = cliente.recv(1024)
            datos = json.loads(datos.decode('utf-8'))
            print(f"[NODO C - Cliente] Mensaje recibido del servidor: ",datos)
            cliente.close()
            break

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            # Reintento si el otro nodo se cayo, no esta activo, etc
            print("Conexión perdida. Reintentando en 3 segundos...")
            time.sleep(3)

def servidor(IP,PUERTO):
    # Creo el socket y espero conexiones
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocketServer.bind((IP, PUERTO))
    SocketServer.listen(1)
    print("[NODO C - Servidor] Servidor esperando conexiones...")

    # Loop para aceptar multiples conexiones
    while True:
        try:
            # Acepto conexion y recibo datos del cliente
            conexion, direccion = SocketServer.accept()
            print("[NODO C - Servidor] Conectado con:", direccion)
            datos = conexion.recv(1024)

            # Manejo la desconexion o cierre del cliente
            if not datos:
                print("[NODO C - Servidor] El cliente cerro la conexión")
                conexion.close()
                continue

            # Obtengo el mensaje del cliente
            mensaje = json.loads(datos.decode("utf-8"))
            print("[NODO C - Servidor] Mensaje del cliente:", mensaje)

           # Envio respuesta al cliente
            respuesta = {
                "tipo": "respuesta",
                "mensaje": "Hola A (cliente), soy B (servidor)"
                }
            respuesta = json.dumps(respuesta)
            conexion.send(respuesta.encode('utf-8'))
            print("[NODO C - Servidor] Mensaje enviado al cliente:", respuesta)

            conexion.close()

        except ConnectionResetError:
            print("El cliente cerro la conexion")

def main():
    # Parametros de D
    ip_escuchaD = sys.argv[1]
    puerto_escuchaD = int(sys.argv[2])

    #Creo socket para escuchar en puerto aleatorio
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind(("0.0.0.0", 0)) 
    Puerto_nodo = servidor_socket.getsockname()[1]
    IP_nodo = "127.0.0.1"
    servidor_socket.close()

    #Inicio servidor TCP del nodo C
    hilo_server = threading.Thread(target=servidor, args=(IP_nodo, Puerto_nodo))
    hilo_server.start()

    #Registro el nodo en D para la próxima ventana
    requests.post(
        "http://" + ip_escuchaD + ":" + str(puerto_escuchaD) + "/REGISTER",
        json={"ip": IP_nodo, "puerto": Puerto_nodo}
    )
    print("[Nodo C] Nodo registrado en D")

    mi_ventana_activa = False  # indica si mi ventana ya empezó

    while True:
        # Consulto nodos activos
        respuesta = requests.get(f"http://{ip_escuchaD}:{puerto_escuchaD}/nodos")
        nodos = respuesta.json()["nodos"]

        # Verifico si yo estoy en los activos
        en_activos = any(nodo["puerto"] == Puerto_nodo for nodo in nodos)

        if en_activos and not mi_ventana_activa:
            print("[Nodo C] Mi ventana comenzó, me conecto a los nodos activos de mi ventana...")
            mi_ventana_activa = True

            for nodo in nodos:
                if nodo["puerto"] != Puerto_nodo:
                    hilo_cliente = threading.Thread(
                    target=cliente,
                    args=(nodo["ip"], nodo["puerto"])
                    )
                    hilo_cliente.start()

        elif en_activos and mi_ventana_activa:
            # Ya estoy activo y ya me conecté, solo espero a que termine la ventana
            pass
        elif not en_activos and mi_ventana_activa:
            # Mi ventana terminó
            print("[Nodo C] Mi ventana terminó, cierro el hilo del nodo.")
            break
        else:
            # Esperando que comience mi ventana
            print("[Nodo C] Esperando turno de ventana...")
        time.sleep(10)

app = main()