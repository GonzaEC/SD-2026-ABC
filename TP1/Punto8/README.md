# TP1 - Sistemas Distribuidos  
## Hit 8 - Refactorización a gRPC / Protocol Buffers

## Descripción

En este punto del trabajo práctico se refactoriza la comunicación implementada previamente en el **Hit #5**, donde los nodos se comunicaban utilizando **sockets TCP y mensajes serializados en JSON**.

El objetivo del Hit #8 es reemplazar ese mecanismo por **gRPC utilizando Protocol Buffers**, lo que permite:

- Definir un **contrato de comunicación claro**
- Generar automáticamente el código de cliente y servidor
- Reducir el tamaño de los mensajes transmitidos
- Mejorar la eficiencia de la comunicación
- Simplificar el manejo de serialización de datos

En lugar de enviar mensajes JSON manualmente por sockets TCP, los nodos ahora se comunican mediante **Remote Procedure Calls (RPC)**.

---

# Tecnologías utilizadas

- Python 3
- gRPC
- Protocol Buffers

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
pip install grpcio grpcio-tools
```

Estas librerías permiten:

- ejecutar servidores y clientes gRPC
- compilar archivos `.proto` a código Python

---

# Compilación del archivo proto

El archivo `mensaje.proto` define el contrato de comunicación.

Para generar el código necesario ejecutar:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. mensaje.proto
```

Este comando genera automáticamente:

```
mensaje_pb2.py
mensaje_pb2_grpc.py
```

---

# Ejecución del sistema

## 1. Iniciar el servidor

Abrir una terminal y ejecutar:

```bash
python server.py
```

Salida esperada:

```
Servidor gRPC escuchando en puerto 50051
```

El servidor queda esperando solicitudes del cliente.

---

## 2. Ejecutar el cliente

En otra terminal ejecutar:

```bash
python cliente.py
```

Salida esperada:

```
Respuesta recibida del servidor:
Tipo: respuesta
Mensaje: Hola A (cliente), soy B (servidor)
```

En la consola del servidor se verá:

```
Mensaje recibido del cliente:
Tipo: saludo
Mensaje: hola!!!
```

Esto demuestra que la llamada RPC se ejecutó correctamente.

---

# Flujo de comunicación

El flujo de comunicación entre los nodos es el siguiente:

1. El cliente crea un canal gRPC hacia el servidor.
2. El cliente construye un mensaje `MensajeRequest`.
3. El cliente invoca el método remoto `Saludo`.
4. El servidor recibe el request.
5. El servidor procesa la solicitud.
6. El servidor envía un `MensajeResponse`.
7. El cliente recibe la respuesta.

---

# Comparación: JSON (Hit 5) vs gRPC/Protobuf (Hit 8)

## Implementación anterior (Hit 5)

En el Hit #5 la comunicación se realizaba utilizando:

- sockets TCP
- mensajes JSON
- serialización manual

Ejemplo de mensaje JSON:

```json
{
  "tipo": "saludo",
  "mensaje": "hola!!!"
}
```

El proceso era:

1. Serializar el objeto con `json.dumps`
2. Enviarlo por el socket
3. Recibir los datos
4. Deserializar con `json.loads`

---

## Implementación actual (Hit 8)

Con gRPC y Protocol Buffers:

- el contrato se define en un archivo `.proto`
- el compilador `protoc` genera automáticamente el código
- los mensajes se envían en **formato binario**

Ejemplo de mensaje en protobuf:

```
MensajeRequest {
  tipo = "saludo"
  mensaje = "hola!!!"
}
```

---

# Comparación técnica

| Característica | JSON + TCP | gRPC + Protobuf |
|---|---|---|
| Formato de datos | Texto | Binario |
| Serialización | Manual | Automática |
| Tipado | Dinámico | Estricto |
| Tamaño de mensaje | Mayor | Menor |
| Performance | Menor | Mayor |
| Código | Más manual | Generado automáticamente |

---

# Tamaño de los mensajes

Un mensaje JSON como:

```
{"tipo":"saludo","mensaje":"hola!!!"}
```

tiene aproximadamente **38 bytes**.

El mismo mensaje usando **Protocol Buffers** se codifica en formato binario y ocupa aproximadamente **15–20 bytes**, dependiendo de la codificación.

Esto reduce la cantidad de datos transmitidos por la red.

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