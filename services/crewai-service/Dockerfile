FROM python:3.12-slim

WORKDIR /app

COPY services/shared /app/shared
COPY services/crewai-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/crewai-service /app

ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
