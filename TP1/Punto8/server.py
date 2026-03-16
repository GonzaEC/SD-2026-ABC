import grpc
from concurrent import futures
import mensaje_pb2
import mensaje_pb2_grpc


class NodoService(mensaje_pb2_grpc.NodoServiceServicer):

    def Saludo(self, request, context):

        print("Mensaje recibido:", request.tipo, request.mensaje)

        return mensaje_pb2.MensajeResponse(
            tipo="respuesta",
            mensaje="Hola A (cliente), soy B (servidor)"
        )


def serve():

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    mensaje_pb2_grpc.add_NodoServiceServicer_to_server(
        NodoService(),
        server
    )

    server.add_insecure_port('[::]:50051')

    server.start()

    print("Servidor gRPC escuchando en puerto 50051")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()