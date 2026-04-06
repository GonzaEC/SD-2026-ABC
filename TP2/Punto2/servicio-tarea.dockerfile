
#El dockerfile es un archivo que le dice a Docker: "cómo construir una imagen"

# Imagen base
FROM python:3.10-slim

# Directorio de trabajo
WORKDIR /app

# Copiar código
COPY docker.py .

# Instalar dependencias
RUN pip install fastapi uvicorn

# Ejecutar servidor
CMD ["uvicorn", "docker:app", "--host", "0.0.0.0", "--port", "8132"]