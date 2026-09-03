# ---------------------------------------------------------------------------
# Evidence (reporting) image
#
# Self-hosted Evidence serving the curated business report over the dbt marts
# in ClickHouse. The SQL lives in `evidence/queries/` as plain ClickHouse SQL.
# ---------------------------------------------------------------------------
FROM evidencedev/serve:latest

COPY --chown=evidence:evidence . /project
