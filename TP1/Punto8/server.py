import grpc
from concurrent import futures
import mensaje_pb2
import mensaje_pb2_grpc
import os
from datetime import datetime

# 📌 logs en memoria
logs = []

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{timestamp}] {mensaje}"

    os.makedirs("log", exist_ok=True)
    ruta = os.path.join("log", "grpc_server.log")

    logs.append(log)

    with open(ruta, "a") as f:
        f.write(log + "\n")

    print(log)


class NodoService(mensaje_pb2_grpc.NodoServiceServicer):

    def Saludo(self, request, context):
        log_evento(f"Mensaje recibido: {request.tipo} - {request.mensaje}")

        respuesta = mensaje_pb2.MensajeResponse(
            tipo="respuesta",
            mensaje="Hola A (cliente), soy B (servidor)"
        )

        log_evento(f"Respuesta enviada: {respuesta.tipo} - {respuesta.mensaje}")

        return respuesta


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    mensaje_pb2_grpc.add_NodoServiceServicer_to_server(
        NodoService(),
        server
    )

    server.add_insecure_port('[::]:50051')

    server.start()

    log_evento("Servidor gRPC escuchando en puerto 50051")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()