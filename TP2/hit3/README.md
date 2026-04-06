# Hit #3 - Coordinación y Tolerancia a Fallos

## Descripción
Implementación del algoritmo Bully para elección de líder en un sistema distribuido.
Se despliegan 3 instancias del servidor detrás de un load balancer nginx. 
Cuando el coordinador cae, el sistema detecta la falla y elige automáticamente un nuevo líder.

---

## Requisitos
- Docker Desktop instalado y corriendo
- Python 3.11+

---

## Instrucciones para ejecutar

### 1. Clonar el repositorio
```bash
git clone https://github.com/GonzaEC/SD-2026-ABC
cd hit3
```

### 2. Levantar todos los servicios
```bash
docker compose up --build
```

### 3. Verificar que los nodos están vivos
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### 4. Ver estado del cluster (quién es el coordinador)
```bash
curl http://localhost:8001/bully/status
curl http://localhost:8002/bully/status
curl http://localhost:8003/bully/status
```

### 5. Simular caída del coordinador
```bash
docker stop nodo3
```
Esperar ~5 segundos y verificar que nodo2 tomó el control:
```bash
curl http://localhost:8002/bully/status
```

### 6. Enviar una tarea al cluster (pasa por nginx)
```bash
curl -X POST http://localhost:7685/getRemoteTask \
  -H "Content-Type: application/json" \
  -d '{"calculo":"suma","parametros":"[1,2,3]","adicional":{"redondeo":-1,"absoluto":false},"imagen":"tu-imagen"}'
```

### 7. Ver estado desde el cliente
```bash
python cliente.py STATUS
```
---

## Tests

### Instalación de dependencias para testing
```bash
pip install pytest httpx fastapi requests
```

### Correr todos los tests
```bash
pytest tests/ -v
```

### Correr por separado
```bash
# Solo unitarios
pytest tests/test_unitario.py -v

# Solo integración
pytest tests/test_integracion.py -v
```

---

## Estructura del proyecto
```
hit3/
├── Dockerfile
├── requirements.txt
├── docker-compose.yml
├── servidor.py        # servidor HTTP + endpoints Bully
├── bully.py           # lógica del algoritmo Bully
├── cliente.py         # cliente HTTP
├── nginx/
│   └── nginx.conf     # configuración del load balancer
├── tests/
│   ├── test_unitario.py      # tests unitarios de bully.py
│   └── test_integracion.py   # tests de endpoints HTTP
└── logs/
    ├── nodo1/
    ├── nodo2/
    └── nodo3/
```

---

## Diagrama de arquitectura
```
                ┌─────────────┐
                │   Cliente   │
                └──────┬──────┘
                       │ HTTP
                ┌──────▼──────┐
                │    nginx    │  puerto 7685
                │ (LB)        │
                └──┬──┬───┬───┘
                   │  │   │
          ┌────────┘  │   └────────┐
          │           │            │
   ┌──────▼─────┐ ┌───▼──────┐ ┌──▼───────┐
   │   nodo1    │ │  nodo2   │ │  nodo3   │
   │  ID=1      │ │  ID=2    │ │  ID=3    │
   │  :8001     │ │  :8002   │ │  :8003   │
   │            │ │          │ │ LÍDER ★  │
   └────────────┘ └──────────┘ └──────────┘
          │           │            │
          └───────────┴────────────┘
                comunicación directa
                (Bully / heartbeat)
```

---

## Diagrama de secuencia — Elección de líder

### Estado normal
```
nodo1          nodo2          nodo3 (líder)
  │               │                │
  │──heartbeat───►│                │
  │               │──heartbeat────►│
  │──heartbeat────────────────────►│
  │               │                │
```

### Caída del líder y nueva elección
```
nodo1          nodo2          nodo3 (caído)
  │               │                x
  │──heartbeat────────────────────►x  (timeout)
  │               │──heartbeat────►x  (timeout)
  │               │
  │──ELECTION────►│
  │               │──OK───────────►│  (nodo2 > nodo1)
  │◄──OK──────────│
  │               │
  │               │── ELECTION ───►x  (no responde)
  │               │
  │               │ (nadie con ID mayor responde)
  │               │
  │◄──COORDINATOR─│  (nodo2 se proclama líder)
  │               │
  │  reconoce     │ ★ NUEVO LÍDER
```

-----

## Decisiones de diseño

### ¿Por qué Bully?
Es el algoritmo más simple de implementar y garantiza que siempre gana el nodo con mayor ID que esté vivo. Apropiado para un sistema pequeño con nodos conocidos.

### Dos canales de comunicación
- **nginx (puerto 7685):** tráfico de clientes, balanceado entre nodos
- **Comunicación directa entre nodos (puertos 8001-8003):** mensajes del protocolo Bully (ELECTION, OK, COORDINATOR) y heartbeat. No pasan por el load balancer.

### Variables de entorno
Cada nodo recibe su `NODE_ID` y la lista de `PEERS` por variable de entorno, lo que permite usar la misma imagen Docker para todos los nodos sin modificar el código.

### Tiempo de recuperación
En las pruebas realizadas el tiempo de recuperación fue de aproximadamente **4 segundos**, determinado por el parámetro `heartbeat_interval` configurado en `BullyNode`. Este valor es configurable.

### Heartbeat
Cada nodo le hace ping al coordinador vía `/health` cada 5 segundos. Si no responde en 3 segundos (`timeout`), inicia una nueva elección.

---

## Métricas observadas

| Métrica | Valor |
|---|---|
| Tiempo de detección de caída | ~5 segundos |
| Tiempo de nueva elección | ~1 segundo |
| Tiempo total de recuperación | ~4-6 segundos |
| Nodos probados | 3 |


---

## Referencias
- [GAR82] Garcia-Molina, H. (1982). "Elections in a Distributed Computing System". IEEE Transactions on Computers.
- [TAN17] Tanenbaum, A. S. & Van Steen, M. (2017). Distributed Systems: Principles and Paradigms (3rd ed.).
- [NGINX] nginx Documentation — Load Balancing. https://nginx.org/en/docs/http/load_balancing.html