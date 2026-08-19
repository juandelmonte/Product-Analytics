# ---------------------------------------------------------------------------
# Evidence (reporting) image
#
# Self-hosted Evidence serving the curated business report over the dbt marts
# in ClickHouse. The SQL lives in `evidence/queries/` so it can also be reused
# in Metabase.
# ---------------------------------------------------------------------------
FROM evidencedev/serve:latest

COPY --chown=evidence:evidence . /project
