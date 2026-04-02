FROM python:3.11
WORKDIR /app
COPY servidor.py .
COPY requirements.txt .
RUN apt-get update && apt-get install -y docker.io
RUN pip install -r requirements.txt
CMD ["uvicorn", "servidor:app", "--host", "0.0.0.0", "--port", "7685"]