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
# 3. Ingresar con usuario docker solo lectura
```bash
docker login -u ianott
```
---
Luego ingresar el token:
```bash
(solicitar token no pudo ser subido)
```
---
# 4. Descargar la imagen de servicio-tarea del repositorio privado

```bash
docker pull ianott/servicio-tarea
```
---
# 5. Configurar contenedor docker del servidor

```bash
docker build -t servidor:1.0 -f servidor.dockerfile .
```
---

# 6. Crear Red para comunicar contenedores


```bash
docker network create red_docker
```

# 7. Ejecutar el servidor


```bash
docker run --network red_docker -v /var/run/docker.sock:/var/run/docker.sock -d -i --name servidor -p 7685:7685 servidor:1.0
```

Salida esperada:

```
INFO:     Started server process [132]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:7685 (Press CTRL+C to quit)
```

---

# 8. Ejecutar el cliente

En otra terminal ejecutar:

```bash
python cliente.py <tipo solicitud> <calculo> <parametros> <adicional> <imagen>

Ejemplo:
python cliente.py POST suma [2,3] [] ianott/servicio-tarea

```

Salida esperada cuando el servidor está activo:

```
2026-03-26 23:09:06,027 - INFO - Se esta procesando una nueva tarea mediante POST: {'calculo': 'suma', 'parametros': '[2,3]', 'adicional': '[]', 'imagen': 'ianott/servicio-tarea'}
INFO:     127.0.0.1:52556 - "POST /getRemoteTask HTTP/1.1" 200 OK
```
Nota: en adicional la primera posicion de la lista se refiere al redondeo de los numeros por lo que si su valor es mayor a cero se redondeara el resultado a esa cantidad de decimales. 
Ademas, la segunda posicion de la lista refiere a valor absoluto que puede ser True o False y en caso que sea True el resultado sera devuelto con valor absoluto. (si no lo quiere usar con ingresar una lista vacia alcanza)
---
# Metodos disponibles

Para visualizar los metodos disponibles en docker ejecute el siguiente comando: 
python cliente.py METODOS ianott/servicio-tarea 

En el caso que se quiera borrar la imagen del servidor use el siguiente comando:
docker rm -f servidor
o en todo caso primero detenga el contenedor:
docker stop servidor
Y luego eliminelo:
docker rm servidor


