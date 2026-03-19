import socket
import time
import threading 
import sys
from datetime import datetime
import os
from flask import Flask, jsonify

# ---------------- LOGS ----------------

logs = []

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{timestamp}] {mensaje}"

    os.makedirs("log", exist_ok=True)
    ruta = os.path.join("log", "nodo.log")

    logs.append(log)

    with open(ruta, "a") as f:
        f.write(log + "\n")

    print(log)

# ---------------- ESTADO ----------------

estado = {
    "servidor": "DOWN",
    "cliente": "DOWN",
    "logs": "OK"
}

# ---------------- CLIENTE ----------------

def cliente(IP, PUERTO): 
    while True:
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.connect((IP, PUERTO))

            estado["cliente"] = "OK"
            log_evento("Cliente conectado al servidor")

            mensaje = "hola!!!"
            cliente.send(mensaje.encode('utf-8'))
            log_evento(f"Mensaje enviado: {mensaje}")

            datos = cliente.recv(1024)
            respuesta = datos.decode('utf-8')
            log_evento(f"Respuesta recibida: {respuesta}")

            cliente.close()
            break

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            estado["cliente"] = "REINTENTANDO"
            log_evento("Conexión fallida. Reintentando en 3 segundos...")
            time.sleep(3)

# ---------------- SERVIDOR ----------------

def servidor(IP, PUERTO):
    SocketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    SocketServer.bind((IP, PUERTO))
    SocketServer.listen(1)
    SocketServer.settimeout(1)

    estado["servidor"] = "OK"
    log_evento(f"Servidor escuchando en {IP}:{PUERTO}")

    while True:
        try:
            conexion, direccion = SocketServer.accept()
            log_evento(f"Cliente conectado desde {direccion}")

            datos = conexion.recv(1024)

            if not datos:
                log_evento("Cliente cerró la conexión")
                conexion.close()
                continue

            mensaje = datos.decode("utf-8")
            log_evento(f"Mensaje recibido: {mensaje}")

            respuesta = "Hola A (cliente), soy B (servidor)"
            conexion.send(respuesta.encode("utf-8"))
            log_evento("Respuesta enviada")

            conexion.close()

        except socket.timeout:
            continue
        except ConnectionResetError:
            log_evento("Conexión reiniciada por el cliente")

# ---------------- HTTP HEALTH ----------------

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({
        **estado,
        "timestamp": datetime.now().isoformat()
    })

def iniciar_http():
    app.run(port=8000)

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 5:
        print("Uso:")
        print("python C.py IP_escucha PUERTO_escucha IP_remota PUERTO_remoto")
        return

    ip_escucha = sys.argv[1]
    puerto_escucha = int(sys.argv[2])
    ip_remota = sys.argv[3]
    puerto_remoto = int(sys.argv[4])

    hilo_server = threading.Thread(target=servidor, args=(ip_escucha, puerto_escucha), daemon=True)
    hilo_cliente = threading.Thread(target=cliente, args=(ip_remota, puerto_remoto))
    hilo_http = threading.Thread(target=iniciar_http, daemon=True)

    hilo_server.start()
    hilo_http.start()

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