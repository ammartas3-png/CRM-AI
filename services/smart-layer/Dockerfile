FROM python:3.12-slim
WORKDIR /app
COPY services/smart-layer/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/smart-layer /app
COPY vault /app/vault
ENV VAULT_DIR=/app/vault
EXPOSE 8060
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8060"]
