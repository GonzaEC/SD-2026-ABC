# Ejemplo 4 - Retry con Exponential Backoff

## Descripción

Cuando un mensaje falla, en lugar de descartarlo o reencolar inmediatamente,
se lo envía a una **cola de espera con TTL** (time-to-live). Al expirar, RabbitMQ
lo reenvía automáticamente a la cola principal. El delay se duplica en cada intento.
Tras 4 fallos → DLQ.

## Arquitectura

```
[Productor]
    │
    ▼
[Exchange: retry_exchange]
    │ routing_key: "trabajo"
    ▼
[Cola: cola_trabajo] ◄──────────────────────────────────────────┐
    │                                                            │
    ▼                                                            │ (TTL expira)
[Consumidor]                                                     │
    ├──     ÉXITO → basic_ack() →                                │
    └──    FALLO                                                 │
            │                                                    │
            ├── intento 1 → [cola_espera_1s] ─── TTL 1000ms ───►┤
            ├── intento 2 → [cola_espera_2s] ─── TTL 2000ms ───►┤
            ├── intento 3 → [cola_espera_4s] ─── TTL 4000ms ───►┤
            ├── intento 4 → [cola_espera_8s] ─── TTL 8000ms ───►┘
            └── intento 5 → [DLQ: cola_muertos_retry] 
```

## Mecanismo de delay sin plugins

Las colas de espera tienen configurado:
- `x-message-ttl`: cuánto tiempo retener el mensaje
- `x-dead-letter-exchange`: a dónde enviarlo al expirar
- `x-dead-letter-routing-key`: routing key al expirar

Cuando el TTL se cumple, el mensaje "muere" de la cola de espera y RabbitMQ
lo reenvía al exchange configurado → vuelve a `cola_trabajo`.

## Cómo ejecutar (primera vez)
```bash
# 0. Posicionarse en el proyecto
cd TP3\queue\ex4   # (o la carpeta correspondiente)

# 1. Crear cluster Kubernetes local
k3d cluster create sobel

# 2. Desplegar RabbitMQ
kubectl apply -f k8s/rabbitmq.yaml

# 3. Construir imágenes Docker
docker build -f Dockerfile.setup -t setup-retry:latest .
docker build -f Dockerfile.productor -t productor-retry:latest .
docker build -f Dockerfile.consumidor -t consumidor-retry:latest .

# 4. Importar imágenes al cluster
k3d image import setup-retry:latest -c sobel
k3d image import productor-retry:latest -c sobel
k3d image import consumidor-retry:latest -c sobel

# 5. Desplegar setup (infraestructura retry)
kubectl apply -f k8s/setup.yaml

# 6. Levantar consumidor
kubectl apply -f k8s/consumidor.yaml

# 7. Ejecutar productor (Job)
kubectl apply -f k8s/productor.yaml

# 8. Verificar pods
kubectl get pods

# 9. Ver logs
kubectl logs -f <pod-productor>
kubectl logs -f <pod-consumidor>
kubectl logs -f <pod-setup>
```

## Cómo volver a ejecutar el ejemplo (sin recrear cluster)
## Sin cambios de código:
```bash
kubectl apply -f k8s/rabbitmq.yaml
kubectl apply -f k8s/setup.yaml
kubectl apply -f k8s/consumidor.yaml
kubectl apply -f k8s/productor.yaml
```

## Con cambios en código:
```bash
docker build -f dockerfile.setup -t setup-retry:latest .
docker build -f dockerfile.productor -t productor-retry:latest .
docker build -f dockerfile.consumidor -t consumidor-retry:latest .

k3d image import setup-retry:latest -c sobel
k3d image import productor-retry:latest -c sobel
k3d image import consumidor-retry:latest -c sobel

kubectl apply -f k8s/setup.yaml
kubectl apply -f k8s/consumidor.yaml
kubectl apply -f k8s/productor.yaml
```

## Limpieza de recursos
```bash
kubectl delete job productor
kubectl delete job setup
kubectl delete deployment consumidor
kubectl delete service rabbitmq
kubectl delete deployment rabbitmq
```

## Eliminación completa del entorno (opcional)
```bash
k3d cluster delete sobel
```

## Log de ejemplo

```
10:15:00 Tarea #1: 'Llamada a API externa'
10:15:00 Intento #1 de 4
10:15:00 Tarea #1 FALLÓ en intento #1
10:15:00   → Reintento #1: esperando 1s en 'cola_espera_1s'
10:15:01 Tarea #1: 'Llamada a API externa'
10:15:01 Intento #2 de 4
10:15:01 Tarea #1 FALLÓ en intento #2
10:15:01   → Reintento #2: esperando 2s en 'cola_espera_2s'
10:15:03 Tarea #1: 'Llamada a API externa'
10:15:03 Intento #3 de 4
10:15:03 Tarea #1 procesada exitosamente en intento #3!
```

## Secuencia de delays (Exponential Backoff)

| Intento | Delay | Cola de espera    | Delay acumulado |
|---------|-------|-------------------|-----------------|
| 1       | 1s    | cola_espera_1s    | 1s              |
| 2       | 2s    | cola_espera_2s    | 3s              |
| 3       | 4s    | cola_espera_4s    | 7s              |
| 4       | 8s    | cola_espera_8s    | 15s             |
| 5       | —     | cola_muertos_retry (DLQ) | —         |

## Por qué Exponential Backoff

El delay creciente permite que los recursos recuperen disponibilidad:
- **Tasa de fallos alta al inicio**: dar tiempo al servicio caído.
- **Evitar thundering herd**: si se reintenta de inmediato, se satura aún más.
- **Proporcional al problema**: delays cortos para fallos breves, largos para outages.

## Cuándo usar este patrón

- Llamadas a APIs externas con rate limits o timeouts.
- Escrituras a bases de datos con contención temporaria.
- Cualquier integración con servicios que pueden estar temporalmente no disponibles.
- Equivalentes en la industria: AWS SQS visibility timeout, Celery retry, Bull.js.

## Endpoints HTTP (Health Check)
Cada componente expone un endpoint HTTP para verificar su estado:
Productor → http://localhost:9001/health
Consumidor principal → http://localhost:8003/health

Esto permite monitoreo básico de disponibilidad

## Logs (Memoria y Disco)
Se implementó logging con:
Consola (memoria): monitoreo en tiempo real
Archivo (disco): auditoría y trazabilidad
Ubicación
/logs
   ├── consumidor.log
   └── productor.log

## Tests
Se incluyeron pruebas utilizando pytest:

### Tests unitarios
test_consumidor.py → Se separan 3 escenarios:
                    test_consumidor_procesa_ok → ACK directo
                    test_consumidor_hace_retry → reencola con delay
                    test_consumidor_envia_a_dlq → supera MAX_INTENTOS
test_productor.py → Verifica que envía mensajes a cola_trabajo
                    Mockeando pika.BlockingConnection
                    Valida contenido del mensaje y routing key

### Test de integración
test_integracion.py → Simula el flujo completo: Productor → cola_trabajo → consumidor → retry → DLQ
                      Verifica:
                        Mensaje reencolado correctamente con TTL
                        Incremento de intentos
                        Derivación final a DLQ cuando corresponde
                        
### Ejecutar tests
```bash
pytest -v
```
