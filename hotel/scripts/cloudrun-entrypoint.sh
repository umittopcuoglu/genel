#!/bin/sh
set -e
cd /app
echo "=== Container starting at $(date -u) ==="
echo "Python: $(python --version 2>&1)"
echo "PORT=${PORT:-8080}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1 --timeout-keep-alive 30
