# Pasos para ejecutar el Hit 1
## 1. Requisitos

Tener instalado **Python 3**.

Verificar instalación:

```bash
python --version
```
Tener instalado **Docker**.

Verificar instalación:

```bash
docker --version
```
Instalar dependencias:

```bash
cd ./TP2
```

```
pip install -r requirements.txt
```
---
# 2. Seleccionar ubicacion del Hit 1
Abrir una terminal y ejecutar:
```bash
cd ./TP3/Hit1
```
---
# 3. Iniciar rabbitmq
```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
---
# 4. Configurar contenedor docker de los workers

```bash
docker compose build --no-cache 
```
---

# 5. Iniciar workers


```bash
docker compose up
```

# 6. Ejecutar el Proceso Principal


```bash
python ProcesoPrincipal.py FondoCristiano.jpg prueba.jpg
```