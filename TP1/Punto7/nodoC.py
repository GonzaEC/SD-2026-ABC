import socket
import time
import threading 
import sys
import json
import requests

def cliente(IP, PUERTO): 
    while(True):
        try:
            cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            cliente.connect((IP,PUERTO))
            print(f"Conectado con el servidor")
            msj = {
                "tipo": "saludo",
                "mensaje": "hola!!!"
                }
            msj = json.dumps(msj)
            cliente.send(msj.encode('utf-8'))
            print(f"Mensaje enviado!!!")
            datos = cliente.recv(1024)
            datos = json.loads(datos.decode('utf-8'))
            print(f"Mensaje recibido del servidor: ",datos)
            cliente.close()
            break

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            print("Conexión perdida. Reintentando en 3 segundos...")
            time.sleep(3)

def servidor(IP,PUERTO):
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocketServer.bind((IP, PUERTO))
    SocketServer.listen(1)
    print("Servidor esperando conexiones...")
    while True:
        try:
            conexion, direccion = SocketServer.accept()
            print("Conectado con:", direccion)

            datos = conexion.recv(1024)

            if not datos:
                print("El cliente cerro la conexión")
                conexion.close()
                continue

            mensaje = json.loads(datos.decode("utf-8"))
            print("Mensaje del cliente:", mensaje)

           
            respuesta = {
                "tipo": "respuesta",
                "mensaje": "Hola A (cliente), soy B (servidor)"
                }
            respuesta = json.dumps(respuesta)
            conexion.send(respuesta.encode('utf-8'))

            conexion.close()

        except ConnectionResetError:
            print("El cliente cerro la conexion")

def main():
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
    print("Nodo registrado en D")

    while True:
        #Consulto nodos activos
        respuesta = requests.get(
            "http://" + ip_escuchaD + ":" + str(puerto_escuchaD) + "/nodos"
        )
        nodos = respuesta.json()["nodos"]

        #Me conecto a cada nodo activo
        for nodo in nodos:
            if nodo["puerto"] != Puerto_nodo:
                hilo_cliente = threading.Thread(
                    target=cliente,
                    args=(nodo["ip"], nodo["puerto"])
                )
                hilo_cliente.start()

        #Espero antes de consultar nuevamente
        time.sleep(10)

app = main()