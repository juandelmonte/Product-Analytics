"""Ingestion entrypoint.

Run inside the dlt container:
    python -m pipelines.ingest                 # historical (full)
    python -m pipelines.ingest --incremental   # incremental (updated_since)
    python -m pipelines.ingest --since 2026-08-01T00:00:00
"""
from __future__ import annotations

import argparse

from . import crm_billing, product_events


def main() -> None:
    parser = argparse.ArgumentParser(prog="ingest")
    parser.add_argument("--incremental", action="store_true", help="incremental load (cursor on source_updated_at)")
    parser.add_argument("--since", default=None, help="ISO8601 lower bound for incremental watermark")
    args = parser.parse_args()

    product_events.run(incremental=args.incremental, since=args.since)
    crm_billing.run(crm_billing.CRM_COLLECTIONS, "crm", incremental=args.incremental, since=args.since)
    crm_billing.run(crm_billing.BILLING_COLLECTIONS, "billing", incremental=args.incremental, since=args.since)


if __name__ == "__main__":
    main()
