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

## Cómo ejecutar

```bash
# Paso 1: Levantar contenedor
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

# Paso 2: crear la infraestructura 
python setup.py

# Paso 3: levantar el auditor de DLQ
python consumidor_dlq.py   # Terminal 1

# Paso 4: levantar el consumidor principal
python consumidor.py       # Terminal 2

# Paso 5: enviar mensajes
python productor.py        # Terminal 3
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