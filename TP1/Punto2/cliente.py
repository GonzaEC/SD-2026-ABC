import socket
import time

host = '127.0.0.1'
puerto= 333

def iniciar_cliente(): 
    while(True):
        try:
            cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            cliente.connect((host,puerto))
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

app = iniciar_cliente()

