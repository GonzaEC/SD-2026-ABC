import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = BASE_DIR / "terraform"

#comprueba que funciona la creacion de workers mediante terraform
def test_terraform_outputs():
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

        assert "worker_ips" in data
        assert len(data["worker_ips"]["value"]) > 0
        assert "rabbitmq_ip" in data
    finally:

        subprocess.run(
            ["terraform", "destroy", "-auto-approve"],
            cwd=TERRAFORM_DIR,
            check=True
        )
