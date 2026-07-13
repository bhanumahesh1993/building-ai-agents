# Dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y \
    wget unzip && \
    wget -q https://releases.hashicorp.com/\
terraform/1.9.8/terraform_1.9.8_linux_amd64.zip \
    -O /tmp/tf.zip && \
    unzip /tmp/tf.zip -d /usr/local/bin && \
    rm /tmp/tf.zip && \
    apt-get remove -y wget unzip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY crew ./crew

EXPOSE 8000
CMD ["uvicorn", "crew.app:app", \
     "--host", "0.0.0.0", "--port", "8000"]
