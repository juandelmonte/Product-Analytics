# ---------------------------------------------------------------------------
# Airflow image with Docker CLI + Compose plugin.
#
# Airflow DAGs orchestrate the pipeline by shelling out to `docker compose exec`
# against the host Docker daemon (via the mounted socket). The Docker CLI and the
# compose plugin are installed so BashOperator can run `docker compose`.
# ---------------------------------------------------------------------------
FROM apache/airflow:2.9.3

USER root

ARG DOCKER_VERSION=24.0.9
ARG COMPOSE_VERSION=2.24.6

# Docker CLI (static binary) + docker compose plugin (static binary).
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" \
        | tar -xz --strip-components=1 -C /usr/local/bin docker/docker \
    && chmod +x /usr/local/bin/docker \
    && mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && chown -R airflow:root /opt/airflow

USER airflow

ENV DOCKER_HOST=unix:///var/run/docker.sock
