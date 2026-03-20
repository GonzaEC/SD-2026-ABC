import grpc
import mensaje_pb2
import mensaje_pb2_grpc
import os
from datetime import datetime

logs = []

def log_evento(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"[{timestamp}] {mensaje}"

    os.makedirs("log", exist_ok=True)
    ruta = os.path.join("log", "grpc_client.log")

    logs.append(log)

    with open(ruta, "a") as f:
        f.write(log + "\n")

    print(log)


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = mensaje_pb2_grpc.NodoServiceStub(channel)

    request = mensaje_pb2.MensajeRequest(
        tipo="saludo",
        mensaje="hola!!!"
    )

    log_evento("Enviando mensaje al servidor")

    response = stub.Saludo(request)

    log_evento(f"Respuesta recibida: {response.tipo} - {response.mensaje}")

    return response  


if __name__ == "__main__":
    run()