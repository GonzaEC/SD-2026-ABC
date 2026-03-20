# INFORME TP 1

Este trabajo práctico tiene como objetivo el desarrollo progresivo de un sistema distribuido, incorporando conceptos fundamentales como:

- Comunicación cliente-servidor  
- Procesamiento asincrónico  
- Descubrimiento de nodos  
- Serialización de datos  

A lo largo de los distintos HITs se construyeron múltiples componentes (nodos A, B, C y D), evolucionando desde una comunicación TCP básica hasta una arquitectura distribuida con registro de nodos, ventanas de inscripción y comunicación mediante gRPC.

---

## Uso de IA

Se utilizó ChatGPT para:

- Consultas conceptuales  
- Comprender las consignas de cada HIT  
- Resolver dudas puntuales  

En algunos casos, también se utilizó para generar código base cuando surgían problemas o al trabajar con librerías desconocidas.

El uso de IA resultó beneficioso, ya que permitió una mejor comprensión de los temas y del código a desarrollar.

---

## Arquitectura del sistema

### Componentes

- **Nodo A (cliente):** Inicia la comunicación enviando mensajes.  
- **Nodo B (servidor):** Escucha conexiones y responde.  
- **Nodo C (nodo híbrido):** Actúa como cliente y servidor simultáneamente.  
- **Nodo D (registro de contactos):** Centraliza la información de nodos activos y coordina ventanas de inscripción.  

---

## Estructura del proyecto

```bash
.gitignore
README.md
TP1/
│
├── informe.txt
├── requirements.txt
│
├── Punto1/
│   ├── cliente.py
│   ├── servidor.py
│   ├── README.md
│   ├── logs/
│   └── tests/
│
├── Punto2/
│   ├── cliente.py
│   ├── servidor.py
│   ├── README.md
│   ├── logs/
│   └── tests/
│
├── Punto3/
│   ├── cliente.py
│   ├── servidor.py
│   ├── README.md
│   ├── logs/
│   └── tests/
│
├── Punto4/
│   ├── nodo.py
│   ├── README.md
│   ├── logs/
│   └── tests/
│
├── Punto5/
│   ├── nodo.py
│   ├── README.md
│   ├── logs/
│   └── tests/
│
├── Punto6/
│   ├── nodoC.py
│   ├── nodoD.py
│   ├── README.md
│   ├── logs/
│   └── tests/
│
├── Punto7/
│   ├── nodoC.py
│   ├── nodoD.py
│   ├── registro_nodos.json
│   ├── README.md
│   ├── logs/
│   └── tests/
│
└── Punto8/
    ├── cliente.py
    ├── server.py
    ├── mensaje.proto
    ├── mensaje_pb2.py
    ├── mensaje_pb2_grpc.py
    ├── README.md
    ├── logs/
    └── tests/