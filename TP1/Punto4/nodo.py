import socket
import time
import threading 
import sys

def cliente(IP, PUERTO): 
    while(True):
        try:
            cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            cliente.connect((IP,PUERTO))
            print(f"Conectado con el servidor")
            mensaje = "hola!!!"
            cliente.send(mensaje.encode('utf-8'))
            print(f"Mensaje enviado!!!")
            datos = cliente.recv(1024)
            print(f"Mensaje recibido del servidor: ",datos.decode('utf-8'))
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

            mensaje = datos.decode("utf-8")
            print("Mensaje del cliente:", mensaje)

            respuesta = "Hola A (cliente), soy B (servidor)"
            conexion.send(respuesta.encode("utf-8"))

            conexion.close()

        except ConnectionResetError:
            print("El cliente cerro la conexion")

def main():
    if len(sys.argv) != 5:
        print("Uso:")
        print("python C.py IP_escucha PUERTO_escucha IP_remota PUERTO_remoto")
        return
    ip_escucha = sys.argv[1]
    puerto_escucha = int(sys.argv[2])
    ip_remota = sys.argv[3]
    puerto_remoto = int(sys.argv[4])

    hilo_server = threading.Thread(target=servidor,args=(ip_escucha,puerto_escucha))
    hilo_cliente = threading.Thread(target=cliente,args=(ip_remota,puerto_remoto))

    hilo_server.start()
    time.sleep(1)  # pequeño delay para asegurar que el servidor arranque
    hilo_cliente.start()

    hilo_server.join()
    hilo_cliente.join()

app = main()

