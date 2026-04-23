# Hit #0 - Patrones de Mensajería con RabbitMQ

## Estructura del proyecto

```
Hit0/
├
├── ejemplo1/
│   ├── productor.py
│   ├── consumidor.py
│   └── README.md
├── ejemplo2/
│   ├── publicador.py
│   ├── suscriptor.py
│   └── README.md
├── ejemplo3/
│   ├── setup.py
│   ├── productor.py
│   ├── consumidor.py
│   ├── consumidor_dlq.py
│   └── README.md
└── ejemplo4/
    ├── setup.py
    ├── productor.py
    ├── consumidor.py
    └── README.md
```

## Prerrequisitos

```bash
# 1. Levantar RabbitMQ con Docker
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

# 2. Instalar dependencias Python
pip install -r requirements.txt

---

## Ejemplo 1 - Message Queue (Punto a Punto)

### Diagrama de arquitectura

```
╔══════════════╗     publish      ╔═══════════════════╗     consume     ╔═══════════════╗
║  Productor   ║ ───────────────► ║  Cola: "tareas"   ║ ──────────────► ║ Consumidor A  ║
║  (10 tareas) ║                  ║  (durable, FIFO)  ║                 ╚═══════════════╝
╚══════════════╝                  ╚═══════════════════╝
                                                         ──────────────► ╔═══════════════╗
                                                                         ║ Consumidor B  ║
                                                                         ╚═══════════════╝
                                          Round-robin: A recibe mensajes impares,
                                                       B recibe mensajes pares
```

### Comportamiento observado

**Con 1 consumidor**: recibe los 10 mensajes secuencialmente.

**Con 2 consumidores (round-robin)**:
- Consumidor A: Tarea #1, #3, #5, #7, #9
- Consumidor B: Tarea #2, #4, #6, #8, #10
- Ningún mensaje se duplica; cada uno es procesado exactamente una vez.

---

## Ejemplo 2 - Event Bus / Pub-Sub (Fan-out)

### Diagrama de arquitectura

```
                              ╔══════════════════════════════╗
                              ║  Exchange: blockchain_eventos  ║
╔═══════════════╗  publish    ║  Tipo: FANOUT                ║
║  Publicador   ║ ──────────► ║  (ignora routing_key,        ║
║ "nuevo bloque"║             ║   copia a todas las colas)   ║
╚═══════════════╝             ╚══════════════════════════════╝
                                 │              │              │
                         bind    ▼      bind    ▼      bind    ▼
                    ╔══════════════╗ ╔══════════════╗ ╔══════════════╗
                    ║ Cola nodo1   ║ ║ Cola nodo2   ║ ║ Cola nodo3   ║
                    ║ (exclusiva)  ║ ║ (exclusiva)  ║ ║ (exclusiva)  ║
                    ╚══════════════╝ ╚══════════════╝ ╚══════════════╝
                           │                │                │
                           ▼                ▼                ▼
                    ╔════════════╗  ╔════════════╗  ╔════════════╗
                    ║ Suscriptor ║  ║ Suscriptor ║  ║ Suscriptor ║
                    ║  nodo1     ║  ║  nodo2     ║  ║  nodo3     ║
                    ╚════════════╝  ╚════════════╝  ╚════════════╝
                    Todos reciben el mismo mensaje (copia idéntica)
```

---

## Ejemplo 3 - Dead Letter Queue (DLQ)

### Diagrama de arquitectura

```
╔═══════════╗          ╔═══════════════════════════════════════════════╗
║ Productor ║ ────────►║ Cola: "cola_principal"                        ║
╚═══════════╝          ║ x-dead-letter-exchange: dlx_exchange          ║
                       ║ x-dead-letter-routing-key: mensajes_fallidos  ║
                       ╚═══════════════════════════════════════════════╝
                                          │
                                          ▼
                                   ╔════════════╗
                                   ║ Consumidor ║
                                   ╚════════════╝
                                    │          │
                          error=false          error=true
                                    │          │
                                    ▼          ▼
                                  ACK()    NACK(requeue=False)
                                    │          │
                                    ▼          ▼
                               ✓ Procesado    ╔══════════════════╗
                                              ║ DLX Exchange     ║
                                              ║ "dlx_exchange"   ║
                                              ╚══════════════════╝
                                                       │
                                              routing_key: "mensajes_fallidos"
                                                       │
                                                       ▼
                                              ╔════════════════════╗
                                              ║ Cola: "cola_muertos"║
                                              ║       (DLQ)         ║
                                              ╚════════════════════╝
                                                       │
                                                       ▼
                                              ╔════════════════════╗
                                              ║  Consumidor DLQ    ║
                                              ║  (Auditor/Alertas) ║
                                              ╚════════════════════╝
```

---

## Ejemplo 4 - Retry con Exponential Backoff

### Diagrama de arquitectura

```
╔═══════════╗
║ Productor ║ ──► [retry_exchange] ──► ╔═══════════════╗
╚═══════════╝      routing: "trabajo"  ║  cola_trabajo  ║◄────────────────────────────┐
                                       ╚═══════════════╝                             │
                                               │                                     │ TTL expira
                                               ▼                                     │ → vuelve a
                                        ╔════════════╗                               │   cola_trabajo
                                        ║ Consumidor ║                               │
                                        ╚════════════╝                               │
                                         │         │                                 │
                                        OK        FALLO                              │
                                         │         │                                 │
                                       ACK()    intento 1 ──► [cola_espera_1s] TTL=1s──►┤
                                                 intento 2 ──► [cola_espera_2s] TTL=2s──►┤
                                                 intento 3 ──► [cola_espera_4s] TTL=4s──►┤
                                                 intento 4 ──► [cola_espera_8s] TTL=8s──►┘
                                                 intento 5 ──► ╔═══════════════════════╗
                                                               ║ cola_muertos_retry    ║
                                                               ║       (DLQ)           ║
                                                               ╚═══════════════════════╝
```

---

## Comparación de patrones

| Dimensión              | Ej.1 - Message Queue    | Ej.2 - Pub-Sub Fanout     | Ej.3 - DLQ                    | Ej.4 - Retry Backoff          |
|------------------------|-------------------------|---------------------------|-------------------------------|
| **Objetivo**           | Distribuir trabajo      | Broadcast de eventos      | Capturar mensajes fallidos    | Manejar fallos transitorios   |
| **Receptores**         | 1 de N consumidores     | Todos los suscriptores    | Consumidor DLQ (auditor)      | Mismo consumidor, con delay   |
| **Tipo de exchange**   | Default (direct)        | Fanout                    | Direct (DLX)                  | Direct + colas TTL            |
| **Colas**              | 1 compartida            | 1 por suscriptor          | Principal + DLQ               | Principal + N colas de espera |
| **Duplicación**        | No                      | Sí (por diseño)           | No                            | No (mismo mensaje, reintento) |
| **Uso principal**      | Task queues, workers    | Notificaciones, eventos   | Auditoría, no-pérdida         | Resiliencia ante fallos       |

## Cuándo usar cada patrón

### Message Queue (Ej. 1)
- Procesamiento paralelo de tareas (renderizado, encoding, ETL).
- Balance de carga entre múltiples workers.
- El orden relativo no es crítico entre consumidores.

### Pub-Sub Fanout (Ej. 2)
- Todos los servicios deben reaccionar a un evento (invalidación de caché, sincronización de estado).
- El publicador no conoce ni le importa quiénes son los suscriptores.
- Arquitecturas event-driven con múltiples consumidores heterogéneos.

### Dead Letter Queue (Ej. 3)
- Cualquier sistema donde perder mensajes es inaceptable.
- Sistemas financieros, transacciones, eventos críticos de negocio.
- Permite auditoría, alertas, y reprocesamiento manual posterior.

### Retry con Exponential Backoff (Ej. 4)
- Integración con APIs externas sujetas a rate limits o timeouts.
- Fallos transitorios: servicio caído brevemente, contención en BD.
- Evitar saturar servicios en problemas; dar tiempo a la recuperación.
