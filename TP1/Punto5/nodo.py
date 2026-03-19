import socket
import time
import threading 
import sys
import json
import os
from datetime import datetime

# 📌 logs en memoria
logs = []

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{timestamp}] {mensaje}"

    # crear carpeta si no existe
    os.makedirs("log", exist_ok=True)
    ruta = os.path.join("log", "nodo_json.log")

    logs.append(log)

    with open(ruta, "a") as f:
        f.write(log + "\n")

    print(log)


def cliente(IP, PUERTO): 
    while True:
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.connect((IP, PUERTO))

            log_evento("Cliente conectado al servidor")

            msj = {
                "tipo": "saludo",
                "mensaje": "hola!!!"
            }

            msj_str = json.dumps(msj)
            cliente.send(msj_str.encode('utf-8'))
            log_evento(f"Mensaje enviado: {msj}")

            datos = cliente.recv(1024)
            datos_json = json.loads(datos.decode('utf-8'))

            log_evento(f"Mensaje recibido: {datos_json}")

            cliente.close()
            return datos_json  # 👈 útil para tests

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            log_evento("Conexión perdida. Reintentando en 3 segundos...")
            time.sleep(3)


def servidor(IP, PUERTO):
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # reutilizar puerto
    SocketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    SocketServer.bind((IP, PUERTO))
    SocketServer.listen(1)
    SocketServer.settimeout(1)

    log_evento(f"Servidor escuchando en {IP}:{PUERTO}")

    while True:
        try:
            conexion, direccion = SocketServer.accept()
            log_evento(f"Cliente conectado desde {direccion}")

            datos = conexion.recv(1024)

            if not datos:
                log_evento("El cliente cerró la conexión")
                conexion.close()
                continue

            mensaje = json.loads(datos.decode("utf-8"))
            log_evento(f"Mensaje recibido: {mensaje}")

            respuesta = {
                "tipo": "respuesta",
                "mensaje": "Hola A (cliente), soy B (servidor)"
            }

            conexion.send(json.dumps(respuesta).encode('utf-8'))
            log_evento(f"Respuesta enviada: {respuesta}")

            conexion.close()

        except socket.timeout:
            continue
        except ConnectionResetError:
            log_evento("El cliente cerró la conexión")


def main():
    if len(sys.argv) != 5:
        print("Uso:")
        print("python nodo.py IP_escucha PUERTO_escucha IP_remota PUERTO_remoto")
        return

    ip_escucha = sys.argv[1]
    puerto_escucha = int(sys.argv[2])
    ip_remota = sys.argv[3]
    puerto_remoto = int(sys.argv[4])

    hilo_server = threading.Thread(target=servidor, args=(ip_escucha, puerto_escucha))
    hilo_server.daemon = True  # permite cerrar con Ctrl+C

    hilo_cliente = threading.Thread(target=cliente, args=(ip_remota, puerto_remoto))

    hilo_server.start()
    time.sleep(1)
    hilo_cliente.start()

    try:
        hilo_server.join()
        hilo_cliente.join()
    except KeyboardInterrupt:
        log_evento("Programa finalizado manualmente")

    log_evento("Programa terminado")


if __name__ == "__main__":
    main()