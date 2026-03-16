from fastapi import FastAPI, Request
import time
import threading
import json

app = FastAPI()
#Lista de nodos activos en la ventana actual
nodos_activos = []
#Lista de nodos registrados para la próxima ventana
nodos_siguientes = []
#Archivo donde se guardan los registros
ARCHIVO = "registro_nodos.json"

tiempoInicio = time.time()

#Guardo el estado actual en un archivo JSON
def guardar_archivo():
    datos = {
        "nodos_activos": nodos_activos,
        "nodos_siguientes": nodos_siguientes
    }

    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=4)


# Hilo que controla las ventanas de inscripción
# Cada 60 segundos:
# los nodos_siguientes pasan a ser nodos_activos y se limpia la lista de siguientes
def controlar_ventanas():
    global nodos_activos, nodos_siguientes
    while True:
        time.sleep(60)
        print("Nueva ventana de tiempo iniciada")
        nodos_activos = nodos_siguientes
        nodos_siguientes = []
        guardar_archivo()


#Inicio el hilo que controla las ventanas
threading.Thread(target=controlar_ventanas, daemon=True).start()

@app.post("/REGISTER")
def registrar_nodo(nodo: dict):
    nodos_siguientes.append(nodo)
    print("Nodo registrado para la próxima ventana")
    guardar_archivo()
    return {"mensaje": "Registrado para la próxima ventana"}

@app.get("/nodos")
def obtener_nodos():
    return {"nodos": nodos_activos}

@app.get("/health")
def estado_actual():
    tiempoActual = time.time() - tiempoInicio
    estado = {
        "estado": "OK",
        "nodos_activos": len(nodos_activos),
        "uptime": tiempoActual
    }
    return estado