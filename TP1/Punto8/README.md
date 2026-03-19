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

# 🧪 Ejecución de tests

Desde la raíz del proyecto:

```bash
python -m unittest discover -s tests -t . -v
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
