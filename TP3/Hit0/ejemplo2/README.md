# Ejemplo 2 - Event Bus / Pub-Sub (Fanout)

## Descripción

Este ejemplo implementa el patrón **Publish/Subscribe (Pub/Sub)** utilizando un
**exchange de tipo fanout en RabbitMQ**.

Un publicador envía eventos de "nuevo_bloque" a un exchange, y todos los
suscriptores reciben una copia idéntica del mensaje.

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

## Cómo ejecutar

```bash
# Levantar contenedor
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

# Levantar los 3 suscriptores (nodos de la red):
python suscriptor.py nodo1   # Terminal 1
python suscriptor.py nodo2   # Terminal 2
python suscriptor.py nodo3   # Terminal 3

# Luego publicar eventos:
python publicador.py         # Terminal 4
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