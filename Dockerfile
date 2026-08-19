# ---------- Stage 1: build frontend ----------
FROM node:20-alpine AS web-build

WORKDIR /build/web

COPY web/package*.json ./
RUN npm install

COPY web/ ./
RUN npm run build

# ---------- Stage 2: runtime (nginx + fastapi) ----------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Backend source
WORKDIR /app/api
COPY api/ /app/api/

# Python deps
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Ensure DB mount target exists, with permissive mode to reduce host UID/GID surprises
RUN mkdir -p /app/api/data \
    && touch /app/api/data/app.db \
    && chmod 666 /app/api/data/app.db || true

# Frontend build output served by nginx
COPY --from=web-build /build/web/dist/ /usr/share/nginx/html/

# nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 5173
EXPOSE 8000

# Run FastAPI privately on localhost:18000, nginx is the only public entrypoint
CMD ["sh", "-c", "uvicorn main:app --host 127.0.0.1 --port 18000 & exec nginx -g 'daemon off;'"]
