"""
Load test para el pipeline Sobel distribuido.

Escenarios controlados por variables de entorno:
  IMAGE_SIZE  — nombre del archivo en images/ (ej: "1KB", "100KB", "1MB")
  BACKEND_URL — URL del backend (default: http://35.202.69.72)

Flujo por usuario virtual:
  1. POST /process con la imagen → recibe job_id
  2. Polling GET /result/{job_id} hasta completed o timeout
  3. Reporta latencia end-to-end como métrica custom "pipeline_e2e"

Métricas que Locust reporta automáticamente:
  - p50 / p95 / p99 de latencia
  - throughput (req/s)
  - tasa de errores
"""

import os
import time
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

BACKEND_URL = os.getenv("BACKEND_URL", "http://35.202.69.72")
IMAGE_SIZE  = os.getenv("IMAGE_SIZE", "100KB")
POLL_INTERVAL = 0.5   # segundos entre polls
POLL_TIMEOUT  = 300   # segundos máximo de espera por job

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")


def load_image(size_label: str) -> bytes:
    path = os.path.join(IMAGES_DIR, f"{size_label}.png")
    with open(path, "rb") as f:
        return f.read()


class SobelUser(HttpUser):
    host = BACKEND_URL
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.image_data = load_image(IMAGE_SIZE)
        self.image_size = IMAGE_SIZE

    @task
    def process_image(self):
        t0 = time.time()

        # ── 1. Enviar imagen ────────────────────────────────────────────────
        with self.client.post(
            "/process",
            files={"file": (f"{self.image_size}.png", self.image_data, "image/png")},
            catch_response=True,
            name=f"POST /process [{self.image_size}]",
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"POST /process → {resp.status_code}: {resp.text[:200]}")
                return
            job_id = resp.json().get("job_id")
            if not job_id:
                resp.failure("No job_id en respuesta")
                return

        # ── 2. Polling hasta completed ──────────────────────────────────────
        deadline = time.time() + POLL_TIMEOUT
        status = "pending"
        polls = 0
        while time.time() < deadline:
            time.sleep(POLL_INTERVAL)
            polls += 1
            r = self.client.get(
                f"/result/{job_id}",
                name=f"GET /result [{self.image_size}]",
            )
            if r.status_code == 200:
                status = r.json().get("status", "unknown")
                if status == "completed":
                    break
            else:
                # error de red — seguir intentando
                pass

        elapsed_ms = (time.time() - t0) * 1000

        # ── 3. Reportar métrica end-to-end ─────────────────────────────────
        success = status == "completed"
        events.request.fire(
            request_type="E2E",
            name=f"pipeline [{self.image_size}]",
            response_time=elapsed_ms,
            response_length=0,
            exception=None if success else Exception(f"status={status} after {polls} polls"),
            context={},
        )

        if not success:
            self.environment.runner.stats.log_error(
                "E2E", f"pipeline [{self.image_size}]", f"timeout: status={status}"
            )
