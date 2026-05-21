# Hit #3 — Sobel contenerizado, asincrónico y escalable (GKE)

Procesamiento distribuido de imágenes con el operador de Sobel sobre un cluster de Kubernetes (GKE) en Google Cloud Platform. Extiende el Hit #2 (VMs + Terraform) con orquestación Kubernetes, dos node pools dedicados y tres patrones avanzados de mensajería: Dead Letter Queue, Retry con Exponential Backoff y Pub/Sub Fanout.

---

## Arquitectura

```
                        Cliente HTTP
                             │
                    ┌────────▼────────┐
                    │    Frontend      │  nginx  (LoadBalancer)
                    │   apps-pool     │
                    └────────┬────────┘
                             │ proxy_pass
                    ┌────────▼────────┐
                    │    Backend      │  FastAPI (LoadBalancer)
                    │   apps-pool     │
                    └──┬──────────┬──┘
                       │          │ Redis GET/SET
              ┌────────▼──┐  ┌────▼────────┐
              │   Split   │  │    Redis    │  infra-pool
              │ apps-pool │  └────▲────────┘
              └─────┬─────┘       │
                    │ tareas_exchange (direct)
                    │
           ┌────────▼─────────────┐
           │  Queue: tareas       │ ← DLX: sobel_dlx → tareas_muertos (DLQ)
           │  (RabbitMQ)          │    Retry: tareas_espera_1s/2s/4s/8s/30s
           │  infra-pool         │
           └──┬────┬────┬─────────┘
              │    │    │   (fair dispatch, prefetch=1)
    ┌─────────▼┐ ┌─▼────▼──┐ ┌──────────────┐
    │  Worker 1│ │ Worker 2 │ │   Worker N   │  Compute Engine VMs
    │  (VM GCE)│ │  (VM GCE)│ │   (VM GCE)   │  fuera del cluster GKE
    └─────┬────┘ └────┬─────┘ └──────┬───────┘
          │           │              │
          └───────────┴──────────────┘
                      │ resultados_exchange (fanout)
              ┌───────┴────────┐
              │                │
     ┌────────▼──┐    ┌────────▼──┐
     │  Joiner   │    │  Monitor  │
     │ apps-pool │    │(resultados│
     └─────┬─────┘    │ _monitor) │
           │          └───────────┘
           │ Redis SET job:{id}:result
           └──────────────────────────▶ Redis
```

### Node Groups (GKE)

| Node Pool | Servicios | Motivo |
|---|---|---|
| `infra-pool` | RabbitMQ, Redis | Servicios con estado, necesitan estabilidad y recursos dedicados |
| `apps-pool` | Frontend, Backend, Split, Joiner | Servicios stateless, escalables |
| (fuera del cluster) | Worker VMs (Compute Engine) | Cómputo intensivo; escalan independientemente con Terraform |

### Patrones de mensajería implementados

| Patrón | Implementación |
|---|---|
| **Dead Letter Queue** | Cola `tareas` con `x-dead-letter-exchange: sobel_dlx`. NACK sin requeue → `tareas_muertos` |
| **Retry exponential backoff** | Conexión: delays `[1, 2, 4, 8, 30]`s. Sin retry infinito sin backoff |
| **Pub/Sub (fanout)** | `resultados_exchange` (fanout) → `resultados_joiner` + `resultados_monitor` |

---

## Estructura de directorios

```
Hit3/
├── terraform/          # Infraestructura como código (GKE + worker VMs)
├── k8s/                # Manifests de Kubernetes
│   ├── namespace.yaml
│   ├── rabbitmq.yaml   # infra-pool
│   ├── redis.yaml      # infra-pool
│   ├── setup-job.yaml  # Inicializa exchanges/queues/DLX
│   ├── backend.yaml    # apps-pool
│   ├── split.yaml      # apps-pool
│   ├── joiner.yaml     # apps-pool
│   └── frontend.yaml   # apps-pool
├── services/
│   ├── setup/          # Inicialización de RabbitMQ
│   ├── worker/         # Sobel worker (se despliega en VMs)
│   ├── split/          # Divide imagen y publica fragmentos
│   ├── joiner/         # Reconstruye imagen desde resultados
│   └── backend/        # API HTTP + orquestación de jobs
├── scripts/
│   └── scaler.py       # Calcula workers según profundidad de cola
└── tests/
    ├── unit/           # Tests de Sobel, scaler, joiner, worker
    └── integration/    # Tests de flujo completo (con mocks)
```

---

## Prerrequisitos

- **gcloud CLI** configurado con proyecto GCP
- **kubectl** instalado
- **Terraform >= 1.5**
- **Docker** (para build local)
- **Python 3.11** (para tests y scaler local)

---

## Despliegue desde la terminal

### 1. Clonar y configurar

```bash
git clone <repo>
cd TP3/Hit3
```

### 2. Infraestructura GKE con Terraform

```bash
cd terraform

# Editar terraform.tfvars con tu project_id, zona y demás variables
# NO commitear terraform.tfvars — está en .gitignore

terraform init
terraform plan
terraform apply
```

Esto crea:
- Cluster GKE `sobel-cluster` con `infra-pool` y `apps-pool`
- Reglas de firewall

### 3. Configurar kubectl

```bash
# El output de terraform muestra el comando exacto
gcloud container clusters get-credentials sobel-cluster \
  --zone us-central1-a \
  --project MI_PROYECTO
```

### 4. Desplegar servicios base (RabbitMQ + Redis + Setup)

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rabbitmq.yaml -n sobel
kubectl apply -f k8s/redis.yaml -n sobel

# Esperar a que RabbitMQ esté listo
kubectl rollout status deployment/rabbitmq -n sobel

# Inicializar exchanges, queues y DLX
kubectl apply -f k8s/setup-job.yaml -n sobel
kubectl wait job/rabbitmq-setup -n sobel --for=condition=complete --timeout=120s
kubectl logs job/rabbitmq-setup -n sobel
```

### 5. Build y push de imágenes

```bash
PROJECT=mi-proyecto
TAG=$(git rev-parse --short HEAD)

for svc in backend split joiner; do
  docker build -t gcr.io/$PROJECT/sobel-$svc:$TAG services/$svc/
  docker push gcr.io/$PROJECT/sobel-$svc:$TAG
done

# Setup image (solo si cambió)
docker build -t gcr.io/$PROJECT/sobel-setup:latest services/setup/
docker push gcr.io/$PROJECT/sobel-setup:latest
```

### 6. Desplegar aplicaciones

```bash
kubectl apply -f k8s/backend.yaml -n sobel
kubectl apply -f k8s/split.yaml -n sobel
kubectl apply -f k8s/joiner.yaml -n sobel
kubectl apply -f k8s/frontend.yaml -n sobel

# Verificar que todos los pods estén Running
kubectl get pods -n sobel -o wide
```

### 7. Desplegar workers (VMs externas)

```bash
cd terraform

# Escalar a 3 workers
terraform apply -var="worker_count=3"

# Ver IPs de workers
terraform output worker_ips
```

### 8. Probar el pipeline

```bash
# Obtener IP del backend
BACKEND_IP=$(kubectl get svc backend -n sobel -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Enviar imagen
JOB=$(curl -s -X POST http://$BACKEND_IP/process \
  -F "file=@foto.jpg" | jq -r '.job_id')

echo "Job ID: $JOB"

# Consultar estado (puede tardar según tamaño de imagen)
curl http://$BACKEND_IP/result/$JOB

# Descargar imagen resultado
curl http://$BACKEND_IP/result/$JOB/image -o resultado_sobel.png
```

---

## Health Checks

Cada servicio expone un endpoint `/health`:

| Servicio | Acceso | Respuesta |
|---|---|---|
| Backend | `http://<BACKEND_IP>/health` | `{"servicio": "backend", "status": "running"}` |
| Split | `kubectl port-forward svc/split 9000:9000 -n sobel` → `/health` | `{"servicio": "split", "status": "running"}` |
| Joiner | `kubectl port-forward svc/joiner 9001:9001 -n sobel` → `/health` | (idem) |
| Worker VM | `http://<WORKER_IP>:8000/health` | `{"servicio": "worker-N", "status": "running"}` |
| RabbitMQ Management | `kubectl port-forward svc/rabbitmq 15672:15672 -n sobel` → `http://localhost:15672` | UI web |

---

## Ejecutar tests

```bash
cd TP3/Hit3

# Instalar dependencias
pip install -r tests/requirements-test.txt

# Tests unitarios
pytest tests/unit/ -v

# Tests de integración (no requieren servicios externos)
pytest tests/integration/ -v

# Todo con cobertura
pytest tests/ --cov=services --cov-report=term-missing
```

---

## Auto-scaling de workers

El scaler consulta la profundidad de la cola `tareas` vía la Management API de RabbitMQ y calcula cuántos workers se necesitan:

```
workers = ceil(mensajes_pendientes / MESSAGES_PER_WORKER)
workers = clamp(workers, MIN_WORKERS, MAX_WORKERS)
```

**Manual:**
```bash
# Ver profundidad actual de la cola y calcular workers
RABBITMQ_HOST=<IP> RABBITMQ_USER=user RABBITMQ_PASS=<pass> \
  python scripts/scaler.py

# Escalar a N workers
cd terraform && terraform apply -var="worker_count=N"
```

**Automático (via GitHub Actions):**  
El pipeline `hit3-2-workers.yml` corre cada 5 minutos y aplica el resultado del scaler.

---

## CI/CD — Pipelines

| Pipeline | Trigger | Qué hace |
|---|---|---|
| `hit3-ci.yml` | Todo push / PR | Gitleaks + tests + terraform validate |
| `hit3-1-infra.yml` | Push a `terraform/**` / manual | Terraform apply del cluster GKE |
| `hit3-1.1-servicios-base.yml` | Push a configs de infra / manual | Deploy RabbitMQ, Redis, setup job |
| `hit3-1.2-backend.yml` | Push a `services/backend/**` | Build, push GCR, deploy K8s |
| `hit3-1.3-split.yml` | Push a `services/split/**` | Build, push GCR, deploy K8s |
| `hit3-1.4-joiner.yml` | Push a `services/joiner/**` | Build, push GCR, deploy K8s |
| `hit3-1.5-frontend.yml` | Push a `k8s/frontend.yaml` | Deploy nginx |
| `hit3-2-workers.yml` | Cron 5min / manual | Auto-scaling de worker VMs |

**Autenticación**: todos los pipelines usan **Workload Identity Federation (OIDC)** — sin static keys ni SA JSON en secrets.

**Gitleaks**: el CI falla si detecta un secret hardcodeado. Si accidentalmente se commitea uno, revocarlo inmediatamente (el historial de Git lo conserva aunque se borre).

---

## Seguridad

- `.env`, `*.tfvars`, claves JSON y `*-secret.yaml` están en `.gitignore`
- Credenciales en GitHub Actions via **GitHub Secrets y Variables** (nunca en código)
- Autenticación GCP via **Workload Identity Federation** (token efímero, sin SA JSON)
- Docker pull en K8s via **Workload Identity** del node pool (sin image pull secrets con contraseña)
- **Gitleaks** en CI bloquea merges si detecta secrets

### Configurar Workload Identity Federation (una sola vez)

```bash
PROJECT=mi-proyecto
POOL=github-pool
PROVIDER=github-provider
SA=deployer@$PROJECT.iam.gserviceaccount.com
REPO=org/repo

# Crear pool
gcloud iam workload-identity-pools create $POOL \
  --location=global --project=$PROJECT

# Crear provider para GitHub Actions
gcloud iam workload-identity-pools providers create-oidc $PROVIDER \
  --workload-identity-pool=$POOL \
  --location=global \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --project=$PROJECT

# Vincular SA al provider
gcloud iam service-accounts add-iam-policy-binding $SA \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT --format='value(projectNumber)')/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO"
```

Luego configurar en GitHub:
- `vars.WIF_PROVIDER` = `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`
- `vars.WIF_SERVICE_ACCOUNT` = `deployer@PROJECT.iam.gserviceaccount.com`

---

## Logging

Todos los servicios escriben logs en **stdout** (capturado por Kubernetes/GKE → Cloud Logging) y en **disco** (`/app/logs/<servicio>.log` dentro del container).

```bash
# Ver logs en tiempo real
kubectl logs -f deployment/backend -n sobel
kubectl logs -f deployment/joiner -n sobel

# Workers (VMs)
ssh -i ~/.ssh/gcp worker@<WORKER_IP> "docker logs -f sobel-worker-0"
```

---

## Decisiones de diseño

| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Workers como VMs externas al cluster | Workers como pods K8s | Las VMs permiten usar tipos de instancia distintos (compute-optimized) y escalar con Terraform independientemente sin cambiar el node pool de GKE |
| Pub/Sub fanout para resultados | Cola directa al joiner | Desacopla el joiner del monitor; ambos reciben la notificación sin coordinación entre sí |
| DLQ con DLX nativo de RabbitMQ | Reintentos en el worker | El DLX es atómico: si el worker crashea antes de hacer NACK, el mensaje vuelve a la cola. El retry en el worker podría perder el mensaje si cae durante el reintento |
| Retry de conexión con backoff en el código | `restartPolicy: Always` en K8s | K8s ya reinicia el pod, pero el backoff evita "tormentas de reconexión" cuando RabbitMQ se reinicia; evita saturar el broker con reconexiones simultáneas |
| Setup como K8s Job | Init container en cada pod | El Job corre una sola vez y falla ruidosamente si algo va mal; los init containers se ejecutan en cada pod y son más difíciles de depurar |
| OIDC / Workload Identity Federation | SA key JSON en secrets | Zero static keys: el token es efímero (10 min), no hay credenciales que rotar ni que filtrar accidentalmente |
