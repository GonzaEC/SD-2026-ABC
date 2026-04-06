from fastapi import FastAPI, Request
import logging
import os

#Es lo que corre dentro de cada contenedor Docker

# Creo la carpeta de logs y defino como se van a guardar
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "docker.log"), mode="w"),
        logging.StreamHandler()
    ]
)

# Crear servidor HTTP
app = FastAPI()

# Metodos disponibles
metodos = ["suma", "resta", "multiplicacion", "division"]

# Endpoint principal, cuando alguien manda un post a ejecutar tarea, se ejecuta esta funcion
@app.post("/ejecutarTarea")
async def ejecutarTarea(peticion: Request):
    """
    Ejecuta la tarea recibida desde el servidor.
    Espera JSON con:
    {
        "calculo": "...",
        "parametros": [1,2,3],
        ...
    }
    """

    try:
        payload = await peticion.json() #obtiene el json que mando el servidor

        calculo = payload.get("calculo") #obtiene la operacion
        lista = payload.get("parametros", []) #obtiene los numeros

        # Verifica que los numeros sean una lista y no este vacia
        if not isinstance(lista, list) or len(lista) == 0:
            return {"error": "Parametros inválidos"}

        # Resuelve la operacion segun sea el caso
        if calculo == "suma":
            resultado = sum(lista)
            return {"resultado": resultado}

        if calculo == "resta":
            resultado = lista[0]
            for v in lista[1:]:
                resultado -= v
            return {"resultado": resultado}

        if calculo == "multiplicacion":
            resultado = 1
            for v in lista:
                resultado *= v
            return {"resultado": resultado}

        if calculo == "division":
            resultado = lista[0]
            for v in lista[1:]:
                if v == 0:
                    return {"error": "División por cero"}
                resultado /= v
            return {"resultado": resultado}

        return {"error": "Tarea no soportada"}

    except Exception as e:
        return {"error": str(e)}

# Endpoint que devuelve los metodos que soporta
@app.get("/getMetodos")
def mostrarMetodos():
    """
    Devuelve los métodos disponibles.
    """
    return {"metodos": metodos}