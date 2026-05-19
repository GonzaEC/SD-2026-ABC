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
# 2. Seleccionar ubicacion del Hit 2
Abrir una terminal y ejecutar:
```bash
cd ./TP3/Hit2
```
---
# 3. Aplicar archivo de rabbitMQ 

```bash
kubectl apply -f rabbitmq.yaml
```
---

# 4. Exponer puerto de rabbitMQ

```bash
kubectl port-forward svc/rabbitmq 5672:5672
```
# 5. Ejecutar Proceso Principal 
```bash
python ProcesoPrincipal.py <PATH_IMAGEN> <PATH_OUTPUT>

```
(nota: el path se recomienda que este completo)
---