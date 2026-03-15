# SD-2026-ABC - Punto 6
Para el siguiente ejercicio se deben utilizar los siguientes comandos:
Para ejecutar comandos primero debe ir a la ubicacion de los archivos mediante:
cd TP1/Punto6
Luego, Para iniciar el nodo D:
python -m uvicorn nodoD:app --host 127.0.0.1 --port 1234 
Finalmente para ejecutar el nodo C se debe escribir para cada instancia el siguiente comando que incluye la direccion del nodo D: 
python nodoC.py 127.0.0.1 1234