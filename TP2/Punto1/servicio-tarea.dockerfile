FROM python:3.11
WORKDIR /app
COPY docker.py .
RUN pip install fastapi uvicorn
CMD ["uvicorn", "docker:app", "--host", "0.0.0.0", "--port", "8132"]