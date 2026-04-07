
# Imagen base
FROM python:3.10-slim

# Directorio de trabajo
WORKDIR /app

# Copiar código
COPY servicio.py .

# Instalar dependencias
RUN pip install fastapi uvicorn

# Ejecutar servidor
CMD ["uvicorn", "servicio:app", "--host", "0.0.0.0", "--port", "8132"]