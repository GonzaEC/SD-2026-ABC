# Load Testing — Hit #3 Sobel Pipeline

Herramientas y scripts para el análisis de desempeño bajo carga del pipeline distribuido de Sobel.

## Estructura

```
load_testing/
├── benchmark.py        # Script principal de benchmark (E2E, multithreaded)
├── generate_images.py  # Genera imágenes PNG de distintos tamaños
├── summarize.py        # Lee resultados y genera tabla resumen
├── locustfile.py       # Escenario Locust (alternativa para load testing HTTP puro)
├── run_experiments.sh  # Script que corre todos los escenarios secuencialmente
├── requirements.txt    # Dependencias (locust)
├── images/             # Imágenes de prueba generadas (no commitear las grandes)
└── results/
    ├── workers_1/      # Resultados con 1 worker
    │   ├── summary.csv
    │   └── <size>_c<conc>.csv
    └── workers_3/      # Resultados con 3 workers
        ├── summary.csv
        └── <size>_c<conc>.csv
```

## Setup

```bash
cd TP3/Hit3/load_testing

# Crear entorno virtual
python3 -m venv venv && source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Generar imágenes de prueba
python3 generate_images.py
```

## Uso del benchmark

`benchmark.py` es el script principal. Envía N jobs concurrentes al backend y espera que todos completen, midiendo la latencia E2E real (desde el POST hasta `status: completed` en Redis).

```bash
# Sintaxis
python3 benchmark.py \
  --size      <1KB|10KB|100KB|1MB|10MB>  \  # tamaño de imagen (V1)
  --concurrency <N>                         \  # requests simultáneos (V2)
  --jobs        <N>                         \  # total de jobs a enviar
  --workers-label <N>                          # label para el CSV (V3)

# Ejemplo: 100KB, 5 concurrentes, 10 jobs, con 3 workers activos
python3 benchmark.py --size 100KB --concurrency 5 --jobs 10 --workers-label 3
```

**Variable de entorno:** `BACKEND_URL` (default: `http://35.202.69.72`)

```bash
BACKEND_URL=http://otra-ip.com python3 benchmark.py --size 1KB --concurrency 1 --jobs 5 --workers-label 1
```

## Correr todos los escenarios

```bash
# Con 1 worker activo (terraform.tfvars: worker_count = 1)
bash run_experiments.sh 1

# Escalar a 3 workers
# (editar terraform.tfvars y aplicar: terraform apply -auto-approve)
bash run_experiments.sh 3
```

El script corre todas las combinaciones de V1 × V2 y guarda resultados en `results/workers_<N>/`.

## Ver resultados

```bash
python3 summarize.py results
```

Salida ejemplo:

```
Workers   Size Conc |  p50 (s)  p95 (s)  p99 (s) |  Jobs/s  Errors
──────────────────────────────────────────────────────────────────────
      1    1KB    1 |     1.74     1.80     1.80 |   0.565      0 err
      1    1KB    5 |     1.79     1.94     1.94 |   2.684      0 err
      1    1KB   10 |     2.05     2.13     2.13 |   4.661      0 err
      1  100KB    1 |     2.79     4.96     4.96 |   0.273      0 err
      1  100KB   10 |     9.22    13.38    13.38 |   0.680      0 err
      1    1MB    1 |   153.37   162.80   162.80 |   0.006      0 err

      3  100KB    1 |     2.78     3.63     3.63 |   0.333      0 err
      3  100KB   10 |     4.51     9.51     9.51 |   1.044      0 err
      3    1MB    1 |     9.49     9.50     9.50 |   0.103      0 err
```

## Métricas

| Métrica | Descripción |
|---------|-------------|
| **p50** | Latencia mediana E2E (50% de los jobs terminan en este tiempo o menos) |
| **p95** | Latencia del percentil 95 — "el peor caso frecuente" |
| **p99** | Latencia del percentil 99 — "el peor caso raro" |
| **Jobs/s** | Throughput: jobs completados por segundo durante todo el experimento |

## Configuración de los tests

| Parámetro | Valor |
|-----------|-------|
| Jobs por escenario | 10 (3 para 1MB) |
| Timeout por job | 600 s |
| Intervalo de polling | 1 s |
| Duración por escenario Locust | 120 s |

## Notas

- Las imágenes se generan con ruido aleatorio puro (sin compresión efectiva) para que el tamaño del archivo sea predecible.
- El pipeline divide cada imagen en **3 fragmentos** (configurado en `split.yaml`: `WORKERS=3`). Con 3 workers activos, los fragmentos se procesan en paralelo, lo que explica el speedup de ~16× para imágenes de 1MB.
- Con `--concurrency > workers × 3`, la cola de RabbitMQ empieza a acumular fragmentos y la latencia p95 diverge del p50.
- Para imágenes de 10MB con 1 worker se esperan tiempos de decenas de minutos; no se incluyó en los experimentos principales.
