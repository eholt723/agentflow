# Stage 1: Build React UI
FROM node:20-slim AS ui-builder
WORKDIR /ui
COPY ui/package*.json ./
RUN npm ci
COPY ui/ .
RUN npm run build

# Stage 2: Python API
FROM python:3.12-slim
WORKDIR /app

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY --from=ui-builder /ui/dist ./ui/dist

EXPOSE 8000

# PORT is set by Render at runtime; falls back to 8000 locally
CMD ["sh", "-c", "uvicorn api.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
