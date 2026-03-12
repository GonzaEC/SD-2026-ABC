import socket
HOST = '127.0.0.1'
PUERTO = 333

SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SocketServer.bind((HOST, PUERTO))
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