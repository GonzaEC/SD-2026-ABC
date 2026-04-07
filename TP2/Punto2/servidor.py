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

MIN_WORKERS = 1          # Siempre hay al menos 1 worker activo esperando tareas
MAX_WORKERS = 4          # No puede haber más de 4 workers al mismo tiempo
MAX_STACK = 10           # La cola no puede tener más de 10 tareas esperando (programación defensiva)

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

# Cors para aceptar requests desde el navegador, sin esto, el navegador bloquearía los requests por seguridad
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cola_tareas = PriorityQueue()   # Cola de tareas ordenada por timestamp (menor = mas prioritario)
lock_cola = threading.Lock()    # Candado: solo 1 thread a la vez puede tocar la cola

workers = []                    # Lista con todos los workers activos
lock_workers = threading.Lock() # Candado para la lista de workers

carga_actual = 0                # Cuantas tareas hay en total (en cola + ejecutándose)

lamport_clock = 0               # Reloj de Lamport: contador logico para ordenar eventos
lock_clock = threading.Lock()   # Candado para el reloj

# Metricas
lock_metricas = threading.Lock()    # Candado para el contador de tareas
tareas_completadas = 0              # Contador de tareas que ya terminaron (para métricas)
inicio = time.time()                # Momento en que arrancó el servidor

def esperar_servicio(puerto, retries=10):
    # Intenta conectarse al contenedor hasta 10 veces
    for _ in range(retries):
        try:
            requests.get(f"http://host.docker.internal:{puerto}/docs", timeout=1)
            return True # Si responde, el servicio está listo
        except:
            time.sleep(0.5) # Si no responde, espera 0.5 seg y reintenta
    return False

# Funcion para ejecutar el contenedor
def ejecutar_contenedor(tarea):
    imagen = tarea["imagen"] # Nombre de la imagen Docker
    container_name = f"servicio-{int(time.time() * 1000)}" # Nombre único usando timestamp en milisegundos
    puerto = random.randint(8000, 9000) # Puerto aleatorio para no chocar entre contenedores

    # Lee la variable de entorno DOCKER_HOST
    # Si no está definida, usa "host.docker.internal" (forma de acceder al host desde dentro de Docker)
    host = os.environ.get("DOCKER_HOST", "host.docker.internal")

    try:
        # logging.info(f"[DEBUG] Levantando contenedor {container_name} en puerto {puerto}")

        subprocess.run([
            "docker", "run", "-d", # Corre el contenedor en segundo plano
            "--name", container_name,
            "--rm",
            "-p", f"{puerto}:8132", # Mapea puerto aleatorio del host al puerto 8132
            imagen
        ], capture_output=True, text=True)

        # Esperar a que el contenedor este listo
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

        # EJECUTAR TAREA
        #logging.info(f"[DEBUG] Ejecutando request al contenedor {container_name}")
        try:
            response = requests.post(
                f"http://{host}:{puerto}/ejecutarTarea", # Llama al endpoint del contenedor
                json=tarea, # Le manda la tarea completa (calculo, parametros, etc.)
                timeout=5
            )
            return response.json()   # Retorna el resultado del cálculo

        except Exception as e:
            logging.error(f"[ERROR] Fallo en request: {e}")
            return {"error": "fallo request"}

    except Exception as e:
        logging.error(f"[ERROR] Fallo general: {e}")
        return {"error": str(e)}

    finally:
        # Limpieza
        subprocess.run(
            ["docker", "stop", container_name], # Detiene el contenedor
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
        # Toma la próxima tarea de la cola (el _ descarta la prioridad, solo nos importa la tarea)
        # Si la cola está vacía, el worker se BLOQUEA aquí hasta que llegue una tarea
        _, tarea = cola_tareas.get() 

        # Actualiza el reloj de Lamport al RECIBIR una tarea
        with lock_clock:
            lamport_clock = max(lamport_clock, tarea["timestamp"]) + 1 # Regla de Lamport: tomar el máximo entre el reloj local y el timestamp recibido, y sumar 1
            lamport_actual = lamport_clock

        logging.info(
            f"[RECIBIDO] Worker {worker_id} | TS recibido={tarea['timestamp']} | Lamport={lamport_actual}"
        )

        logging.info(f"[Worker {worker_id}] Ejecutando tarea {tarea}")

        resultado = ejecutar_contenedor(tarea) # Ejecuta la tarea en un contenedor Docker

        logging.info(f"[Worker {worker_id}] Resultado: {resultado}")

        # Actualiza el reloj de Lamport al TERMINAR 
        with lock_clock:
            lamport_clock += 1  # Cualquier evento interno incrementa el reloj en 1
            lamport_fin = lamport_clock

        logging.info(
            f"[FIN] Worker {worker_id} | Tarea completada | Lamport={lamport_fin}"
        )

        # métricas
        with lock_metricas:
            tareas_completadas += 1 # Suma 1 al contador de tareas completadas

        # disminuir carga
        with lock_workers:
            carga_actual -= 1  # La tarea ya no está en ejecución, baja la carga

        cola_tareas.task_done() # Marca la tarea como terminada

# Inicalizar Pool
def inicializar_workers():
    """
    Crea el pool mínimo de workers al iniciar el servidor.
    """
    for i in range(MIN_WORKERS):
        t = threading.Thread(target=worker_loop, args=(i,), daemon=True) # daemon=True = si el servidor se cierra, los workers mueren solos 
        t.start()   # Arranca el thread
        workers.append(t)   # Lo agrega a la lista

# Funcion para decidir si crear mas workers o no 
def ajustar_workers():
    """
    Ajusta cantidad de workers según carga.
    """
    global workers

    with lock_workers:
        # Si hay más tareas que workers disponibles Y no se llegó al máximo = crear uno nuevo
        if carga_actual > len(workers) and len(workers) < MAX_WORKERS:
            worker_id = len(workers)
            t = threading.Thread(target=worker_loop, args=(worker_id,), daemon=True)
            t.start()
            workers.append(t)

            logging.info(f"Nuevo worker creado: {worker_id}")

# ENDPOINT PRINCIPAL
@app.post("/getRemoteTask")  # Responde a requests POST en esta ruta
async def ejecutarTareaRemota(peticion: Request):
    global carga_actual, lamport_clock

    tarea = await peticion.json()  # Lee el body del request (la tarea que mandó el cliente)

    if cola_tareas.qsize() >= MAX_STACK:
        return {"error": "Cola llena, intente más tarde"}

    # Actualiza el reloj de Lamport al RECIBIR el evento
    with lock_clock:
        lamport_clock += 1
        tarea["timestamp"] = lamport_clock  # Le asigna un timestamp a la tarea
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
        "estado": "encolado",   # Le avisa al cliente que la tarea fue recibida
        "timestamp": tarea["timestamp"],    # Le devuelve el timestamp asignado
        "cola": cola_tareas.qsize()  # Le dice cuántas tareas hay en la cola
    }

# Metricas
@app.get("/metrics")
def metrics():
    tiempo = time.time() - inicio # Cuántos segundos lleva corriendo el servidor
    throughput = (tareas_completadas / tiempo) * 60 if tiempo > 0 else 0

    return {
        "tareas_completadas": tareas_completadas,
        "tiempo_segundos": tiempo,
        "throughput_tareas_min": throughput, # Cuántas tareas por minuto procesa
        "workers_activos": len(workers),
        "cola": cola_tareas.qsize(),
        "carga_actual": carga_actual
    }

@app.get("/health")
def health():
    # Verifica si Docker está funcionando
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
    uvicorn.run(app, host="0.0.0.0", port=7685)