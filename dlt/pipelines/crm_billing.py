"""CRM + Billing ingestion (HubSpot/Stripe-like).

Each collection is its own resource/table. Historical = full load;
incremental = `updated_since` on `source_updated_at`.

Write disposition: `merge` with a source primary key → idempotent re-runs
(upsert by key, not duplicate).
"""
from __future__ import annotations

import dlt

from .client import fetch_pages
from .common import new_pipeline

# path -> (table name, primary key for merge)
CRM_COLLECTIONS = {
    "/api/crm/contacts": ("crm_contacts", "contact_id"),
    "/api/crm/companies": ("crm_companies", "company_id"),
    "/api/crm/deals": ("crm_deals", "deal_id"),
}

BILLING_COLLECTIONS = {
    "/api/billing/customers": ("billing_customers", "customer_id"),
    "/api/billing/prices": ("billing_prices", "price_id"),
    "/api/billing/subscriptions": ("billing_subscriptions", "subscription_id"),
    "/api/billing/invoices": ("billing_invoices", "invoice_id"),
}


def run(collections: dict[str, tuple[str, str]], pipeline_name: str, incremental: bool = False, since: str | None = None) -> None:
    resources = [
        _merge_resource(table, path, pk, since if incremental else None)
        for path, (table, pk) in collections.items()
    ]
    pipe = new_pipeline(pipeline_name)
    info = pipe.run(resources)
    print(f"{pipeline_name} loaded: {info}")


def _merge_resource(table: str, api_path: str, primary_key: str, since: str | None):
    """Merge (upsert by primary key) so re-runs are idempotent."""
    if since:
        @dlt.resource(name=table, table_name=table, write_disposition="merge", primary_key=primary_key)
        def res(api_path=api_path, updated_since=dlt.sources.incremental("source_updated_at", initial_value=since)):
            yield from fetch_pages(api_path, params={"updated_since": updated_since.last_value} if updated_since.last_value else {})
    else:
        @dlt.resource(name=table, table_name=table, write_disposition="merge", primary_key=primary_key)
        def res(api_path=api_path):
            yield from fetch_pages(api_path)

    return res


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--since", default=None)
    args = parser.parse_args()

    run(CRM_COLLECTIONS, "crm", incremental=args.incremental, since=args.since)
    run(BILLING_COLLECTIONS, "billing", incremental=args.incremental, since=args.since)
