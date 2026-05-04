from pathlib import Path
import subprocess
import time

BASE_DIR = Path(__file__).resolve().parent.parent
ETAPA3_DIR = BASE_DIR / "etapa3"
inputPath = BASE_DIR / "FondoCristiano.jpg"
outputPath = BASE_DIR / "output_test.jpg"
procesoPath = ETAPA3_DIR / "ProcesoPrincipalM.py"

#antes de empezar el test procurar que no esten los workers o rabbit ya iniciado
def test_completo():
    rabbit = subprocess.run(["docker", "build", "-t", "grupoABC/sobel-worker:latest", str(BASE_DIR)])
    # esperamos a que se arme la imagen
    time.sleep(10)
    
    subprocess.run(["kubectl", "apply", "-f", str(BASE_DIR / "rabbitmq.yaml"), "-f", str(BASE_DIR /"workers.yaml") ])
    #esperamos a que inicien los workers y rabbitMQ
    time.sleep(10)
    #exponemos puerto
    subprocess.Popen(["kubectl", "port-forward", "svc/rabbitmq", "5672:5672" ])
    
    
    proceso = subprocess.Popen(["python", str(procesoPath), str(inputPath), str(outputPath) ])
    
    #eliminamos un worker para simular reenvio de datos
    subprocess.run(["kubectl", "delete", "pod", "-l", "app=sobel-worker"])
    
    # tiempo de espera de procesamiento final
    time.sleep(20)
    
    result = subprocess.run(
    ["kubectl", "logs", "deployment/sobel-worker"],
    capture_output=True,
    text=True
    )
    #verificamos que los logs contengan el mensaje reenviando
    logs = result.stdout
    assert "Reenviando" in logs
    #verificamos que se haya devuelto la imagen correctamente
    assert Path(outputPath).exists()
    
    