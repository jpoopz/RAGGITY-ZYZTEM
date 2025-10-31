FROM python:3.12-slim

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Preinstall requirements (layered for faster rebuilds)
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && pip install uvicorn[standard] fastapi chromadb faiss-cpu psutil python-multipart

ENV PYTHONUNBUFFERED=1

# Devcontainers keep container running; compose overrides command to run uvicorn
CMD ["sleep", "infinity"]


