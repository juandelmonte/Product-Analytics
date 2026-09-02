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

## The 3 steps

### 1. Clone the project on the VPS

```bash
git clone <your-repo-url> projects/06_analytics_environment
cd projects/06_analytics_environment
```

### 2. Build and start everything

```bash
docker compose up --build -d
```

That's it. The stack **self-bootstraps**: the one-time `bootstrap` service runs
the full pipeline automatically on a cold start (empty volumes):

```
create ClickHouse DBs (bronze/staging/core/marts)
  → reset operational schema + generate 24 months of simulated history
  → dlt ingest into ClickHouse bronze
  → dbt build (staging → core → marts) + data tests
  → dbt docs generate (catalog for the docs site)
  → create the read-only Evidence user + grant
```

It then writes a completion marker to the `bootstrap-state` volume, so a later
`docker compose up` (reboot, redeploy) is a **no-op** — it does not wipe or
regenerate data. Airflow's scheduler + webserver, Evidence, **and the dbt docs
server** all **wait** for the bootstrap to finish
(`depends_on: service_completed_successfully`) before they start, so nothing
races an empty warehouse. Once started, the `dbt` service runs
`dbt docs serve` as a persistent server (it does **not** auto-run `dbt build`),
so the docs stay available on :8083 with no manual step.

Watch the initialisation:

```bash
docker compose logs -f bootstrap
```

### 3. Open the two ports on the firewall

```bash
# UFW example
sudo ufw allow 8083/tcp   # dbt docs
sudo ufw allow 3000/tcp   # Evidence
```

### 4. Verify from the VPS itself

```bash
# both should return HTTP 200 once the bootstrap has finished
curl -I http://localhost:8083     # dbt docs
curl -I http://localhost:3000     # Evidence
```

### 5. Access from the outside

- **dbt docs:** `http://<vps-ip>:8083`
- **Evidence:** `http://<vps-ip>:3000`

Add DNS later by pointing a record at the VPS IP (optionally in front of a
reverse proxy on 443).

## Daily refresh (automatic)

Airflow's `daily_pipeline` DAG runs on a daily schedule:
`advance simulation one day → incremental dlt ingest → dbt build → tests`.
Each task shells out to `docker compose run --rm` against the mounted docker
socket (the Airflow image bundles the Docker CLI + compose plugin). The
`historical_initialization` DAG (same chain but a full 720-day regen) is
available to trigger manually if you ever want to rebuild from scratch —
normally you only need the scheduler's daily run.

> The daily `dbt build` refreshes the marts **and** the shared `target/` on the
> `./dbt` bind mount; the long-running docs server picks up the regenerated
> `manifest.json`/`catalog.json` automatically. To refresh the docs catalog
> after a manual model change: `docker compose run --rm dbt docs generate`.

## Full reset (optional)

To wipe everything and re-bootstrap from scratch (new deterministic 720-day
history):

```bash
docker compose down -v
docker compose up --build -d
```

> The `bootstrap` marker lives on the `bootstrap-state` volume, so `down -v`
> clears it and the next `up` re-runs the whole chain.

## What stays internal

| Service | Purpose | Exposed? |
|---------|---------|----------|
| postgres | operational source-of-truth | no |
| api | source APIs + simulation | no |
| clickhouse | warehouse (bronze/staging/core/marts) | no |
| dlt | ingestion | no |
| dbt | transforms + **persistent docs server (:8083)** | yes — docs |
| airflow | daily orchestration (webserver + scheduler) | no |
| bootstrap | one-time initialisation (exits after success) | no |
| evidence | curated report | yes — :3000 |

All persistent services use `restart: unless-stopped`, so the stack survives a
VPS reboot and comes back up (bootstrap is a no-op once the marker exists).

Airflow's webserver is not exposed. To reach the UI, use an SSH tunnel:

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
