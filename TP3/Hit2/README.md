# Hit #2 — Sobel con offloading en la nube (Terraform + GCP)

Extiende el Hit #1 con una arquitectura **híbrida**: RabbitMQ corre en un cluster Kubernetes local (k3d), mientras que los workers de cómputo se provisionan y destruyen bajo demanda en **Google Cloud Platform** mediante Terraform.

---

## Arquitectura

```
  Local (k3d)                          GCP (Compute Engine)
  ─────────────────────────────        ─────────────────────────────────────
                                        terraform apply
  ┌──────────────────────────┐  ──────▶  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │  ProcesoPrincipal.py     │            │  Worker VM 0│  │  Worker VM 1│  │  Worker VM N│
  │  (orquestador)           │            │  (e2-micro) │  │  (e2-micro) │  │  (e2-micro) │
  │  puerto 9013 /health     │            │  Docker     │  │  Docker     │  │  Docker     │
  └──┬───────────────────────┘            │  worker.py  │  │  worker.py  │  │  worker.py  │
     │                                    │  :8000      │  │  :8000      │  │  :8000      │
     │  ┌──────────────┐                  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
     │  │  Splitter    │  tareas queue            │                │                │
     │  │  puerto 9000 │ ──────────────────────── └────────────────┴───────── ──────┘
     │  └──────────────┘         │                         │ (consume, aplica Sobel)
     │                    ┌──────▼──────┐                  │
     │                    │  RabbitMQ   │◀─────────────────┘ resultado queue
     │                    │  (k3d pod)  │
     │                    │  5672/15672 │
     │                    └─────────────┘
     │                           │
     │  ┌──────────────┐         │
     └──│   Joiner     │◀────────┘
        │   puerto 9001│
        └──────────────┘
                │
                ▼
          imagen_sobel.png
```

### Ciclo de vida de un worker

```
Provisioning  →  Bootstrap  →  Deploy  →  Join  →  Teardown
(terraform       (startup.sh:   (docker    (conecta   (terraform
  apply)          apt + docker)   pull)     rabbit)    destroy)
```

### Justificación local vs nube

| Componente | Dónde | Por qué |
|---|---|---|
| **RabbitMQ** | Local (k3d) | Broker de mensajería: latencia predecible, sin costo, accesible via port-forward. No requiere alta disponibilidad en esta etapa |
| **Splitter / Joiner** | Local (Python) | Procesan una sola vez por imagen; no justifica costo de VM. Se benefician del acceso directo al filesystem local para leer/escribir la imagen |
| **Workers Sobel** | Nube (GCP e2-micro) | Cómputo intensivo y paralelizable. Se crean bajo demanda y se destruyen al terminar → costo proporcional al trabajo real. Terraform permite escalar N sin cambiar código |

---

## Requisitos previos

- Python 3.11
- Docker Desktop
- k3d + kubectl
- Terraform >= 1.5
- gcloud CLI autenticado (`gcloud auth application-default login`)
- GCP project con Compute Engine API habilitada
- Bucket GCS `sobel-terraform-state` creado

---

## Ejecución desde la terminal


### 1. Configurar Terraform

Editar `terraform/terraform.tfvars` (no committear — está en .gitignore):

```hcl
project_id    = "mi-proyecto-gcp"
region        = "us-central1"
zone          = "us-central1-a"
worker_count  = 3

rabbitmq_user = "user"
rabbitmq_pass = "password"
docker_image  = "gcr.io/mi-proyecto/sobel-worker:latest"
```
(tambien se debe configurar un .env con las variables RABBITMQ_USER y RABBITMQ_PASS que deben coincidir con las que tiene terraform.tfvars)
### 2. Buildear y pushear la imagen del worker

```bash
docker build -t gcr.io/MI_PROYECTO/sobel-worker:latest .
gcloud auth configure-docker gcr.io
docker push gcr.io/MI_PROYECTO/sobel-worker:latest
```

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### 4. Seleccionar ubicacion del Hit 2

```bash
cd TP3/Hit2
```

### 5. Ejecutar el proceso principal

```bash
python ProcesoPrincipal.py /ruta/imagen.jpg /ruta/salida_sobel.jpg
```

El proceso:
1. Llama `terraform apply` → crea las VMs en GCP
2. Espera que los workers pasen el health check (`GET :8000/health`)
3. Divide la imagen en fragmentos y los envía a la cola `tareas`
4. Los workers consumen, aplican Sobel, publican en `resultado`
5. El joiner reconstruye la imagen y la guarda
6. Llama `terraform destroy` → elimina las VMs

---

## Health checks

| Servicio | Endpoint | Respuesta |
|---|---|---|
| ProcesoPrincipal | `http://localhost:9013/health` | `{"servicio": "proceso_principal", "status": "running"}` |
| Splitter | `http://localhost:9000/health` | `{"servicio": "splitter", "status": "running"}` |
| Joiner | `http://localhost:9001/health` | `{"servicio": "joiner", "status": "running"}` |
| Worker VM | `http://<IP_VM>:8000/health` | `{"servicio": "worker-N", "status": "running"}` |

---

## Infraestructura como código

```
terraform/
├── provider.tf    # GCP provider + backend GCS remoto (sobel-terraform-state)
├── variables.tf   # project_id, region, zone, worker_count, rabbitmq_*, docker_image
├── main.tf        # google_compute_instance × worker_count + firewall
└── outputs.tf     # worker_ips[]
```

**Remote state**: GCS bucket `sobel-terraform-state` con prefix `terraform/state`.  
No se acepta `terraform.tfstate` en el repositorio.

---

## CI/CD

El pipeline `.github/workflows/hit2-ci.yml`:

- **Pull Request** → `terraform plan` y publica el output como comentario en el PR
- **Merge a main** → `terraform apply -auto-approve`

Variables necesarias en GitHub:
- `vars.GCP_PROJECT_ID`, `vars.GCP_REGION`, `vars.GCP_ZONE`
- `vars.HIT2_WORKER_COUNT` (default: 3)
- `vars.HIT2_RABBITMQ_HOST`, `vars.RABBITMQ_USER`
- `vars.HIT2_WORKER_IMAGE`
- `secrets.GCP_SA_KEY`, `secrets.RABBITMQ_PASS`

---

## Decisiones de diseño

| Decisión | Alternativa | Razón |
|---|---|---|
| RabbitMQ en k3d local | RabbitMQ en GCP VM | Simplicidad: no requiere exponer el broker a internet ni configurar VPN. El master accede directamente vía localhost |
| Workers en e2-micro | e2-standard | Balancear costo vs capacidad para una demo. Para imágenes grandes se puede cambiar `machine_type` en una variable |
| `terraform destroy` al terminar | Apagar VMs (stop) | Costo cero entre ejecuciones. Las VMs de GCP cobran aunque estén detenidas (disco) |
| Tolerancia a fallos con resubmisión | Sin tolerancia | Si un worker no responde en 20s, ProcesoPrincipal reenvía la tarea. Evita que una VM con problema bloquee el pipeline completo |
