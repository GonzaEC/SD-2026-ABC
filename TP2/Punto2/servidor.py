from fastapi import FastAPI, Request
import uvicorn
import time
import logging
import os
import subprocess
import requests
import threading
import random
from queue import PriorityQueue
from fastapi.middleware.cors import CORSMiddleware

#El servidor recibe los pedidos del cliente y los atiende mediante workers, ejecutando las tareas en distintos
#contenedores Docker.

MIN_WORKERS = 1          # mínimo de workers activos
MAX_WORKERS = 4          # máximo de workers
MAX_STACK = 10           # tamaño máximo de cola (programación defensiva)

# Creo la carpeta de logs y defino como se van a guardar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit2.log")),
        logging.StreamHandler()
    ]
)


# Crear servidor HTTP
app = FastAPI()

# Cors para aceptar requests desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permitir todos (para TP está bien)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cola_tareas = PriorityQueue()           # cola de tareas
lock_cola = threading.Lock()    # exclusión mutua para cola

workers = []                    # pool de workers
lock_workers = threading.Lock() #exclusion mutua para workers

carga_actual = 0                # cantidad de tareas (cola + ejecucion)

# Reloj/contador global
lamport_clock = 0
lock_clock = threading.Lock()

# Metricas
lock_metricas = threading.Lock()
tareas_completadas = 0
inicio = time.time()

def esperar_servicio(puerto, retries=10):
    for _ in range(retries):
        try:
            requests.get(f"http://host.docker.internal:{puerto}/docs", timeout=1)
            return True
        except:
            time.sleep(0.5)
    return False

# Funcion para ejecutar el contenedor
def ejecutar_contenedor(tarea):
    """
    Ejecuta el contenedor Docker y llama al servicio tarea.
    VERSION ROBUSTA (sin cuelgues, con limpieza garantizada)
    """

    imagen = tarea["imagen"]
    container_name = f"servicio-{int(time.time() * 1000)}"
    puerto = random.randint(8000, 9000)

    # Detectar host automáticamente
    host = os.environ.get("DOCKER_HOST", "host.docker.internal")

    try:
        # logging.info(f"[DEBUG] Levantando contenedor {container_name} en puerto {puerto}")

        subprocess.run([
            "docker", "run", "-d",
            "--name", container_name,
            "--rm",
            "-p", f"{puerto}:8132",
            imagen
        ], capture_output=True, text=True)

        # =========================
        # ESPERAR A QUE EL SERVICIO RESPONDA
        # =========================
        listo = False
        for i in range(10):
            try:
                requests.get(f"http://{host}:{puerto}/docs", timeout=1)
                listo = True
                # logging.info(f"[DEBUG] Contenedor listo en intento {i+1}")
                break
            except:
                time.sleep(0.5)

        if not listo:
            logging.error("[ERROR] El contenedor no respondió a tiempo")
            return {"error": "timeout contenedor"}

        # =========================
        # EJECUTAR TAREA
        # =========================
        #logging.info(f"[DEBUG] Ejecutando request al contenedor {container_name}")

        try:
            response = requests.post(
                f"http://{host}:{puerto}/ejecutarTarea",
                json=tarea,
                timeout=5
            )
            return response.json()

        except Exception as e:
            logging.error(f"[ERROR] Fallo en request: {e}")
            return {"error": "fallo request"}

    except Exception as e:
        logging.error(f"[ERROR] Fallo general: {e}")
        return {"error": str(e)}

    finally:
        # =========================
        # LIMPIEZA GARANTIZADA
        # =========================
        #logging.info(f"[DEBUG] Deteniendo contenedor {container_name}")

        subprocess.run(
            ["docker", "stop", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

# Funcion que ejecuta cada worker
def worker_loop(worker_id):
    """
    Cada worker toma tareas de la cola y las ejecuta.
    """
    global carga_actual, tareas_completadas, lamport_clock

    #Loop infinito, el worker siempre esta trabajando
    while True:
        _, tarea = cola_tareas.get()  # toma tarea 

        #Actualización Lamport (Evento recibido)
        with lock_clock:
            lamport_clock = max(lamport_clock, tarea["timestamp"]) + 1
            lamport_actual = lamport_clock

        logging.info(
            f"[RECIBIDO] Worker {worker_id} | TS recibido={tarea['timestamp']} | Lamport={lamport_actual}"
        )

        logging.info(f"[Worker {worker_id}] Ejecutando tarea {tarea}")

        resultado = ejecutar_contenedor(tarea)

        logging.info(f"[Worker {worker_id}] Resultado: {resultado}")

        #Evento interno (fin de ejecución)
        with lock_clock:
            lamport_clock += 1
            lamport_fin = lamport_clock

        logging.info(
            f"[FIN] Worker {worker_id} | Tarea completada | Lamport={lamport_fin}"
        )

        # métricas
        with lock_metricas:
            tareas_completadas += 1

        # disminuir carga
        with lock_workers:
            carga_actual -= 1

        cola_tareas.task_done() #marca la tarea como terminada

# Inicalizar Pool
def inicializar_workers():
    """
    Crea el pool mínimo de workers al iniciar el servidor.
    """
    for i in range(MIN_WORKERS):
        t = threading.Thread(target=worker_loop, args=(i,), daemon=True)
        t.start()
        workers.append(t)

# Funcion para decidir si crear mas workers o no 
def ajustar_workers():
    """
    Ajusta cantidad de workers según carga.
    """
    global workers

    with lock_workers:
        # si hay más carga que workers → crear nuevos
        if carga_actual > len(workers) and len(workers) < MAX_WORKERS:
            worker_id = len(workers)
            t = threading.Thread(target=worker_loop, args=(worker_id,), daemon=True)
            t.start()
            workers.append(t)

            logging.info(f"Nuevo worker creado: {worker_id}")

# ENDPOINT PRINCIPAL
@app.post("/getRemoteTask")
async def ejecutarTareaRemota(peticion: Request):
    global carga_actual, lamport_clock

    tarea = await peticion.json() #recibo json del cliente

    #PROGRAMACIÓN DEFENSIVA
    if cola_tareas.qsize() >= MAX_STACK:
        return {"error": "Cola llena, intente más tarde"}

    #Lamport (Evento enviado)
    with lock_clock:
        lamport_clock += 1
        tarea["timestamp"] = lamport_clock
        lamport_send = lamport_clock

    logging.info(
        f"[ENVIO] Nueva tarea | TS={tarea['timestamp']} | Lamport={lamport_send}"
    )

    #Exclusión mutua para encolar
    with lock_cola:
        cola_tareas.put((tarea["timestamp"], tarea))

    #Aumentar carga
    with lock_workers:
        carga_actual += 1

    # ajustar pool dinámicamente
    ajustar_workers()

    return {
        "estado": "encolado",
        "timestamp": tarea["timestamp"],
        "cola": cola_tareas.qsize()
    }

# =========================
# 📊 MÉTRICAS
# =========================

@app.get("/metrics")
def metrics():
    tiempo = time.time() - inicio
    throughput = (tareas_completadas / tiempo) * 60 if tiempo > 0 else 0

    return {
        "tareas_completadas": tareas_completadas,
        "tiempo_segundos": tiempo,
        "throughput_tareas_min": throughput,
        "workers_activos": len(workers),
        "cola": cola_tareas.qsize(),
        "carga_actual": carga_actual
    }

@app.get("/health")
def health():
    """
    Endpoint público para verificar el estado del sistema.
    """

    # Chequeo de Docker (programación defensiva)
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        docker_status = "OK" if result.returncode == 0 else "ERROR"
    except:
        docker_status = "ERROR"

    return {
        "servidor": "OK",
        "workers_activos": len(workers),
        "cola_tareas": cola_tareas.qsize(),
        "carga_actual": carga_actual,
        "docker": docker_status,
    }

if __name__ == "__main__":
    inicializar_workers()
    uvicorn.run(app, host="127.0.0.1", port=7685)