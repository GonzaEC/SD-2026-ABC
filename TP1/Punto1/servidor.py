import socket

HOST = '127.0.0.1'
PUERTO = 333

def iniciar_servidor():
    #Creo el socket
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocketServer.bind((HOST, PUERTO))
    SocketServer.listen(1)
    print("Servidor esperando conexión...")
    
    conexion, direccion = SocketServer.accept()
    print(f"Conectado con: {direccion}")
    
    mensaje = conexion.recv(1024).decode("utf-8")
    print(f"Mensaje del cliente: {mensaje}")
    
    respuesta = "Hola A (cliente), soy B (servidor)."
    conexion.send(respuesta.encode())
    print(f"Respuesta enviada: {respuesta}")
    
    conexion.close()
    SocketServer.close()
    
    return mensaje, respuesta

if __name__ == "__main__":
    iniciar_servidor()