SHELL := /bin/bash

.DEFAULT_GOAL := help

.PHONY: help build seed run test docs debug compile shell clickhouse up down ps logs \
        db-start db-shell api-up api-shell dlt-ingest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

# --- dbt / ClickHouse -----------------------------------------------------

build: ## Run the full dbt pipeline (models + tests, ordered automatically)
	docker compose run --rm dbt build

seed: ## Load seed data only
	docker compose run --rm dbt seed

run: ## Run models only
	docker compose run --rm dbt run

test: ## Run data tests only
	docker compose run --rm dbt test

compile: ## Compile models without executing
	docker compose run --rm dbt compile

docs: ## Generate docs and serve them at http://localhost:8080
	docker compose run --rm dbt docs generate
	docker compose run --rm --service-ports dbt docs serve --port 8080 --host 0.0.0.0

debug: ## Verify the dbt <-> ClickHouse connection
	docker compose run --rm dbt debug

shell: ## Open the ClickHouse client on the analytics database
	docker compose exec clickhouse clickhouse-client --database $${CLICKHOUSE_DB:-analytics}

# --- Operational DB / API -------------------------------------------------

db-start: ## Start PostgreSQL + ClickHouse in the background
	docker compose up -d postgres clickhouse

db-shell: ## Open psql on the operational database
	docker compose exec postgres psql -U $${POSTGRES_USER:-saas} -d $${POSTGRES_DB:-saas}

api-up: ## Start the source API (and its Postgres dependency)
	docker compose up -d api

api-shell: ## Open a shell in the api container
	docker compose run --rm api bash

# --- Ingestion -------------------------------------------------------------

dlt-ingest: ## Run the dlt ingestion pipeline (historical or incremental)
	docker compose run --rm dlt python -m pipelines.product_events

# --- Simulation -------------------------------------------------------------

sim-history: ## Generate 24 months of deterministic history
	docker compose run --rm api python -m app.sim history

sim-day: ## Advance the simulation by one day (append-only)
	docker compose run --rm api python -m app.sim day

sim-reset: ## Drop and recreate the operational schema
	docker compose run --rm api python -m app.sim reset

reset-environment: ## Full reset: stop, wipe volumes, rebuild, re-init
	docker compose down -v
	docker compose build
	docker compose up -d postgres clickhouse api
	docker compose run --rm api alembic upgrade head
	docker compose run --rm api python -m app.sim reset
	docker compose run --rm api python -m app.sim history --days 720
	docker compose run --rm dlt python -m pipelines.ingest
	docker compose run --rm dbt build
	docker compose exec -T clickhouse clickhouse-client --query "CREATE USER IF NOT EXISTS evidence IDENTIFIED WITH sha256_password BY 'evidence'; GRANT SELECT ON marts.* TO evidence"

backfill: ## Re-ingest from a watermark and rebuild (corrects late data)
	docker compose run --rm dlt python -m pipelines.ingest --incremental
	docker compose run --rm dbt build --full-refresh

# --- Orchestration ---------------------------------------------------------

airflow-init: ## Initialise the Airflow metadata database
	docker compose --profile orchestration run --rm airflow-init

airflow-up: ## Start Airflow scheduler + webserver
	docker compose --profile orchestration up -d airflow-scheduler airflow-webserver

airflow-down: ## Stop Airflow services
	docker compose --profile orchestration down

bi-up: ## Start the Evidence business report (http://localhost:3000)
	docker compose up -d evidence

# --- Stack -----------------------------------------------------------------

up: ## Start the full stack in the background
	docker compose build
	docker compose up -d

down: ## Stop and remove containers
	docker compose down

ps: ## List containers for this stack
	docker compose ps

logs: ## Tail logs
	docker compose logs -f
