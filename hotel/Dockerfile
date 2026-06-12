# === Stage 1: Build Frontend ===
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY frontend/ .

ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# === Stage 2: Python Backend ===
FROM python:3.11-slim AS runtime

RUN groupadd -r hotelops && useradd -r -g hotelops -d /app -s /sbin/nologin hotelops

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Copy frontend standalone build into /app/frontend_static for optional static serving
COPY --from=frontend-builder /frontend/.next/standalone /app/frontend/
COPY --from=frontend-builder /frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /frontend/public /app/frontend/public

RUN chown -R hotelops:hotelops /app

USER hotelops

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
