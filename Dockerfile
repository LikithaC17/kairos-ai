FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY network-attack-forecasting/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY network-attack-forecasting/ ./network-attack-forecasting/

WORKDIR /app/network-attack-forecasting

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
