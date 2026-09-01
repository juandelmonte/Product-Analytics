# ===========================================================================
# Project-scoped shortcuts for the SaaS Product Analytics Platform.
#
# These functions live INSIDE this project (not in your PowerShell profile),
# so nothing leaks to other projects.
#
#   Load in any terminal:   . .\scripts\activate.ps1
#   VS Code auto-loads them via .vscode/settings.json in this workspace.
# ===========================================================================

# Project root = parent of the folder that contains this script.
$script:AnalyticsRoot = Split-Path -Parent $PSScriptRoot

# ClickHouse connection settings (mirrors .env defaults; used by ch / chq).
$script:ClickHouseUser = if ($env:CLICKHOUSE_USER) { $env:CLICKHOUSE_USER } else { 'default' }
$script:ClickHouseDb   = if ($env:CLICKHOUSE_DB) { $env:CLICKHOUSE_DB } else { 'analytics' }

# dbt -> run any dbt command inside the container (dbt only exists in Docker)
function dbt {
    Push-Location $script:AnalyticsRoot
    try { docker compose run --rm dbt @args }
    finally { Pop-Location }
}

# ch -> open the ClickHouse client inside the running server container
function ch {
    Push-Location $script:AnalyticsRoot
    try { docker compose exec clickhouse clickhouse-client --database $script:ClickHouseDb @args }
    finally { Pop-Location }
}

# chq -> run one SQL query against ClickHouse and print the result
function chq($query) {
    Push-Location $script:AnalyticsRoot
    try { docker compose exec clickhouse clickhouse-client --database $script:ClickHouseDb --query $query @args }
    finally { Pop-Location }
}

# dbt-docs -> regenerate docs and serve them at http://localhost:8083
function dbt-docs {
    Push-Location $script:AnalyticsRoot
    try {
        docker compose run --rm dbt docs generate
        docker compose run --rm --service-ports dbt docs serve --port 8080 --host 0.0.0.0
    }
    finally { Pop-Location }
}

# db-up -> start PostgreSQL + ClickHouse in the background
function db-up {
    Push-Location $script:AnalyticsRoot
    try { docker compose up -d postgres clickhouse }
    finally { Pop-Location }
}

# psql -> open psql on the operational database
function psql {
    Push-Location $script:AnalyticsRoot
    try {
        $user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { 'saas' }
        $db   = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { 'saas' }
        docker compose exec postgres psql -U $user -d $db @args
    }
    finally { Pop-Location }
}

# api-up -> start the source API (and its Postgres dependency)
function api-up {
    Push-Location $script:AnalyticsRoot
    try { docker compose up -d api }
    finally { Pop-Location }
}

# sim -> run a simulation command inside the api container
function sim($command, $days) {
    Push-Location $script:AnalyticsRoot
    try {
        if ($command -eq 'history') {
            docker compose run --rm api python -m app.sim history --days $days
        }
        else {
            docker compose run --rm api python -m app.sim $command
        }
    }
    finally { Pop-Location }
}

# airflow-up -> start the Airflow scheduler + webserver (runs with `up` by default)
function airflow-up {
    Push-Location $script:AnalyticsRoot
    try { docker compose up -d airflow-scheduler airflow-webserver }
    finally { Pop-Location }
}

# bi-up -> start the Evidence business report (http://localhost:3000)
function bi-up {
    Push-Location $script:AnalyticsRoot
    try { docker compose up -d evidence }
    finally { Pop-Location }
}

# reset-env -> full reset: wipe volumes, rebuild, re-init the pipeline
function reset-env {
    Push-Location $script:AnalyticsRoot
    try {
        docker compose down -v
        docker compose build
        docker compose up -d postgres clickhouse api
        docker compose run --rm api alembic upgrade head
        docker compose run --rm api python -m app.sim reset
        docker compose run --rm api python -m app.sim history --days 720
        docker compose run --rm dlt python -m pipelines.ingest
        docker compose run --rm dbt build
        docker compose exec -T clickhouse clickhouse-client --query "CREATE USER IF NOT EXISTS evidence IDENTIFIED WITH sha256_password BY 'evidence'; GRANT SELECT ON marts.* TO evidence"
    }
    finally { Pop-Location }
}

Write-Host "Analytics shortcuts loaded: dbt, ch, chq, dbt-docs, db-up, psql, api-up, sim, airflow-up, bi-up, reset-env" -ForegroundColor Green
