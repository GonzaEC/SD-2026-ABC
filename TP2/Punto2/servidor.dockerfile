FROM python:3.10-slim

WORKDIR /app

# Copiar código
COPY servidor.py .

# Instalar dependencias
RUN pip install fastapi uvicorn requests

# (IMPORTANTE) instalar cliente docker
RUN apt-get update && apt-get install -y docker.io

# Ejecutar servidor
CMD ["uvicorn", "servidor:app", "--host", "0.0.0.0", "--port", "7685"]