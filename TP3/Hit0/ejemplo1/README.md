# Ejemplo 1 - Message Queue (Punto a Punto)

## Descripción

Un productor envía mensajes a una cola y los consumidores los reciben de forma exclusiva:
cada mensaje es procesado por **exactamente un** consumidor.

## Arquitectura

```
[Productor] ──► [Cola: "tareas"] ──► [Consumidor A]
                                 └──► [Consumidor B]  ← round-robin
```

## Cómo ejecutar

```bash
# Levantar contenedor Docker
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

# Terminal 1 - Consumidor A
python consumidor.py 1

# Terminal 2 - Consumidor B
python consumidor.py 2

# Terminal 3 - Productor
python productor.py
```

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

## Endpoints de salud (Health Check)
Cada servicio expone un endpoint HTTP para verificar su estado.

Consumidor 1 → http://localhost:8001/health
Consumidor 2 → http://localhost:8002/health
Productor → http://localhost:9000/health

Ejemplo de respuesta
{
  "servicio": "consumidor_1",
  "status": "running",
  "rabbitmq": "connected"
}

## Logs (Memoria y Disco)

Se implementó logging con:
Consola (memoria): monitoreo en tiempo real
Archivo (disco): auditoría y trazabilidad
Ubicación
/logs
   ├── consumidor.log
   └── productor.log


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


