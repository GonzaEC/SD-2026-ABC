import grpc
from concurrent import futures
import mensaje_pb2
import mensaje_pb2_grpc
import os
from datetime import datetime
from flask import Flask, jsonify
import threading

# 📌 logs en memoria
logs = []

# 📌 estado del sistema
estado = {
    "grpc_server": "DOWN",
    "logs": "OK"
}

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{timestamp}] {mensaje}"

    os.makedirs("log", exist_ok=True)
    ruta = os.path.join("log", "grpc_server.log")

    logs.append(log)

    with open(ruta, "a") as f:
        f.write(log + "\n")

    print(log)


# ---------------- gRPC ----------------

class NodoService(mensaje_pb2_grpc.NodoServiceServicer):

    def Saludo(self, request, context):
        log_evento(f"Mensaje recibido: {request.tipo} - {request.mensaje}")

        estado["grpc_server"] = "OK"

        respuesta = mensaje_pb2.MensajeResponse(
            tipo="respuesta",
            mensaje="Hola A (cliente), soy B (servidor)"
        )

        log_evento(f"Respuesta enviada: {respuesta.tipo} - {respuesta.mensaje}")

        return respuesta


def iniciar_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    mensaje_pb2_grpc.add_NodoServiceServicer_to_server(
        NodoService(),
        server
    )

    server.add_insecure_port('[::]:50051')
    server.start()

    estado["grpc_server"] = "OK"
    log_evento("Servidor gRPC escuchando en puerto 50051")

    server.wait_for_termination()


# ---------------- HTTP HEALTH ----------------

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify(estado)


def iniciar_http():
    app.run(port=8000)


# ---------------- MAIN ----------------

def main():
    hilo_grpc = threading.Thread(target=iniciar_grpc, daemon=True)
    hilo_http = threading.Thread(target=iniciar_http, daemon=True)

    hilo_grpc.start()
    hilo_http.start()

    hilo_grpc.join()
    hilo_http.join()


if __name__ == "__main__":
    main()