FROM python:3.12-slim

WORKDIR /app

# Install dependencies as a separate layer so rebuilds are fast
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/

EXPOSE 8000

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
