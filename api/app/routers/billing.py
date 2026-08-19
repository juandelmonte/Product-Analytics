"""Billing source APIs (Stripe-like): customers, prices, subscriptions, invoices."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import BillingCustomer, BillingInvoice, BillingPrice, BillingSubscription
from ..pagination import Page
from ..source_paging import apply_cursor, apply_updated_since, finish_page

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/customers")
def list_customers(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(BillingCustomer)
    stmt = apply_updated_since(stmt, BillingCustomer.source_updated_at, updated_since)
    stmt = stmt.order_by(BillingCustomer.source_updated_at.asc(), BillingCustomer.customer_id.asc())
    stmt = apply_cursor(stmt, (BillingCustomer.source_updated_at, BillingCustomer.customer_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "customer_id")

    data = [
        {
            "customer_id": r.customer_id,
            "account_ref": r.account_ref,
            "email": r.email,
            "name": r.name,
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)


@router.get("/prices")
def list_prices(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(BillingPrice)
    stmt = apply_updated_since(stmt, BillingPrice.source_updated_at, updated_since)
    stmt = stmt.order_by(BillingPrice.source_updated_at.asc(), BillingPrice.price_id.asc())
    stmt = apply_cursor(stmt, (BillingPrice.source_updated_at, BillingPrice.price_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "price_id")

    data = [
        {
            "price_id": r.price_id,
            "product_id": r.product_id,
            "plan": r.plan,          # schema-evolution field (may be null pre-cutover)
            "plan_code": r.plan_code,
            "unit_amount": float(r.unit_amount),
            "currency": r.currency,
            "billing_frequency": r.billing_frequency,
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)


@router.get("/subscriptions")
def list_subscriptions(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(BillingSubscription)
    stmt = apply_updated_since(stmt, BillingSubscription.source_updated_at, updated_since)
    stmt = stmt.order_by(BillingSubscription.source_updated_at.asc(), BillingSubscription.subscription_id.asc())
    stmt = apply_cursor(stmt, (BillingSubscription.source_updated_at, BillingSubscription.subscription_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "subscription_id")

    data = [
        {
            "subscription_id": r.subscription_id,
            "customer_id": r.customer_id,
            "price_id": r.price_id,
            "status": r.status,
            "seats": r.seats,
            "start_date": r.start_date.isoformat(),
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "recorded_at": r.recorded_at.isoformat(),
            "effective_at": r.effective_at.isoformat(),
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)


@router.get("/invoices")
def list_invoices(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(BillingInvoice)
    stmt = apply_updated_since(stmt, BillingInvoice.source_updated_at, updated_since)
    stmt = stmt.order_by(BillingInvoice.source_updated_at.asc(), BillingInvoice.invoice_id.asc())
    stmt = apply_cursor(stmt, (BillingInvoice.source_updated_at, BillingInvoice.invoice_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "invoice_id")

    data = [
        {
            "invoice_id": r.invoice_id,
            "customer_id": r.customer_id,
            "subscription_id": r.subscription_id,
            "amount_due": float(r.amount_due),
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)
