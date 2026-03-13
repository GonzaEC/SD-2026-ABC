import socket

HOST = '127.0.0.1'
PUERTO = 333

#Creo el socket
SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Asocio al socket la IP y Puerto
SocketServer.bind((HOST, PUERTO))

#Escucho conexiones
SocketServer.listen(1)
print("Servidor esperando conexión...")

#Acepto conexion
conexion, direccion = SocketServer.accept()
print("Conectado con:", direccion)

#Recibo mensaje
mensaje = conexion.recv(1024).decode("UTF-8")
print("Mensaje del cliente:", mensaje)

#Respondo saludo
respuesta = "Hola A (cliente), soy B (servidor)."
conexion.send(respuesta.encode())

#Cierro conexion
conexion.close()
SocketServer.close()