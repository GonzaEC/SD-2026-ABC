# Ejemplo 1 - Message Queue (Punto a Punto)

## Descripcion
En este patrón, un productor envía mensajes a una cola y un consumidor (o varios) los recibe. 
La clave es que cada mensaje es procesado por un único consumidor, sin importar cuántos haya escuchando.

## Cuándo usarlo
Cuando se tienen tareas independientes que necesitan ser distribuidas entre workers.
Ejemplos claros: procesar órdenes de compra, redimensionar imágenes subidas por usuarios, enviar emails en cola, o cualquier trabajo que se pueda paralelizar sin que dos workers hagan lo mismo.

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

# Ejemplo 2 - Event Bus / Pub-Sub (Fanout)

## Descripcion
Acá el productor publica en un exchange, no en una cola directamente. Ese exchange replica el mensaje a todas las colas suscritas. Cada suscriptor tiene su propia cola exclusiva y recibe una copia completa del mensaje, independientemente de los demás.

## Cuando usarlo
Cuando un evento debe disparar múltiples acciones independientes al mismo tiempo.
Por ejemplo: un usuario se registra: simultáneamente se le manda un email de bienvenida, se crea su perfil y se notifica al equipo de ventas.
Otro caso típico es broadcasting de actualizaciones de estado a múltiples nodos de un sistema distribuido.

## Arquitectura

```
                        ┌──► [Cola nodo1] ──► [Suscriptor nodo1]
[Publicador] ──► [Exchange: eventos (fanout)] ──► [Cola nodo2] ──► [Suscriptor nodo2]
                        └──► [Cola nodo3] ──► [Suscriptor nodo3]
```

# Ejemplo 3 - Dead Letter Queue (DLQ)

## Descripcion
Una DLQ es una cola especial donde van a parar los mensajes que no pudieron ser procesados. Puede ser porque el consumidor los rechazó explícitamente, porque expiraron (TTL), o porque la cola de destino estaba llena. En lugar de perder esos mensajes, se redirigen a la DLQ para su análisis posterior.

## Cuando usarlo
En cualquier sistema productivo donde perder un mensaje sea inaceptable.
Por ejemplo: transacciones financieras fallidas, pedidos que no pudieron procesarse, o notificaciones que no llegaron. La DLQ permite revisar qué falló, corregir el problema y reprocesar.

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

# Ejemplo 4 - Retry con Exponential Backoff

## Descripcion
En lugar de descartar un mensaje fallido inmediatamente o mandarlo directo a la DLQ, se reintenta su procesamiento con esperas crecientes entre cada intento (1s, 2s, 4s, 8s). Si después de todos los intentos sigue fallando, ahí sí va a la DLQ.

## Cuando usarlo
Cuando los fallos son probablemente transitorios. Llamadas a APIs externas que pueden estar caídas momentáneamente, escrituras en base de datos bajo alta carga, integraciones con servicios de terceros con rate limiting, o cualquier operación de red que puede fallar por condiciones temporales.

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

### Comparación entre los 4 patrones

## Comparación de patrones

| Dimensión              | Ej.1 - Message Queue    | Ej.2 - Pub-Sub Fanout     | Ej.3 - DLQ                    | Ej.4 - Retry Backoff          |
|------------------------|-------------------------|---------------------------|-------------------------------|-------------------------------|
| **Objetivo**           | Distribuir trabajo      | Broadcast de eventos      | Capturar mensajes fallidos    | Manejar fallos transitorios   |
| **Receptores**         | 1 de N consumidores     | Todos los suscriptores    | Consumidor DLQ (auditor)      | Mismo consumidor, con delay   |
| **Tipo de exchange**   | Default (direct)        | Fanout                    | Direct (DLX)                  | Direct + colas TTL            |
| **Colas**              | 1 compartida            | 1 por suscriptor          | Principal + DLQ               | Principal + N colas de espera |
| **Duplicación**        | No                      | Sí (por diseño)           | No                            | No (mismo mensaje, reintento) |
| **Uso principal**      | Task queues, workers    | Notificaciones, eventos   | Auditoría, no-pérdida         | Resiliencia ante fallos       |