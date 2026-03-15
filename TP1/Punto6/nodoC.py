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
    peticion = requests.get("http://" + str(ip_escuchaD) + ":" + str(puerto_escuchaD) + "/REGISTER", stream = True)
    socket = peticion.raw._connection.sock
    IP_nodo, Puerto_nodo = socket.getsockname()
    resultado = peticion.json()
    nodos = resultado["nodosDisponibles"]
    hilo_server = threading.Thread(target=servidor,args=(IP_nodo,Puerto_nodo))
    hilo_server.start()
    time.sleep(1) 
    for nodo in nodos:
        IP_Actual = nodo["ip"]
        Puerto_Actual = nodo["puerto"] 
        if(Puerto_Actual != Puerto_nodo):
            hilo_cliente = threading.Thread(target=cliente,args=(IP_Actual,Puerto_Actual))
            hilo_cliente.start()
            hilo_cliente.join()
    #peticion = requests.get("http://"  + str(ip_escuchaD) + ":" + str(puerto_escuchaD) +"/health")

app = main()