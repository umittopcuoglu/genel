#!/usr/bin/env bash
set -euo pipefail

# Blue-green deployment
# Usage: ./deploy.sh <blue|green> <image-tag>

SLOT="${1:-green}"
TAG="${2:-latest}"
HEALTH_URL="http://127.0.0.1:800$([ "$SLOT" = "blue" ] && echo 1 || echo 2)/api/v1/health"

echo "Deploying to $SLOT slot with tag $TAG..."
docker compose -f docker-compose.yml up -d "$SLOT" --build

echo "Waiting for health check..."
for i in {1..30}; do
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "[$SLOT] healthy after ${i}s"
        break
    fi
    sleep 1
done

if ! curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "[$SLOT] failed health check — rolling back"
    docker compose stop "$SLOT"
    exit 1
fi

echo "Switching nginx upstream to $SLOT..."
PORT=$([ "$SLOT" = "blue" ] && echo 8001 || echo 8002)
sed -i "s|upstream active.*|upstream active { server 127.0.0.1:$PORT; }|" /etc/nginx/conf.d/hotel.conf
nginx -s reload

echo "Deploy complete: $SLOT is now active"
