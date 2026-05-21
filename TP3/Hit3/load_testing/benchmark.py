"""
Benchmark end-to-end del pipeline Sobel.

Envía N jobs concurrentes y espera que todos completen, midiendo la
latencia E2E real (submit → result=completed) para cada job.

Uso:
  python3 benchmark.py --size 100KB --concurrency 5 --jobs 10 --workers-label 1

Salida: imprime tabla y guarda CSV en results/workers_<N>/<size>_c<conc>.csv
"""

import os
import sys
import csv
import time
import argparse
import threading
import statistics
import urllib.request
import urllib.parse
import urllib.error
import json

BACKEND_URL = os.getenv("BACKEND_URL", "http://35.202.69.72")
IMAGES_DIR  = os.path.join(os.path.dirname(__file__), "images")
POLL_INTERVAL = 1.0   # segundos entre polls
POLL_TIMEOUT  = 600   # timeout por job


def post_job(image_path: str) -> tuple[str, float]:
    """Envía una imagen al backend. Retorna (job_id, elapsed_ms_post)."""
    with open(image_path, "rb") as f:
        data = f.read()

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    filename  = os.path.basename(image_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BACKEND_URL}/process",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    elapsed = (time.time() - t0) * 1000
    return result["job_id"], elapsed


def poll_until_done(job_id: str) -> tuple[str, int]:
    """Hace polling hasta que el job complete. Retorna (status, polls)."""
    deadline = time.time() + POLL_TIMEOUT
    polls = 0
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        polls += 1
        try:
            url = f"{BACKEND_URL}/result/{job_id}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
                if data.get("status") == "completed":
                    return "completed", polls
        except Exception:
            pass
    return "timeout", polls


def run_job(image_path: str, results: list, lock: threading.Lock):
    """Función ejecutada por cada thread: POST + poll + registra resultado."""
    t_start = time.time()
    try:
        job_id, post_ms = post_job(image_path)
    except Exception as e:
        with lock:
            results.append({"status": "post_error", "e2e_ms": None, "error": str(e)})
        return

    status, polls = poll_until_done(job_id)
    e2e_ms = (time.time() - t_start) * 1000

    with lock:
        results.append({
            "job_id":   job_id,
            "status":   status,
            "post_ms":  round(post_ms, 1),
            "e2e_ms":   round(e2e_ms, 1),
            "polls":    polls,
        })
        done = len(results)
        print(f"  [{done}] job {job_id[:8]}… → {status}  E2E={e2e_ms/1000:.1f}s")


def percentile(data: list[float], p: int) -> float:
    if not data:
        return 0.0
    data_sorted = sorted(data)
    idx = max(0, int(len(data_sorted) * p / 100) - 1)
    return data_sorted[idx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size",          default="100KB")
    parser.add_argument("--concurrency",   type=int, default=5)
    parser.add_argument("--jobs",          type=int, default=10)
    parser.add_argument("--workers-label", default="1")
    args = parser.parse_args()

    image_path = os.path.join(IMAGES_DIR, f"{args.size}.png")
    if not os.path.exists(image_path):
        print(f"ERROR: imagen no encontrada: {image_path}")
        sys.exit(1)

    print(f"\n=== Benchmark: size={args.size}  concurrency={args.concurrency}  jobs={args.jobs}  workers={args.workers_label} ===")
    print(f"Backend: {BACKEND_URL}\n")

    results: list = []
    lock = threading.Lock()
    threads = []

    t_global = time.time()
    sem = threading.Semaphore(args.concurrency)

    def worker_fn():
        sem.acquire()
        try:
            run_job(image_path, results, lock)
        finally:
            sem.release()

    for _ in range(args.jobs):
        t = threading.Thread(target=worker_fn)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    total_time = time.time() - t_global

    # ── Estadísticas ────────────────────────────────────────────────────────
    completed = [r for r in results if r["status"] == "completed"]
    errors    = [r for r in results if r["status"] != "completed"]
    e2e_vals  = [r["e2e_ms"] for r in completed]

    print(f"\n{'─'*55}")
    print(f"Jobs completados: {len(completed)}/{args.jobs}  Errores: {len(errors)}")
    if e2e_vals:
        print(f"E2E latencia (segundos):")
        print(f"  p50  = {percentile(e2e_vals, 50)/1000:.2f}s")
        print(f"  p95  = {percentile(e2e_vals, 95)/1000:.2f}s")
        print(f"  p99  = {percentile(e2e_vals, 99)/1000:.2f}s")
        print(f"  min  = {min(e2e_vals)/1000:.2f}s")
        print(f"  max  = {max(e2e_vals)/1000:.2f}s")
        print(f"  mean = {statistics.mean(e2e_vals)/1000:.2f}s")
    print(f"Throughput total: {len(completed)/total_time:.3f} jobs/s")
    print(f"Tiempo total: {total_time:.1f}s")
    print(f"{'─'*55}")

    # ── Guardar CSV ─────────────────────────────────────────────────────────
    out_dir = os.path.join(
        os.path.dirname(__file__),
        "results",
        f"workers_{args.workers_label}",
    )
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{args.size}_c{args.concurrency}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["job_id", "status", "post_ms", "e2e_ms", "polls"])
        writer.writeheader()
        writer.writerows(results)

    # Guardar resumen
    summary_path = os.path.join(out_dir, "summary.csv")
    write_header = not os.path.exists(summary_path)
    with open(summary_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["size", "concurrency", "workers", "jobs", "completed", "errors",
                             "p50_s", "p95_s", "p99_s", "mean_s", "throughput_jobs_s"])
        writer.writerow([
            args.size, args.concurrency, args.workers_label,
            args.jobs, len(completed), len(errors),
            f"{percentile(e2e_vals, 50)/1000:.2f}" if e2e_vals else "",
            f"{percentile(e2e_vals, 95)/1000:.2f}" if e2e_vals else "",
            f"{percentile(e2e_vals, 99)/1000:.2f}" if e2e_vals else "",
            f"{statistics.mean(e2e_vals)/1000:.2f}" if e2e_vals else "",
            f"{len(completed)/total_time:.3f}",
        ])

    print(f"Resultados guardados en: {csv_path}")


if __name__ == "__main__":
    main()
