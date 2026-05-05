# Ejemplo 3 - Dead Letter Queue (DLQ)

## Descripción

Los mensajes que no pueden ser procesados (rechazados con NACK ) son
redirigidos automáticamente a una **Dead Letter Queue** a través de un
**Dead Letter Exchange (DLX)**. Un segundo consumidor audita estos mensajes fallidos.

## Arquitectura

```
[Productor]
    │
    ▼
[Cola: "cola_principal"]  ←── x-dead-letter-exchange: dlx_exchange
    │                          x-dead-letter-routing-key: mensajes_fallidos
    ▼
[Consumidor]
    ├── mensaje OK  → basic_ack()   → Procesado
    └── mensaje ERR → basic_nack(requeue=False)
                            │
                            ▼
                    [DLX Exchange: "dlx_exchange"]
                            │
                            ▼ routing_key: "mensajes_fallidos"
                    [Cola: "cola_muertos" (DLQ)]
                            │
                            ▼
                    [Consumidor DLQ / Auditor]
```

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
cd TP3\queue\ex3   # (o la carpeta correspondiente)

# 1. Crear cluster Kubernetes local
k3d cluster create sobel

# 2. Desplegar RabbitMQ
kubectl apply -f k8s/rabbitmq.yaml

# 3. Construir imágenes Docker
docker build -f Dockerfile.setup -t setup-dlq:latest .
docker build -f Dockerfile.productor -t productor-dlq:latest .
docker build -f Dockerfile.consumidor -t consumidor-dlq:latest .
docker build -f Dockerfile.dlq -t dlq-consumer:latest .

# 4. Importar imágenes al cluster
k3d image import setup-dlq:latest -c sobel
k3d image import productor-dlq:latest -c sobel
k3d image import consumidor-dlq:latest -c sobel
k3d image import dlq-consumer:latest -c sobel

# 5. Desplegar setup
kubectl apply -f k8s/setup.yaml

# 6. Levantar consumidores
kubectl apply -f k8s/consumidor-principal.yaml
kubectl apply -f k8s/consumidor-dlq.yaml

# 7. Ejecutar productor (Job)
kubectl apply -f k8s/productor-dlq.yaml

# 8. Verificar pods
kubectl get pods

# 9. Ver logs
kubectl logs -f <pod-productor>
kubectl logs -f <pod-consumidor>
kubectl logs -f <pod-dlq>
```

## Cómo volver a ejecutar el ejemplo (sin recrear cluster)
## Sin cambios de código:
```bash
kubectl apply -f k8s/rabbitmq.yaml
kubectl apply -f k8s/setup.yaml
kubectl apply -f k8s/consumidor.yaml
kubectl apply -f k8s/dlq-consumidor.yaml
kubectl apply -f k8s/productor.yaml
```

## Con cambios en código:
```bash
docker build -f Dockerfile.productor -t productor-dlq:latest .
docker build -f Dockerfile.setup -t setup-dlq:latest .
docker build -f Dockerfile.consumidor -t consumidor-dlq:latest .
docker build -f Dockerfile.dlq -t dlq-consumer:latest .

k3d image import setup-dlq:latest -c sobel
k3d image import productor-dlq:latest -c sobel
k3d image import consumidor-dlq:latest -c sobel
k3d image import dlq-consumer:latest -c sobel

kubectl apply -f k8s/setup.yaml
kubectl apply -f k8s/consumidor.yaml
kubectl apply -f k8s/dlq-consumidor.yaml
kubectl apply -f k8s/productor.yaml
```

## Limpieza de recursos
```bash
kubectl delete job productor-dlq
kubectl delete deployment consumidor-principal
kubectl delete deployment consumidor-dlq
kubectl delete service rabbitmq
kubectl delete deployment rabbitmq
kubectl delete job setup-dlq
```

## Eliminación completa del entorno (opcional)
```bash
k3d cluster delete sobel
```

## Comportamiento esperado

De los 8 mensajes enviados:
- **5 mensajes** (sin error) → procesados y descartados por el consumidor principal.
- **3 mensajes** (con error: IDs 2, 4, 6) → rechazados → aparecen en el auditor DLQ.

## Por qué esto es importante

Sin DLQ, los mensajes fallidos se **pierden para siempre** o quedan atrapados en
un loop infinito (si se reencolaran). La DLQ garantiza:

1. **Cero pérdida de mensajes**: los fallidos son capturados, no descartados.
2. **Auditoría**: se puede revisar qué falló y por qué.
3. **Reprocesamiento manual**: se pueden mover mensajes de la DLQ de vuelta a la
   cola principal una vez corregido el problema.
4. **Alertas**: el consumidor DLQ puede disparar alertas o abrir tickets.

## Endpoints HTTP (Health Check)
Cada componente expone un endpoint HTTP para verificar su estado:
Productor → http://localhost:9000/health
Consumidor principal → http://localhost:8001/health
Consumidor DLQ (Auditor) → http://localhost:8002/health

Esto permite monitoreo básico de disponibilidad

## Logs (Memoria y Disco)
Se implementó logging con:
Consola (memoria): monitoreo en tiempo real
Archivo (disco): auditoría y trazabilidad
Ubicación
/logs
   ├── consumidor.log
   └── dlq.log
   └── productor.log

## Tests
Se incluyeron pruebas utilizando pytest:

### Tests unitarios
test_consumidor.py → Validan la lógica del consumidor: ACK para mensajes válidos, NACK (sin requeue) para mensajes con error
test_productor.py → Validan que el productor envía mensajes
test_dlq.py → Validan que el auditor DLQ procesa correctamente

### Test de integración
test_integracion.py → Se simula el flujo completo: Mensaje con error es rechazado por el consumidor
                                                   Es redirigido a la DLQ
                                                   El auditor lo procesa correctamente

### Ejecutar tests
```bash
pytest -v
```