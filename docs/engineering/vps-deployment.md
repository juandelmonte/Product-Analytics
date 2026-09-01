# VPS Deployment

Deploy the **whole project** on your VPS. Only **dbt docs** and **Evidence** are
exposed to the internet; everything else stays on the internal Docker network.

## Ports

Only two host ports are exposed (the only ones to open in the firewall):

| Service | Host port | Container port | Notes |
|---------|-----------|----------------|-------|
| **dbt docs** | **8083** | 8080 | renumbered from 8080 (taken on the reference VPS) |
| **Evidence** | **3000** | 3000 | unchanged (free on the reference VPS) |

Everything else (postgres, api, clickhouse, dlt, airflow) has **no host port** —
it is reachable only inside the Docker network by container name. This removes
most port-collision risk on a shared VPS.

> Changing a host port later is a host-side-only edit in `docker-compose.yml`
> (e.g. `"8083:8080"` → `"9083:8080"`). No code changes are needed: all
> inter-service links use container hostnames + container-side ports.

## The 4 steps

### 1. Clone the project on the VPS

```bash
git clone <your-repo-url> projects/06_analytics_environment
cd projects/06_analytics_environment
```

### 2. Build and start everything

```bash
docker compose up --build -d
```

This starts the full stack: postgres → api → clickhouse → dbt → dlt → evidence,
plus Airflow (scheduler + webserver + its postgres).

**First-time only — initialise the data:**

```bash
# apply the operational schema + generate 24 months of history
docker compose exec clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS bronze; CREATE DATABASE IF NOT EXISTS staging; CREATE DATABASE IF NOT EXISTS core; CREATE DATABASE IF NOT EXISTS marts"
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.sim history --days 720
docker compose run --rm dlt python -m pipelines.ingest
docker compose run --rm dbt build

# create the read-only Evidence ClickHouse user
docker compose exec -T clickhouse clickhouse-client --query "CREATE USER IF NOT EXISTS evidence IDENTIFIED WITH sha256_password BY 'evidence'; GRANT SELECT ON marts.* TO evidence"
```

> This is the same `reset-env` flow as locally — run `make reset-environment` if
> you prefer.

**Airflow first-time init:**

```bash
docker compose run --rm airflow-init
```

Then trigger the `historical_initialization` DAG once from the Airflow UI (or
CLI). After that, `daily_pipeline` runs on a daily schedule: advance simulation →
incremental dlt ingest → dbt build → tests.

### 3. Open the two ports on the firewall

```bash
# UFW example
sudo ufw allow 8083/tcp   # dbt docs
sudo ufw allow 3000/tcp   # Evidence
```

### 4. Access from the outside

- **dbt docs:** `http://<vps-ip>:8083`
- **Evidence:** `http://<vps-ip>:3000`

Add DNS later by pointing a record at the VPS IP (optionally in front of a
reverse proxy on 443).

## What stays internal

| Service | Purpose | Exposed? |
|---------|---------|----------|
| postgres | operational source-of-truth | no |
| api | source APIs + simulation | no |
| clickhouse | warehouse (bronze/staging/core/marts) | no |
| dlt | ingestion | no |
| airflow | daily orchestration (webserver + scheduler) | no |

Airflow's webserver is not exposed. To reach it for the one-time historical
trigger, use an SSH tunnel:

```bash
ssh -L 8081:localhost:8081 juan@<vps-ip>
# then http://localhost:8081
```

(Or temporarily add a port mapping if you prefer direct access.)

## Security note

Evidence runs with `EVIDENCE_AUTH_DISABLED: "true"` by default (matching local
dev). Before exposing it to the internet for real, set
`EVIDENCE_BASIC_USER` / `EVIDENCE_BASIC_PASSWORD` and flip
`EVIDENCE_AUTH_DISABLED` to `"false"` — or front Evidence with an authenticating
reverse proxy.
