"""
Lee los summary.csv generados por benchmark.py y genera tabla resumen.
Uso: python3 summarize.py [results_dir]
"""
import os
import sys
import csv
import glob

RESULTS_DIR = sys.argv[1] if len(sys.argv) > 1 else "results"

SIZE_ORDER = {"1KB": 0, "10KB": 1, "100KB": 2, "1MB": 3, "10MB": 4, "100MB": 5}

rows = []
for summary_file in sorted(glob.glob(f"{RESULTS_DIR}/**/summary.csv", recursive=True)):
    with open(summary_file, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

rows.sort(key=lambda r: (
    int(r["workers"]),
    SIZE_ORDER.get(r["size"], 99),
    int(r["concurrency"]),
))

print(f"\n{'Workers':>7} {'Size':>6} {'Conc':>4} | {'p50 (s)':>8} {'p95 (s)':>8} {'p99 (s)':>8} | {'Jobs/s':>7} {'Errors':>7}")
print("─" * 72)

prev_workers = None
for r in rows:
    w = r["workers"]
    if prev_workers and w != prev_workers:
        print()
    prev_workers = w
    print(
        f"{w:>7} {r['size']:>6} {r['concurrency']:>4} | "
        f"{r['p50_s']:>8} {r['p95_s']:>8} {r['p99_s']:>8} | "
        f"{r['throughput_jobs_s']:>7} {int(r['errors']):>6d} err"
    )

print()
