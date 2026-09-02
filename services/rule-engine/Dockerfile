FROM python:3.12-slim

WORKDIR /app

COPY services/rule-engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/rule-engine /app
COPY vault /app/vault

ENV VAULT_RUNS_DIR=/app/vault/runs
EXPOSE 8070
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8070"]
