from pathlib import Path
import subprocess
import time

BASE_DIR = Path(__file__).resolve().parent.parent
inputPath = BASE_DIR / "FondoCristiano.jpg"
outputPath = BASE_DIR / "output_test.jpg"
procesoPath = BASE_DIR / "ProcesoPrincipal.py"

#antes de empezar el test procurar que no esten los workers o rabbit ya iniciado
def test_completo():
    rabbit = subprocess.run(["docker", "run", "-d", "--name", "rabbitmq", "-p", "5672:5672", "-p", "15672:15672", "rabbitmq:3-management"])
    if rabbit.returncode != 0:
        subprocess.run(["docker", "start", "rabbitmq"])
    # esperamos a que inicie rabbit
    time.sleep(10)
    
    subprocess.run(["docker", "compose", "build", "--no-cache" ])
    time.sleep(10)
    
    subprocess.run(["docker", "compose", "up", "-d" ])
    time.sleep(10)
    #esperamos que inicien los workers
    
    proceso = subprocess.Popen(["python", str(procesoPath), str(inputPath), str(outputPath) ])
    print(proceso.stderr)
    print(proceso.stdout)
    # tiempo de espera de procesamiento
    time.sleep(20)
    
    assert Path(outputPath).exists()
    subprocess.run(["docker", "stop", "rabbitmq"])
    subprocess.run(["docker", "compose", "down"])
    