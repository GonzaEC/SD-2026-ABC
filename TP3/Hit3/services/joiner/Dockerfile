FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pika pillow fastapi uvicorn redis

COPY joiner.py .

CMD ["python", "joiner.py"]
