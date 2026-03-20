# TP1 - Sistemas Distribuidos

## Hit 8 - Refactorización a gRPC / Protocol Buffers

---

## Descripción

En este punto del trabajo práctico se refactoriza la comunicación implementada previamente en el **Hit #5**, donde los nodos se comunicaban utilizando **sockets TCP y mensajes serializados en JSON**.

El objetivo del Hit #8 es reemplazar ese mecanismo por **gRPC utilizando Protocol Buffers**, lo que permite:

* Definir un **contrato de comunicación claro**
* Generar automáticamente el código de cliente y servidor
* Reducir el tamaño de los mensajes transmitidos
* Mejorar la eficiencia de la comunicación
* Simplificar el manejo de serialización de datos

Además, se incorporan:

* Sistema de **logs en memoria y en disco**
* **Pruebas automatizadas** (unitarias e integración)
* Endpoint HTTP de **monitoreo del estado del sistema**

---

# Tecnologías utilizadas

* Python 3
* gRPC
* Protocol Buffers
* Flask (para endpoint de health check)
* unittest (testing)

---

# Estructura del proyecto

```
Punto8/
│
├── mensaje.proto
├── mensaje_pb2.py
├── mensaje_pb2_grpc.py
├── server.py
├── cliente.py
├── log/
├── tests/
│   ├── __init__.py
│   └── test_grpc.py
└── README.md
```
### Archivos principales

**mensaje.proto**

Define el contrato de comunicación entre cliente y servidor utilizando Protocol Buffers.

**mensaje_pb2.py**

Archivo generado automáticamente que contiene las clases de los mensajes.

**mensaje_pb2_grpc.py**

Archivo generado automáticamente que contiene los stubs de cliente y servidor.

**server.py**

Implementación del servidor gRPC que recibe las solicitudes.

**cliente.py**

Implementación del cliente que realiza la llamada RPC al servidor.

---

# Instalación

Se requiere **Python 3** y las siguientes dependencias:

```bash
pip install grpcio grpcio-tools flask
```

---

# Compilación del archivo proto

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. mensaje.proto
```

---

# Ejecución del sistema

## 1. Iniciar servidor

```bash
python server.py
```

Esto levanta:

* Servidor gRPC → `localhost:50051`
* Endpoint HTTP → `localhost:8000`

---

## 2. Ejecutar cliente

```bash
python cliente.py
```

---

# Ejecución de tests

Desde la raíz del proyecto:

```bash
python -m pytest -v tests/test_grpc.py
```

Importante:

* La carpeta `tests/` debe contener `__init__.py`

---

# Endpoint de estado (Health Check)

Se implementa un endpoint HTTP para monitorear el estado del sistema.

## URL

```
http://localhost:8000/health
```

## Ejemplo de respuesta

```json
{
  "grpc_server": "OK",
  "logs": "OK"
}
```

Este endpoint permite verificar rápidamente si los servicios principales están funcionando correctamente.

---

# Flujo de comunicación

1. El cliente crea un canal gRPC hacia el servidor.
2. Construye un `MensajeRequest`.
3. Invoca el método remoto `Saludo`.
4. El servidor procesa la solicitud.
5. Retorna un `MensajeResponse`.
6. El cliente recibe la respuesta.

---

# Comparación: JSON (Hit 5) vs gRPC/Protobuf (Hit 8)

| Característica    | JSON + TCP | gRPC + Protobuf |
| ----------------- | ---------- | --------------- |
| Formato de datos  | Texto      | Binario         |
| Serialización     | Manual     | Automática      |
| Tipado            | Dinámico   | Estricto        |
| Tamaño de mensaje | Mayor      | Menor           |
| Performance       | Menor      | Mayor           |

---

# Tamaño de los mensajes

JSON:

```
{"tipo":"saludo","mensaje":"hola!!!"}
```

≈ 38 bytes

Protobuf:

≈ 15–20 bytes

---

# Latencia de las llamadas

gRPC utiliza **HTTP/2**, lo que permite:

- multiplexación de conexiones
- mejor manejo de concurrencia
- menor overhead de comunicación

Esto generalmente resulta en **menor latencia** comparado con la comunicación basada en JSON sobre sockets TCP.

---

# Experiencia de desarrollo

## JSON + Sockets

Ventajas:

- implementación simple
- fácil de inspeccionar

Desventajas:

- más código manual
- mayor probabilidad de errores
- no existe verificación de tipos

---

## gRPC + Protocol Buffers

Ventajas:

- contrato de comunicación claro
- generación automática de código
- mayor eficiencia
- tipado fuerte

Desventajas:

- requiere definir archivos `.proto`
- necesita compilación previa

---

# Conclusión

La migración de **JSON sobre TCP** a **gRPC con Protocol Buffers** mejora significativamente la comunicación entre nodos en sistemas distribuidos.

Las principales mejoras son:

- reducción del tamaño de los mensajes
- menor latencia
- generación automática de código
- mejor mantenibilidad del sistema

Por estas razones, gRPC es una solución ampliamente utilizada en arquitecturas modernas de microservicios y sistemas distribuidos.


# Arquitectura del sistema

```mermaid
flowchart LR

A[Cliente gRPC\ncliente.py]
B[gRPC Channel\nHTTP/2]
C[Servidor gRPC\nserver.py]

A -->|MensajeRequest| B
B -->|RPC Saludo| C
C -->|MensajeResponse| B
B -->|Respuesta| A
