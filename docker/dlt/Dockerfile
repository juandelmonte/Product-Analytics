# ---------------------------------------------------------------------------
# dlt ingestion image
#
# Installs only the Python dependencies; the pipeline code lives in `./dlt`
# and is mounted at /app at runtime. Pipelines are run on demand with:
#     docker compose run --rm dlt python -m pipelines.<name> ...
# ---------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

CMD ["python", "--version"]
