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

## Cómo ejecutar

```bash
# Paso 1: Levantar contenedor
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

# Paso 2: crear infraestructura
python setup.py

# Paso 3: levantar consumidor
python consumidor.py      # Terminal 1

# Paso 4: enviar tareas
python productor.py       # Terminal 2
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
