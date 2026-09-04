FROM python:3.12-slim

WORKDIR /app

COPY services/memory-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/memory-service /app

ENV MEMORY_STORAGE_PATH=/app/data/memory.jsonl
RUN mkdir -p /app/data

EXPOSE 8090
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
