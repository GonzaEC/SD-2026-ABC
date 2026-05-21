#!/bin/bash
# Corre todos los escenarios V1 x V2 y guarda resultados en results/
# Uso: bash run_experiments.sh [workers_count]
#
# V1 — Tamaños de imagen
# V2 — Concurrencia (usuarios virtuales)
# V3 — Cantidad de workers (cambiar manualmente via terraform antes de correr)

set -e

BACKEND_URL="${BACKEND_URL:-http://35.202.69.72}"
WORKERS_LABEL="${1:-1}"          # label para el nombre del resultado (ej: 1, 3)
DURATION="120s"                  # duración por escenario
RESULTS_DIR="results/workers_${WORKERS_LABEL}"

mkdir -p "$RESULTS_DIR"

# V1: tamaños de imagen
IMAGE_SIZES=("1KB" "10KB" "100KB" "1MB" "10MB")

# V2: niveles de concurrencia
CONCURRENCIES=(1 5 10 20)

echo "=== Experimentos Hit#3 — $(date) ==="
echo "Backend: $BACKEND_URL"
echo "Workers: $WORKERS_LABEL"
echo ""

for SIZE in "${IMAGE_SIZES[@]}"; do
  for CONC in "${CONCURRENCIES[@]}"; do
    LABEL="${SIZE}_c${CONC}"
    echo "▶ Escenario: size=$SIZE concurrencia=$CONC"

    IMAGE_SIZE="$SIZE" BACKEND_URL="$BACKEND_URL" \
    locust \
      -f locustfile.py \
      --headless \
      --users "$CONC" \
      --spawn-rate "$CONC" \
      --run-time "$DURATION" \
      --host "$BACKEND_URL" \
      --csv "${RESULTS_DIR}/${LABEL}" \
      --csv-full-history \
      --only-summary \
      2>&1 | tee "${RESULTS_DIR}/${LABEL}.log"

    echo "  ✓ Guardado en ${RESULTS_DIR}/${LABEL}_stats.csv"
    echo ""

    # Pausa entre escenarios para que el pipeline drene
    sleep 10
  done
done

echo "=== Todos los escenarios completados ==="
echo "Resultados en: $RESULTS_DIR"
