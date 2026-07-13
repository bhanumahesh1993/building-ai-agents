# Dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY catalog_server.py .
COPY shopping ./shopping

EXPOSE 8000
CMD ["uvicorn", "shopping.app:app", \
     "--host", "0.0.0.0", "--port", "8000"]
