#!/usr/bin/env bash
# ===========================================================================
# One-time platform bootstrap — runs the FULL pipeline from an empty state.
#
#   operational schema (sim reset = create_all from models) -> 24 months of
#   simulated history (sim) -> dlt ingest into ClickHouse bronze -> dbt build
#   (staging/core/marts) + tests -> Evidence read-only user + grant.
#
# Invoked by the `bootstrap` compose service (docker-compose.yml) on a cold
# `docker compose up --build`, with the repo mounted at /workspace and the
# host docker socket at /var/run/docker.sock. It can also be run by hand from
# a host shell (make reset-environment) — the compose invocation below is
# explicit so it works from any directory / inside any container.
#
# Idempotency:
#   - sim history: skipped if sim_state already exists in Postgres.
#   - dlt ingest:  merge/append dispositions make re-runs safe.
#   - dbt build:   safe to re-run (incremental).
#   - ClickHouse DDL: all IF NOT EXISTS.
# The compose `bootstrap` service additionally gates the whole script behind a
# marker file, so a completed bootstrap is a no-op on subsequent `up`s.
# ===========================================================================
set -euo pipefail

# The compose project + file are explicit so this works whether run inside the
# bootstrap/airflow container (repo at /workspace) or from the host repo root.
COMPOSE_PROJECT="${COMPOSE_PROJECT_NAME:-saas-analytics}"
COMPOSE_FILE="/workspace/docker-compose.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
  # Fallback: running from a host checkout (repo root is the compose dir).
  COMPOSE_FILE="$(pwd)/docker-compose.yml"
fi
DC=(docker compose --project-name "$COMPOSE_PROJECT" -f "$COMPOSE_FILE")

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die()  { echo "FATAL: $*" >&2; exit 1; }

# clickhouse-admin-query: run DDL against the ClickHouse server container.
chq() { "${DC[@]}" exec -T clickhouse clickhouse-client --query "$1"; }

# --- Wait for long-running dependencies ------------------------------------
log "Waiting for ClickHouse to accept queries..."
for i in $(seq 1 90); do
  if chq "SELECT 1" >/dev/null 2>&1; then break; fi
  [ "$i" -eq 90 ] && die "ClickHouse not reachable after ~3 min"
  sleep 2
done

log "Waiting for the source API to be ready (http://api:8000/health)..."
for i in $(seq 1 90); do
  # python is available in the airflow/bootstrap image; the API is on the
  # internal compose network reachable as http://api:8000 from this container.
  if python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://api:8000/health', timeout=2).status==200 else 1)" 2>/dev/null; then
    break
  fi
  [ "$i" -eq 90 ] && die "API not reachable after ~3 min"
  sleep 2
done

# --- 1+2. Operational schema + 24 months of deterministic history -----------
# The SQLAlchemy models are the source of truth for the schema. `sim reset`
# drops + recreates from Base.metadata (create_all) — the validated path the
# project's reset flow uses (alembic's surrogate-id migrations are incomplete:
# they add `id` without a backing sequence, which breaks inserts).
#
# Idempotency: if sim_state already exists the operational DB is already
# initialised, so we skip the destructive reset+regen (a completed bootstrap is
# a no-op). A re-run after a PARTIAL failure (no marker yet) resets and
# regenerates deterministically — the desired recovery for a cold start.
# --no-deps: never touch already-running sibling containers (avoids the
# recreate cascade that broke an earlier bootstrap attempt).
log "Checking simulation state..."
SIM_STATE=$("${DC[@]}" exec -T api python -c \
  "from app.db import SessionLocal; from app.models import SimState; print(1 if SessionLocal().get(SimState,1) else 0)" 2>/dev/null || echo 0)

if [ "$SIM_STATE" = "1" ]; then
  echo "Operational schema + simulation already initialised — skipping (idempotent)."
else
  log "Resetting operational schema (sim reset = create_all from models)..."
  "${DC[@]}" run --rm --no-deps api python -m app.sim reset
  log "Generating ${SIM_HISTORY_DAYS:-720} days of simulated history (seed=${SEED:-42})..."
  "${DC[@]}" run --rm --no-deps api python -m app.sim history --days "${SIM_HISTORY_DAYS:-720}"
fi

# --- 3. ClickHouse analytical databases --------------------------------------
# dbt-clickhouse does NOT auto-create databases — create them up front.
log "Creating ClickHouse databases (bronze/staging/core/marts)..."
chq "CREATE DATABASE IF NOT EXISTS bronze; CREATE DATABASE IF NOT EXISTS staging; CREATE DATABASE IF NOT EXISTS core; CREATE DATABASE IF NOT EXISTS marts"

# --- 4. Ingest into ClickHouse bronze (dlt) ----------------------------------
log "Ingesting source data into ClickHouse bronze (dlt)..."
"${DC[@]}" run --rm --no-deps dlt python -m pipelines.ingest

# --- 5. Transform + test (dbt) -----------------------------------------------
log "Running dbt build (staging -> core -> marts + tests)..."
"${DC[@]}" run --rm --no-deps dbt build

# Generate the docs catalog so the `dbt` service can serve docs (port 8083)
# immediately after bootstrap, without needing a manual `dbt docs generate`.
log "Generating dbt docs catalog..."
"${DC[@]}" run --rm --no-deps dbt docs generate

# --- 6. Evidence read-only user + grant --------------------------------------
log "Creating Evidence read-only ClickHouse user + grant..."
chq "CREATE USER IF NOT EXISTS evidence IDENTIFIED WITH sha256_password BY '${EVIDENCE_CLICKHOUSE_PASSWORD:-evidence}'; GRANT SELECT ON marts.* TO evidence"

log "Bootstrap complete. Evidence report: http://localhost:3000"
