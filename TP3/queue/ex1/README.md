# Ejemplo 1 - Message Queue (Punto a Punto)

## Descripción

Este ejemplo implementa el patrón de mensajería **Message Queue (Point to Point)** utilizando RabbitMQ como broker AMQP.

Un productor envía 10 tareas numeradas a una cola llamada `tareas`, mientras que uno o más consumidores reciben los mensajes desde dicha cola.

La característica principal del patrón es que cada mensaje es consumido por exactamente un consumidor.


## Objetivo del ejemplo
Demostrar:

- comunicación asincrónica entre procesos,
- desacoplamiento productor/consumidor,
- persistencia de cola y mensajes,
- ACK manual,
- distribución automática de carga entre múltiples consumidores.

## Arquitectura lógica

```text
                    ┌────────────────────┐
                    │   Productor (Job)  │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ RabbitMQ Queue      │
                    │      tareas         │
                    └───────┬───────┬────┘
                            │       │
                            ▼       ▼
                  ┌────────────┐ ┌────────────┐
                  │Consumidor 1│ │Consumidor 2│
                  └────────────┘ └────────────┘
```
## Tecnologias utilizadas
Python 3.11
RabbitMQ
pika (cliente AMQP)
FastAPI + Uvicorn (health checks)
Docker
Kubernetes local con k3d/k3s

## Cómo ejecutar (primera vez)
```bash
# 0. Estar parado en la carpeta correcta
cd TP3\queue\ex1
# 1. Crear cluster Kubernetes local
k3d cluster create sobel
# 2. Desplegar RabbitMQ en Kubernetes
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/rabbitmq-service.yaml
# 3. Construir imágenes Docker de la aplicación
docker build -f Dockerfile.consumer -t consumidor-ex1:latest .
docker build -f Dockerfile.producer -t productor-ex1:latest .
# 4. Importar imágenes al cluster k3d
k3d image import consumidor-ex1:latest -c sobel
k3d image import productor-ex1:latest -c sobel
# 5. Levantar dos consumidores
kubectl apply -f k8s/consumer-deployment.yaml
# 6. Ejecutar productor (envía las 10 tareas)
kubectl apply -f k8s/producer-job.yaml
# 7. Verificar estado
kubectl get pods
# 8. Verificar funcionamiento
kubectl logs -f <nombre_del_pod_productor>
kubectl logs <pod_consumidor_1>
kubectl logs <pod_consumidor_2>
```

## Cómo volver a ejecutar el ejemplo (sin recrear el cluster)
Si el cluster sobel ya existe, no es necesario volver a crearlo.

Si NO hubo cambios en el código:
```bash
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/rabbitmq-service.yaml
kubectl apply -f k8s/consumer-deployment.yaml
kubectl apply -f k8s/producer-job.yaml
```

Si hubo cambios en consumidor.py o productor.py:
```bash
docker build -f Dockerfile.consumer -t consumidor-ex1:latest .
docker build -f Dockerfile.producer -t productor-ex1:latest .

k3d image import consumidor-ex1:latest -c sobel
k3d image import productor-ex1:latest -c sobel

kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/rabbitmq-service.yaml
kubectl apply -f k8s/consumer-deployment.yaml
kubectl apply -f k8s/producer-job.yaml
```

## Limpieza de recursos Kubernetes

Una vez finalizada la ejecución:
```bash
kubectl delete job productor
kubectl delete deployment consumidor
kubectl delete service rabbitmq
kubectl delete deployment rabbitmq
```
Esto elimina únicamente los recursos del ejercicio, pero mantiene el cluster sobel disponible para futuras ejecuciones.

## Eliminación completa del entorno (opcional)

Si se desea borrar todo el entorno Kubernetes local:
```bash
k3d cluster delete sobel
```

Para volver a correr el ejemplo luego de esto, se debe comenzar nuevamente desde el paso 1.

## Comportamiento observado

### Con 1 consumidor
- El consumidor recibe los 10 mensajes en orden secuencial.
- No hay competencia: procesa 1 mensaje por vez (gracias a `prefetch_count=1`).

### Con 2 consumidores (A y B)
RabbitMQ distribuye los mensajes en **round-robin**:
- Consumidor A recibe: Tarea #1, Tarea #3, Tarea #5, Tarea #7, Tarea #9
- Consumidor B recibe: Tarea #2, Tarea #4, Tarea #6, Tarea #8, Tarea #10

Cada mensaje llega a **un solo** consumidor. Ningún mensaje se duplica.

## Conceptos clave

| `durable=True` | La cola sobrevive reinicios del broker |
| `delivery_mode=2` | Los mensajes son persistentes en disco |
| `basic_qos(prefetch_count=1)` | Fair dispatch: no sobrecargar un worker lento |
| `auto_ack=False` | ACK manual: el mensaje no se descarta hasta confirmar procesamiento |
| `RABBITMQ_HOST=rabbitmq` | Resolución DNS interna de Kubernetes |

## Endpoints de salud (Health Check)
Los contenedores exponen endpoints HTTP para validación de estado.

Consumidores
/health
Productor
/health

(Accesibles dentro del pod para monitoreo interno)

## Logs (Memoria y Disco)
Los logs registran:
envío de tareas,
recepción,
procesamiento,
confirmación implícita por ACK.

Esto permitió verificar experimentalmente la distribución de mensajes entre pods consumidores.

## Se implementaron pruebas unitarias y de integración.

Estructura
tests/
├── test_productor.py
├── test_consumidor.py
├── test_integracion.py
└── conftest.py

## Ejecutar tests
```bash
pytest -v
```

### Tipos de pruebas
#### Unitarias
    Productor: Verifica que se envían 10 mensajes, usa mocks (no requiere RabbitMQ).
    Consumidor: Verifica que procesa mensajes y hace ACK

#### Integración
    Valida el flujo completo: Productor → Cola → Consumidor
    Usa RabbitMQ real
    Verifica:
        envío correcto
        recepción
        procesamiento
Requiere RabbitMQ en ejecución


