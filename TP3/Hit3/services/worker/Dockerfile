FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pika pillow fastapi uvicorn prometheus-client

COPY sobel.py worker.py ./

CMD ["python", "worker.py"]
