import socket
import time
import threading 
import sys
import json
import os
from datetime import datetime
from flask import Flask, jsonify

# ---------------- LOGS ----------------

logs = []

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{timestamp}] {mensaje}"

    os.makedirs("log", exist_ok=True)
    ruta = os.path.join("log", "nodo_json.log")

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
            sock_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_cliente.connect((IP, PUERTO))

            estado["cliente"] = "OK"
            log_evento(f"Conectado exitosamente al servidor en {IP}:{PUERTO}")

            msj = {
                "tipo": "saludo",
                "mensaje": "hola!!!"
            }

            msj_str = json.dumps(msj)
            sock_cliente.send(msj_str.encode('utf-8'))
            log_evento(f"Mensaje JSON enviado: {msj}")

            datos = sock_cliente.recv(1024)
            
            if not datos:
                log_evento("Error: El servidor cerró la conexión sin enviar datos.")
                sock_cliente.close()
                time.sleep(3)
                continue
            
            try:
                # Intentar decodificar el JSON
                datos_json = json.loads(datos.decode('utf-8'))
                log_evento(f"Respuesta JSON recibida: {datos_json}")
                
                sock_cliente.close()
                return datos_json # Salida exitosa

            except json.JSONDecodeError:
                log_evento("Error: La respuesta del servidor no es un JSON válido.")
                sock_cliente.close()
                time.sleep(3)
                continue

        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            estado["cliente"] = "REINTENTANDO"
            log_evento(f"No se pudo conectar a {IP}:{PUERTO}. Reintentando en 3 segundos...")
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
        print("python nodo.py IP_escucha PUERTO_escucha IP_remota PUERTO_remoto")
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