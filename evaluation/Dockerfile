FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir prometheus-client

COPY evaluation /app/evaluation

ENV PYTHONPATH=/app

EXPOSE 9108

CMD ["python", "-m", "evaluation.metrics.exporter"]
