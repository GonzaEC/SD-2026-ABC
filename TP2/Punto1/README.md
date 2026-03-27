# Pasos para ejecutar el Punto 1
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
# 2. Seleccionar ubicacion del Punto 1
Abrir una terminal y ejecutar:
```bash
cd ./TP2/Punto1
```
---
# 3. Configurar contenedor docker

```bash
docker build -t servicio-tarea:1.0 -f servicio-tarea dockerfile .
```
---

# 4. Ejecutar el servidor

Abrir una terminal y ejecutar:

```bash
python servidor.py
```

Salida esperada:

```
INFO:     Started server process [132]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:7685 (Press CTRL+C to quit)
```

---

# 5. Ejecutar el cliente

En otra terminal ejecutar:

```bash
python cliente.py <tipo solicitud> <calculo> <parametros> <adicional> <imagen>
Ejemplo:
python cliente.py POST suma [2,3] [] servicio-tarea:1.0
```

Salida esperada cuando el servidor está activo:

```
2026-03-26 23:09:06,027 - INFO - Se esta procesando una nueva tarea mediante POST: {'calculo': 'suma', 'parametros': '[2,3]', 'adicional': '[]', 'imagen': 'servicio-tarea:1.0'}
INFO:     127.0.0.1:52556 - "POST /getRemoteTask HTTP/1.1" 200 OK
```

---
# Metodos disponibles

Para visualizar los metodos disponibles en docker ejecute el siguiente comando: 
python cliente.py METODOS servicio-tarea:1.0 

En el caso que se quiera borrar la imagen use el siguiente comando:
docker rm -f servicio-tarea
