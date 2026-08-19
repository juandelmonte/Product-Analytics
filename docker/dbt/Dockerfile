# ---------------------------------------------------------------------------
# dbt + ClickHouse adapter image
#
# Builds from a Python base and installs `dbt-core` + `dbt-clickhouse` via pip.
# dbt-core is pinned explicitly because the ClickHouse adapter supports up to
# dbt-core 1.10.
#
#   build arg DBT_CLICKHOUSE_VERSION -> dbt-clickhouse version (default 1.10.2)
#   build arg DBT_CORE_VERSION       -> dbt-core version       (default 1.10.23)
# ---------------------------------------------------------------------------
FROM python:3.12-slim

ARG DBT_CLICKHOUSE_VERSION=1.10.2
ARG DBT_CORE_VERSION=1.10.23

# Install dbt-core and the ClickHouse adapter. Keep the build lean: no venv
# needed because this container is single-purpose (run dbt against ClickHouse).
# git is required by `dbt debug` (and `dbt deps` for git packages).
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
        "dbt-core==${DBT_CORE_VERSION}" \
        "dbt-clickhouse==${DBT_CLICKHOUSE_VERSION}"

WORKDIR /app

ENTRYPOINT ["dbt"]
CMD ["--version"]
