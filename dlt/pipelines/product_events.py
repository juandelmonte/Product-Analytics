"""Product events ingestion (Mixpanel-like).

- Historical: incremental cursor seeded at epoch → loads everything, then
  persists the max `source_updated_at` as the watermark.
- Incremental: reuses the persisted watermark → loads only new rows.

`append` disposition is intentional: duplicate deliveries of the same event_id
must survive in bronze (the DQ scenario "duplicate events" is detected and
deduped downstream in dbt).
"""
from __future__ import annotations

import dlt

from .client import fetch_pages
from .common import new_pipeline

EPOCH = "1970-01-01T00:00:00"


@dlt.resource(table_name="product_events", write_disposition="append")
def product_events(updated_since=dlt.sources.incremental("source_updated_at", initial_value=EPOCH)):
    yield from fetch_pages(
        "/api/product-events",
        params={"updated_since": updated_since.last_value} if updated_since.last_value else {},
    )


def run(incremental: bool = False, since: str | None = None) -> None:
    pipe = new_pipeline("product_events")
    info = pipe.run(product_events)
    print(f"product_events loaded: {info}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--since", default=None)
    args = parser.parse_args()
    run(incremental=args.incremental, since=args.since)
