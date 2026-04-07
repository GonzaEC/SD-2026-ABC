# TP2 - Punto 2: Concurrencia y Exclusión Mutua

## Descripción

Este proyecto implementa un sistema distribuido que permite ejecutar tareas remotas (operaciones matemáticas) utilizando contenedores Docker, incorporando concurrencia, sincronización y métricas de rendimiento.

El sistema está compuesto por:

* Un cliente (CLI y web)
* Un servidor central (FastAPI)
* Un pool de workers
* Contenedores Docker que ejecutan las tareas

Se agregan los siguientes conceptos:

* Pool dinámico de workers
* Cola de tareas con exclusión mutua
* Relojes lógicos de Lamport
* Métricas de throughput
* Endpoint de health check

---

## Cómo ejecutar el proyecto

### 1. Requisitos

* Python 3
* Docker Desktop (en ejecución)
* pip

Verificar instalación:

```bash
python --version
docker --version
```

---

### 2. Instalar dependencias

```bash
cd ./TP2/Punto2
```

```
pip install -r requirements.txt
```

---

### 3. Construir las imagenes Docker

```bash
docker build -t servicio-tarea:1.0 -f servicio-tarea.dockerfile .
```
```bash
docker build -t servidor:1.0 -f servidor.dockerfile .
```

---

### 4. Ejecutar el servidor
```bash
docker run -d -p 7685:7685 -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}/logs:/app/logs servidor:1.0
```

### 5. Ejecutar cliente (CLI)

```bash
python cliente.py POST suma "[2,3]" "[]" servicio-tarea:1.0
```

---


### 6. Cliente Web (opcional)

Abrir el archivo (permite ejecutar de a un cliente o probar la concurrencia con 3 clientes):

```
index.html
```

---

### 7. Métricas del sistema

```
http://127.0.0.1:7685/metrics
```

---

### 8. Health Check

```
http://127.0.0.1:7685/health
```

---

### 9. Tests

```bash
pytest tests/
```

---

##  Diagrama de Arquitectura

```
        +-------------------+
        |      Cliente      |
        | (CLI / Web)       |
        +--------+----------+
                 |
                 v
        +-------------------+
        |     Servidor      |
        |  (En contenedor   |
        |     docker)       |
        |-------------------|
        | - Cola de tareas  |
        | - Pool workers    |
        | - Lamport clock   |
        +--------+----------+
                 |
     -------------------------
     |      |       |        |
     v      v       v        v
+--------+ +--------+ +--------+ +--------+
|Worker 0| |Worker 1| |Worker 2| |Worker 3|
+--------+ +--------+ +--------+ +--------+
     |         |         |         |
     v         v         v         v
+--------------------------------------+
|     Contenedores Docker              |
|  (servicio-tarea:1.0)                |
|  FastAPI ejecutando operaciones      |
+--------------------------------------+
```

---

## Decisiones de Diseño

### Pool de Workers

Se implementa un pool dinámico de threads.

Configuración:

* MIN_WORKERS = 1
* MAX_WORKERS = 4

Funcionamiento:

* El sistema comienza con un mínimo de workers.
* A medida que aumenta la carga, se crean nuevos workers.
* Cada worker procesa tareas de manera independiente.

---

### Cola de Tareas

Se utiliza una cola con prioridad (PriorityQueue) basada en timestamps de Lamport.

Las tareas se encolan si no hay workers disponibles
Se limita el tamaño con MAX_STACK
Se evita saturación mediante programación defensiva

---

### Exclusión Mutua

Se utilizan locks (`threading.Lock`) para evitar condiciones de carrera.

Protege:

* Cola de tareas
* Contador de carga (carga_actual)
* Pool de workers
* Reloj de Lamport

Garantiza consistencia en ejecución concurrente.

---

### Relojes de Lamport

Eventos definidos:

* ENVIADO: cuando el servidor recibe una tarea del cliente
* RECIBIDO: cuando un worker toma la tarea
* FIN: cuando la tarea termina

Funcionamiento:

* En SEND: se incrementa el reloj
* En RECEIVE:
     L = max(L, timestamp_recibido) + 1
* En FIN: se incrementa nuevamente

Esto permite un orden consistente de eventos sin depender del reloj físico.

---

### Ejecución de Tareas

Cada worker:

1. Toma una tarea de la cola
2. Levanta un contenedor Docker
3. Ejecuta la tarea vía HTTP (`/ejecutarTarea`)
4. Obtiene el resultado
5. Detiene el contenedor

---

### Programación Defensiva

Se implementaron controles para evitar errores:

* Validación de parámetros
* Límite de cola (`MAX_STACK`)
* Manejo de errores en Docker
* Timeout en requests
* Manejo de excepciones

---

### Metricas

Se exponen métricas mediante `/metrics`:

* tareas completadas
* tiempo de ejecución
* throughput (tareas por minuto)
* workers activos
* tamaño de cola
* carga actual

---

### Health Check

Endpoint `/health` que devuelve:

* estado del servidor
* estado de Docker
* cantidad de workers
* cola de tareas
* uptime

---

## Análisis de rendimiento

Se evaluó el throughput variando la cantidad de workers (en el informe se encuentra este proceso y sus resultados detallados).


## Pruebas

Se implementaron:

### Tests Unitarios

* Validan las operaciones matemáticas en `docker.py`

### Tests de Integración

* Verifican el flujo completo:
  Cliente → Servidor → Worker → Contenedor

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
pytest tests/testUnitario.py -v

# Solo integración
pytest tests/testIntegracion.py -v
```
