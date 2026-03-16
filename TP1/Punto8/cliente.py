import grpc
import mensaje_pb2
import mensaje_pb2_grpc

def run():

    channel = grpc.insecure_channel('localhost:50051')
    stub = mensaje_pb2_grpc.NodoServiceStub(channel)

    request = mensaje_pb2.MensajeRequest(
        tipo="saludo",
        mensaje="hola!!!"
    )

    response = stub.Saludo(request)

    print("Mensaje recibido del servidor:", response.tipo, response.mensaje)

run()