from fastapi import FastAPI, Request
import ast
import logging
import os
import time

# -------------------
# Carpeta de logs relativa al script
# -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# -------------------
# Logging
# -------------------
logging.basicConfig(
    level=logging.INFO,  # Solo INFO y superior
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "hit1.log")),
        logging.StreamHandler()
    ]
)
estado_servicio = {
    "Servidor": "Iniciado",
}
app = FastAPI()
tiempoInicio = time.time()
logging.info(f"Se inicio correctamente docker")
estado_servicio["Servidor"] = "OK"
metodos = ["suma","resta","multiplicacion","division"]
@app.post("/ejecutarTarea")
async def ejecutarTarea(peticion: Request):
    payload = await peticion.json()
    adicional = payload.get("adicional",{})
    redondeo = adicional.get("redondeo",-1)
    absoluto = adicional.get("absoluto",False)
    if payload["calculo"] == metodos[0]:
        p = payload["parametros"]
        lista = ast.literal_eval(p) #convierte el payload tipo string a una lista para obtener los valores ingresados
        resultado = lista[0]
        for valor in lista[1:]:
            resultado += valor
        
        if(redondeo >= 0):
            resultado = round(resultado, redondeo)
        if(absoluto):
            resultado = abs(resultado)
        logging.info({"resultado": resultado})
        return {"resultado": resultado}
    if payload["calculo"] == metodos[1]:
        p = payload["parametros"]
        lista = ast.literal_eval(p) #convierte el payload tipo string a una lista para obtener los valores ingresados
        resultado = lista[0]
        for valor in lista[1:]:
            resultado -= valor
        
        if(redondeo >= 0):
            resultado = round(resultado, redondeo)
        if(absoluto):
            resultado = abs(resultado)
        logging.info({"resultado": resultado})
        return {"resultado": resultado}
    if payload["calculo"] == metodos[2]:
        p = payload["parametros"]
        lista = ast.literal_eval(p) #convierte el payload tipo string a una lista para obtener los valores ingresados
        resultado = lista[0]
        for valor in lista[1:]:
            resultado *= valor
        
        if(redondeo >= 0):
            resultado = round(resultado, redondeo)
        if(absoluto):
            resultado = abs(resultado)
        logging.info({"resultado": resultado})
        return {"resultado": resultado}
    if payload["calculo"] == metodos[3]:
        p = payload["parametros"]
        lista = ast.literal_eval(p) #convierte el payload tipo string a una lista para obtener los valores ingresados
        resultado = lista[0]
        for valor in lista[1:]:
            resultado /= valor
        
        if(redondeo >= 0):
            resultado = round(resultado, redondeo)
        if(absoluto):
            resultado = abs(resultado)
        logging.info({"resultado": resultado})
        return {"resultado": resultado}
    logging.info({"error": "tarea no soportada"})
    return {"error": "tarea no soportada"}

@app.get("/getMetodos")
def mostrarMetodos():
    logging.info({"metodos": metodos})
    return {"metodos": metodos}

@app.get("/health")
def estado_Actual():
    tiempoActual = time.time() - tiempoInicio
    estado = {
        "uptime": tiempoActual,
        "Estado": estado_servicio["Servidor"]
    }
    return estado