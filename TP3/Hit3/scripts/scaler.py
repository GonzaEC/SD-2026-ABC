"""
Hit3 - Scaler dinámico de workers
Consulta la profundidad de la cola 'tareas' en RabbitMQ y calcula
cuántas VMs worker se necesitan. Imprime DESIRED_WORKERS=N para que
el pipeline de GitHub Actions lo capture con $GITHUB_OUTPUT.

Fórmula de escala:
  workers = ceil(mensajes_pendientes / MESSAGES_PER_WORKER)
  workers = clamp(workers, MIN_WORKERS, MAX_WORKERS)

  Si la cola está vacía → MIN_WORKERS (puede ser 0 para apagar todo).

Uso:
  python scaler.py >> $GITHUB_OUTPUT
"""

import os
import sys
import math
import requests
from requests.auth import HTTPBasicAuth

RABBITMQ_HOST     = os.environ["RABBITMQ_HOST"]
RABBITMQ_USER     = os.environ["RABBITMQ_USER"]
RABBITMQ_PASS     = os.environ["RABBITMQ_PASS"]
QUEUE_NAME        = os.getenv("QUEUE_NAME", "tareas")
MESSAGES_PER_WORKER = int(os.getenv("MESSAGES_PER_WORKER", "5"))
MIN_WORKERS       = int(os.getenv("MIN_WORKERS", "1"))
MAX_WORKERS       = int(os.getenv("MAX_WORKERS", "10"))


def get_queue_depth() -> int:
    url = f"http://{RABBITMQ_HOST}:15672/api/queues/%2F/{QUEUE_NAME}"
    try:
        r = requests.get(
            url,
            auth=HTTPBasicAuth(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        # 'messages' incluye ready + unacked
        return data.get("messages", 0)
    except requests.RequestException as e:
        print(f"[Scaler] Error consultando RabbitMQ: {e}", file=sys.stderr)
        # Si no se puede consultar, mantener mínimo de workers
        return -1


def calculate_workers(queue_depth: int) -> int:
    if queue_depth < 0:
        return MIN_WORKERS
    if queue_depth == 0:
        return MIN_WORKERS
    workers = math.ceil(queue_depth / MESSAGES_PER_WORKER)
    return max(MIN_WORKERS, min(workers, MAX_WORKERS))


def main():
    depth = get_queue_depth()

    if depth >= 0:
        print(f"[Scaler] Cola '{QUEUE_NAME}': {depth} mensajes pendientes.", file=sys.stderr)
    else:
        print(f"[Scaler] No se pudo consultar la cola. Usando mínimo.", file=sys.stderr)

    desired = calculate_workers(depth)
    print(f"[Scaler] Workers deseados: {desired} (min={MIN_WORKERS}, max={MAX_WORKERS})", file=sys.stderr)

    # Salida para $GITHUB_OUTPUT
    print(f"DESIRED_WORKERS={desired}")


if __name__ == "__main__":
    main()
