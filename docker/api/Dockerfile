# ---------------------------------------------------------------------------
# FastAPI source-API image
#
# Installs only the Python dependencies; the application code lives in `./api`
# and is mounted at /app at runtime (same pattern as the dbt service).
# ---------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
