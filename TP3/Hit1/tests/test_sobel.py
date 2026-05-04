from pathlib import Path
import subprocess
import time

BASE_DIR = Path(__file__).resolve().parent.parent
ETAPA1_DIR = BASE_DIR / "etapa1"
inputPath = BASE_DIR / "FondoCristiano.jpg"
outputPath = BASE_DIR / "output_test.jpg"
procesoPath = ETAPA1_DIR / "sobel.py"

#antes de empezar el test procurar que no esten los workers o rabbit ya iniciado
def test_completo():
    
    #iniciamos sobel
    proceso = subprocess.Popen(["python", str(procesoPath), str(inputPath), str(outputPath) ])
    
    # tiempo de espera de procesamiento
    time.sleep(20)
    #verificamos que se haya devuelto la imagen correctamente
    assert Path(outputPath).exists()
    