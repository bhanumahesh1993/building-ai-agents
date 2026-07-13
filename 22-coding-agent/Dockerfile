# Dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y \
    git docker.io && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY agent ./agent

EXPOSE 8000
CMD ["uvicorn", "agent.app:app", \
     "--host", "0.0.0.0", "--port", "8000"]
