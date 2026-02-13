FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite fallback (only used if DATABASE_URL is not set)
RUN mkdir -p /data /data/backups
ENV ETSAI_DB=/data/etsai.db
ENV ETSAI_BACKUP_DIR=/data/backups
ENV FLASK_DEBUG=0

EXPOSE ${PORT:-8000}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --preload
