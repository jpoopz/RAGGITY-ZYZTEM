FROM python:3.12-slim

WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip &&     pip install -r /tmp/requirements.txt &&     pip install uvicorn fastapi chromadb faiss-cpu psutil python-multipart loguru

COPY . .

# run from repo root; rag_api.py is at /workspace
WORKDIR /workspace
CMD ["uvicorn", "rag_api:app", "--host", "0.0.0.0", "--port", "8000"]
