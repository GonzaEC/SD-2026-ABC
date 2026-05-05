# Ejemplo 2 - Event Bus / Pub-Sub (Fanout)
## Descripción

Este ejemplo implementa el patrón Publish/Subscribe (Pub/Sub) utilizando un exchange de tipo fanout en RabbitMQ.
Un publicador envía eventos de “nuevo bloque minado” a un exchange, y todos los suscriptores reciben una copia idéntica del mensaje.
Cada suscriptor representa un nodo distinto de la red distribuida.

## Arquitectura

```
                        ┌──► [Cola nodo1] ──► [Suscriptor nodo1]
[Publicador] ──► [Exchange: eventos (fanout)] ──► [Cola nodo2] ──► [Suscriptor nodo2]
                        └──► [Cola nodo3] ──► [Suscriptor nodo3]
```

## Conceptos clave

- **Exchange fanout**:
  - Reenvía cada mensaje a **todas** las colas vinculadas
  - No utiliza `routing_key`

- **Colas exclusivas**:
  - Cada suscriptor tiene su propia cola
  - Se eliminan automáticamente al desconectarse

- **Broadcast**:
  - Todos los suscriptores reciben el mismo mensaje

## Tecnologías utilizadas
Python 3.11
RabbitMQ
pika (cliente AMQP)
FastAPI + Uvicorn (health checks)
Docker
Kubernetes (k3d / k3s)

## Cómo ejecutar (primera vez)
```bash
# 0. Posicionarse en el proyecto
cd TP3\queue\ex2   # (o la carpeta correspondiente)

# 1. Crear cluster Kubernetes local
k3d cluster create sobel

# 2. Desplegar RabbitMQ
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/rabbitmq-service.yaml

# 3. Construir imágenes Docker
docker build -f Dockerfile.publicador -t publicador-ex2:latest .
docker build -f Dockerfile.suscriptor -t suscriptor-ex2:latest .

# 4. Importar imágenes al cluster
k3d image import publicador-ex2:latest -c sobel
k3d image import suscriptor-ex2:latest -c sobel

# 5. Levantar 3 suscriptores (nodos)
kubectl apply -f k8s/subscriber-deployment.yaml

# 6. Ejecutar publicador (Job)
kubectl apply -f k8s/publisher-job.yaml

# 7. Verificar pods
kubectl get pods

# 8. Ver logs
kubectl logs -f <pod-publicador>
kubectl logs <pod-suscriptor-1>
kubectl logs <pod-suscriptor-2>
kubectl logs <pod-suscriptor-3>
```

## Cómo volver a ejecutar el ejemplo (sin recrear cluster)

### Sin cambios de código:
```bash
kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/rabbitmq-service.yaml
kubectl apply -f k8s/subscriber-deployment.yaml
kubectl apply -f k8s/publisher-job.yaml
```

### Con cambios en código:
```bash
docker build -f Dockerfile.publicador -t publicador-ex2:latest .
docker build -f Dockerfile.suscriptor -t suscriptor-ex2:latest .

k3d image import publicador-ex2:latest -c sobel
k3d image import suscriptor-ex2:latest -c sobel

kubectl apply -f k8s/rabbitmq-deployment.yaml
kubectl apply -f k8s/rabbitmq-service.yaml
kubectl apply -f k8s/subscriber-deployment.yaml
kubectl apply -f k8s/publisher-job.yaml
```

## Limpieza de recursos
```bash
kubectl delete job publicador
kubectl delete deployment suscriptor
kubectl delete service rabbitmq
kubectl delete deployment rabbitmq
```

## Eliminación completa del entorno (opcional)
```bash
k3d cluster delete sobel
```

## Resultado esperado

Cada mensaje enviado por el publicador:
[PUBLICADOR] Enviado: {'evento': 'nuevo_bloque', 'numero': 1}

Es recibido por TODOS los nodos:
[nodo1] Recibido: {'evento': 'nuevo_bloque', 'numero': 1}
[nodo2] Recibido: {'evento': 'nuevo_bloque', 'numero': 1}
[nodo3] Recibido: {'evento': 'nuevo_bloque', 'numero': 1}

## Endpoints de salud (Health Check)

Cada componente expone un endpoint HTTP utilizando FastAPI para verificar su estado:

### Suscriptores (puerto según nodo)
http://localhost:8001/health   # nodo1
http://localhost:8002/health   # nodo2
http://localhost:8003/health   # nodo3

### Publicador
http://localhost:9000/health

### Ejemplo de respuesta:
{
  "servicio": "suscriptor_nodo1",
  "status": "running",
  "rabbitmq": "connected"
}

## Logs (Memoria y Disco)

Se implementó logging con:
Consola (memoria): monitoreo en tiempo real
Archivo (disco): auditoría y trazabilidad
Ubicación
/logs
   ├── nodo1.log
   └── nodo2.log
   └── nodo3.log
   └── publicador.log

## Tests
Se incluyeron pruebas utilizando pytest:

### Tests unitarios
test_publicador.py → verifica envío de eventos
test_suscriptor.py → verifica procesamiento de mensajes

### Test de integración
test_integracion.py → valida que un evento publicado sea recibido por múltiples suscriptores (fanout)

### Ejecutar tests
```bash
pytest -v
```