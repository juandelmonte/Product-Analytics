"""Shared dlt pipeline configuration and helpers.

Conventions (docs/ingestion_design.md):
- destination: ClickHouse `bronze` database.
- All pipelines preserve source timestamps (`source_updated_at`, `event_at`,
  `effective_at`) and add `_dlt_ingested_at`-style metadata via dlt defaults.
- Historical mode: append full snapshot. Incremental mode: cursor on
  `source_updated_at` (NOT event_at), so late-arriving records are not skipped.
"""
from __future__ import annotations

import os

import dlt
from dlt.destinations import clickhouse

API_BASE_URL = os.environ.get("API_BASE_URL", "http://api:8000")


def destination():
    return clickhouse(
        credentials=dict(
            database=os.environ.get("BRONZE_DB", os.environ.get("DESTINATION__CLICKHOUSE__CREDENTIALS__DATABASE", "bronze")),
            host=os.environ.get("CLICKHOUSE_HOST", "clickhouse"),
            port=int(os.environ.get("CLICKHOUSE_NATIVE_PORT", "9000")),
            http_port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
            secure=int(os.environ.get("CLICKHOUSE_SECURE", "0")),
            username=os.environ.get("CLICKHOUSE_USER", "default"),
            password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        )
    )


def new_pipeline(name: str, dataset_name: str | None = None):
    """Create a dlt pipeline writing to ClickHouse bronze.

    dataset_name is left None so dlt uses the default (schema-less) naming: the
    ClickHouse destination stores tables in the `database` from credentials
    (bronze) with clean `<table>` names instead of `dataset__table`.
    """
    return dlt.pipeline(
        pipeline_name=name,
        destination=destination(),
        dataset_name=dataset_name,
    )
