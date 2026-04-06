import subprocess
import json
import time


#NOTA: Antes de realizar el test no olvide hacer el login en docker:
# 1. Ingresar con usuario docker solo lectura
#docker login -u ianott
#Luego ingresar el token:
#(solicitar token no pudo ser subido)


def test_servicio_tarea():
    """Prueba de integración docker"""
    #Descargando la imagen de servicio-tarea del repositorio privado
    proceso1 = subprocess.run(
        ["docker", "pull", "ianott/servicio-tarea"],
        capture_output=True,
        text=True
    )
    #Configuramos contenedor docker del servidor
    proceso2 = subprocess.run(
        ["docker", "build", "-t", "servidor:1.0", "-f", "servidor.dockerfile", "."],
        capture_output=True,
        text=True
    )
    #Creamos Red para comunicar contenedores
    proceso3 = subprocess.run(
        ["docker", "network", "create", "red_docker"],
        capture_output=True,
        text=True
    )
    #Ejecutamos el servidor
    proceso4 = subprocess.run(
        ["docker", "run", "--network", "red_docker", "-v", "/var/run/docker.sock:/var/run/docker.sock", "-d", "-i", "--name", "servidor", "-p", "7685:7685", "servidor:1.0"],
        capture_output=True,
        text=True
    )
    if proceso4.returncode != 0:
        #En caso que el contenedor ya este en uso pero en estado exited simplemente lo inicia
        proceso4 = subprocess.run(
        ["docker","start","servidor"],
        capture_output=True,
        text=True
        )
        if proceso4.returncode != 0:
            assert proceso4.returncode == 0, proceso4.stderr
    # Pequeña espera para que el servidor se inicialice
    time.sleep(1)
    #Ejecutamos el metodo suma mediante el cliente con peticion POST
    proceso5 = subprocess.run(
        ["python", "cliente.py", "POST", "suma", "[2,3]", "[]", "ianott/servicio-tarea"],
        capture_output=True,
        text=True
    )
    # Pequeña espera para obtener respuesta
    time.sleep(1)
    #Comprobamos que la salida de la suma sea 5
    assert "{'resultado': 5}" in proceso5.stderr

    #Ejecutamos el metodo resta mediante el cliente con peticion GET
    proceso6 = subprocess.run(
        ["python", "cliente.py", "GET", "resta", "[2,3]", "[]", "ianott/servicio-tarea"],
        capture_output=True,
        text=True
    )
    # Pequeña espera para obtener respuesta
    time.sleep(1)
    #Comprobamos que la salida de la resta sea -1
    assert "{'resultado': -1}" in proceso6.stderr
    
    

    #Ejecutamos el metodo multiplicacion con valor absoluto mediante el cliente con peticion GET
    proceso7 = subprocess.run(
        ["python", "cliente.py", "GET", "multiplicacion", "[-2,3]", "[-1,True]", "ianott/servicio-tarea"],
        capture_output=True,
        text=True
    )
    # Pequeña espera para obtener respuesta
    time.sleep(1)

    #Comprobamos que la salida de la multiplicacion sea 6
    assert "{'resultado': 6}" in proceso7.stderr
    

    
    #Ejecutamos el metodo division con redondeo de 2 mediante el cliente con peticion POST
    proceso8 = subprocess.run(
        ["python", "cliente.py", "POST", "division", "[2,3]","[2,False]", "ianott/servicio-tarea"],
        capture_output=True,
        text=True
    )
    # Pequeña espera para obtener respuesta
    time.sleep(1)
    #Comprobamos que la salida de la division sea 0.67
    assert "{'resultado': 0.67}" in proceso8.stderr
    
    #Ejecutamos el cliente pidiendo todos los metodos
    proceso9 = subprocess.run(
        ["python", "cliente.py", "METODOS", "ianott/servicio-tarea"],
        capture_output=True,
        text=True
    )
    # Pequeña espera para obtener respuesta
    time.sleep(1)
    #Comprobamos que la salida de la suma sea 0.66
    assert "{'metodos': ['suma', 'resta', 'multiplicacion', 'division']}" in proceso9.stderr

    #Detenemos el servidor
    proceso4 = subprocess.run(
        ["docker","stop","servidor"],
        capture_output=True,
        text=True
    )
    


    
    

