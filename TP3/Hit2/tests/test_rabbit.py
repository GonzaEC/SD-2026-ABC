import socket
import subprocess
import json
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = BASE_DIR / "terraform"

def test_rabbitmq_port():

    try:

        subprocess.run(
            ["terraform", "apply", "-auto-approve"],
            cwd=TERRAFORM_DIR,
            check=True
        )

        resultado = subprocess.check_output(
            ["terraform", "output", "-json"],
            cwd=TERRAFORM_DIR
        )

        data = json.loads(resultado)

        ip = data["rabbitmq_ip"]["value"]

        time.sleep(100)

        s = socket.create_connection((ip, 5672), timeout=10)

        assert s is not None

        s.close()
        
    finally:

        subprocess.run(
            ["terraform", "destroy", "-auto-approve"],
            cwd=TERRAFORM_DIR,
            check=True
        )
            
