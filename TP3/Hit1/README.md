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
Tener instalado **k3d**.

Verificar instalación:

```bash
k3d --version
```
Tener instalado **kubectl**.

Verificar instalación:

```bash
kubectl --version
```
Instalar dependencias:

```bash
cd ./TP3
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
# 3. Construir imagen del worker
```bash
docker build -t grupoABC/sobel-worker:latest .
```
---
# 4. Aplicar archivos de rabbitMQ y de los workers

```bash
kubectl apply -f rabbitmq.yaml -f workers.yaml
```
---

# 5. Exponer puerto de rabbitMQ


```bash
kubectl port-forward svc/rabbitmq 5672:5672
```
# 6. Ejecutar el Proceso Principal


```bash
python ProcesoPrincipal.py FondoCristiano.jpg prueba.jpg
```