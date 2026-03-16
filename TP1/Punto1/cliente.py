import socket
host = '127.0.0.1'
puerto= 333

def iniciar_cliente(): 
    cliente = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    cliente.connect((host,puerto))
    print(f"Conectado con el servidor")
    mensaje = "hola!!!"
    cliente.send(mensaje.encode('utf-8'))
    print(f"Mensaje enviado!!!")
    datos = cliente.recv(1024)
    print(f"Mensaje recibido del servidor: ",datos.decode('utf-8'))
    cliente.close()
    return datos.decode('utf-8') 

if __name__ == "__main__":
    iniciar_cliente()
    

