import requests
import subprocess
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = BASE_DIR / "terraform"

def test_workers_health():

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

        ips = data["worker_ips"]["value"]

        time.sleep(100)

        for ip in ips:

            r = requests.get(f"http://{ip}:8000/health")

            assert r.status_code == 200

    finally:

        subprocess.run(
            ["terraform", "destroy", "-auto-approve"],
            cwd=TERRAFORM_DIR,
            check=True
        )
    