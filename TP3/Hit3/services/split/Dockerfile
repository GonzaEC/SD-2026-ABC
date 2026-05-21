FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pika pillow fastapi uvicorn python-multipart

COPY split.py .

CMD ["python", "split.py"]
