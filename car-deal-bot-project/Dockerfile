FROM python:3.12-slim

WORKDIR /app

# System dependencies for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persist the SQLite dedup DB across container restarts by mounting a volume
# at /data and setting DEDUPE_DB_PATH=/data/seen_listings.db via environment
# or by editing config.py.
VOLUME ["/data"]

# By default: one scan per container run. Use a scheduler (cron/systemd/
# GitHub Actions/Railway cron/etc.) to invoke it on an interval.
CMD ["python", "main.py"]
