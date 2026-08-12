FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Use $PORT from environment (Render, Railway, etc.)
ENV PORT=8000
EXPOSE $PORT
# TASK-018: Run Alembic migrations before starting the server.
# Verify the deployed database revision and required columns, then start only on success.
# This is idempotent — already-applied revisions are skipped.
CMD ["sh", "-c", "alembic upgrade head && python -m app.core.migration_verify && exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\"\"]
