FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn redis httpx python-multipart

COPY backend.py .

CMD ["python", "backend.py"]
