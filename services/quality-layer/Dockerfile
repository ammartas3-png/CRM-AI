FROM python:3.12-slim
WORKDIR /app
COPY services/quality-layer/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/quality-layer /app
COPY evals /app/evals
ENV QUALITY_DATA_DIR=/app/data
RUN mkdir -p /app/data/review_queue
EXPOSE 8050
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8050"]
