# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System updates (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Cloud Run provides PORT; default to 8080 for local runs
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Start a web server that listens on 0.0.0.0:$PORT
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT}
