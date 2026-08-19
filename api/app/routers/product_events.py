"""Product events source API (Mixpanel-like export).

GET /api/product-events
  ?from=ISO8601&to=ISO8601      filter on event_at
  ?updated_since=ISO8601        filter on source_updated_at (incremental cursor)
  ?limit=100&cursor=...         pagination
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ProductEvent
from ..pagination import Page
from ..source_paging import apply_cursor, apply_updated_since, finish_page, parse_dt

router = APIRouter(prefix="/api/product-events", tags=["product-events"])


@router.get("")
def list_product_events(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    from_dt = parse_dt(from_, "from")
    to_dt = parse_dt(to, "to")

    stmt = select(ProductEvent)

    if from_dt is not None:
        stmt = stmt.where(ProductEvent.event_at >= from_dt)
    if to_dt is not None:
        stmt = stmt.where(ProductEvent.event_at < to_dt)
    stmt = apply_updated_since(stmt, ProductEvent.source_updated_at, updated_since)
    stmt = stmt.order_by(ProductEvent.source_updated_at.asc(), ProductEvent.event_id.asc())
    stmt = apply_cursor(stmt, (ProductEvent.source_updated_at, ProductEvent.event_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "event_id")

    data = [
        {
            "event_id": r.event_id,
            "event_name": r.event_name,
            "distinct_id": r.distinct_id,
            "account_id": r.account_id,
            "event_at": r.event_at.isoformat(),
            "source_updated_at": r.source_updated_at.isoformat(),
            "properties": r.properties,
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)
