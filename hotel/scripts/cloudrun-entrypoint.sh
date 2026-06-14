#!/bin/bash
set -e
cd /app
echo "=== Initializing database tables ==="
python init_db.py
echo "=== Seeding demo data ==="
python seed.py
echo "=== Starting uvicorn ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 2
