from pathlib import Path
import subprocess
import time
import os
import logging

BASE_DIR = Path(__file__).resolve().parent.parent
ETAPA3_DIR = BASE_DIR / "etapa3"
#LOG_DIR = ETAPA3_DIR / "logs"

inputPath = BASE_DIR / "FondoCristiano.jpg"
outputPath = BASE_DIR / "output_test.jpg"
procesoPath = ETAPA3_DIR / "ProcesoPrincipalM.py"

#antes de empezar el test procurar que esten los workers y rabbit ya iniciado. Ademas procurar tener en otra terminal el port forward activo.
def test_completo():
    
    proceso = subprocess.Popen(
    ["python", str(procesoPath), str(inputPath), str(outputPath)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
    time.sleep(10)
    #eliminamos un worker para simular reenvio de datos
    pod_name = subprocess.run(
        [
            "kubectl", "get", "pod",
            "-l", "app=sobel-worker",
            "-o", "jsonpath={.items[0].metadata.name}"
        ],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()

    subprocess.run([
    "kubectl", "delete", "pod", pod_name,
    "--grace-period=0",
    "--force"
    ], check=True)
    
    # tiempo de espera de procesamiento final
    
    time.sleep(40)
    output = ""
    while True:
        line = proceso.stdout.readline()
        if not line:
            break
        output += line
        if "Reenviando" in output:
            break
    assert "Reenviando" in output
    
    #verificamos que se haya devuelto la imagen correctamente
    assert Path(outputPath).exists()
    
    