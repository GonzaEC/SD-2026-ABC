from fastapi import FastAPI, Request
import time

registro = []
app = FastAPI()
tiempoInicio = time.time()

@app.get("/REGISTER")
def registrarPrograma(peticion: Request):
    registro_actual = {
        "ip": peticion.client.host,
        "puerto": peticion.client.port
    }
    registro.append(registro_actual)
    print(f"Se registro un nuevo nodo C")
    return {"nodosDisponibles": registro}

@app.get("/health")
def estado_Actual():
    tiempoActual = time.time() - tiempoInicio
    estado = {
        "Cantidad de nodos registrados": len(registro),
        "uptime": tiempoActual,
        "Estado": "OK"
    }
    return estado

