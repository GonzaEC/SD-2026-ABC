import os
from PIL import Image
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = BASE_DIR / "terraform"

def test_integracion():
    input_path = "test_input.jpg"
    output_path = "test_output.jpg"

    # crear imagen de prueba
    img = Image.new("RGB", (100, 100), color="white")
    img.save(input_path)
    try:

        subprocess.run(
            ["terraform", "apply", "-auto-approve"],
            cwd=TERRAFORM_DIR,
            check=True
        )


        subprocess.run(
            ["python", "ProcesoPrincipal.py", input_path, output_path],
            check=True
        )

        assert os.path.exists(output_path)

        
        with Image.open(output_path) as img:
            assert img.width == 100
            assert img.height == 100
        
    finally:

        subprocess.run(
            ["terraform", "destroy", "-auto-approve"],
            cwd=TERRAFORM_DIR,
            check=True
        )
        if os.path.exists(input_path):
            os.remove(input_path)

        if os.path.exists(output_path):
            os.remove(output_path)
    
    