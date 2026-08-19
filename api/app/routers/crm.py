"""CRM source APIs (HubSpot-like): contacts, companies, deals."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import CRMCompany, CRMContact, CRMDeal
from ..pagination import Page
from ..source_paging import apply_cursor, apply_updated_since, finish_page

router = APIRouter(prefix="/api/crm", tags=["crm"])


@router.get("/contacts")
def list_contacts(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(CRMContact)
    stmt = apply_updated_since(stmt, CRMContact.source_updated_at, updated_since)
    stmt = stmt.order_by(CRMContact.source_updated_at.asc(), CRMContact.contact_id.asc())
    stmt = apply_cursor(stmt, (CRMContact.source_updated_at, CRMContact.contact_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "contact_id")

    data = [
        {
            "contact_id": r.contact_id,
            "company_id": r.company_id,
            "email": r.email,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "lifecycle_stage": r.lifecycle_stage,
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)


@router.get("/companies")
def list_companies(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(CRMCompany)
    stmt = apply_updated_since(stmt, CRMCompany.source_updated_at, updated_since)
    stmt = stmt.order_by(CRMCompany.source_updated_at.asc(), CRMCompany.company_id.asc())
    stmt = apply_cursor(stmt, (CRMCompany.source_updated_at, CRMCompany.company_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "company_id")

    data = [
        {
            "company_id": r.company_id,
            "account_ref": r.account_ref,
            "name": r.name,
            "industry": r.industry,
            "company_size": r.company_size,
            "country": r.country,
            "lead_source": r.lead_source,
            "lifecycle_stage": r.lifecycle_stage,
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)


@router.get("/deals")
def list_deals(
    updated_since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> Page[dict]:
    stmt = select(CRMDeal)
    stmt = apply_updated_since(stmt, CRMDeal.source_updated_at, updated_since)
    stmt = stmt.order_by(CRMDeal.source_updated_at.asc(), CRMDeal.deal_id.asc())
    stmt = apply_cursor(stmt, (CRMDeal.source_updated_at, CRMDeal.deal_id), cursor)
    stmt = stmt.limit(limit + 1)

    rows = session.execute(stmt).scalars().all()
    rows, next_cursor = finish_page(list(rows), limit, "source_updated_at", "deal_id")

    data = [
        {
            "deal_id": r.deal_id,
            "company_id": r.company_id,
            "deal_stage": r.deal_stage,
            "amount": float(r.amount),
            "close_date": r.close_date.isoformat() if r.close_date else None,
            "source_updated_at": r.source_updated_at.isoformat(),
        }
        for r in rows
    ]
    return Page(data=data, next_cursor=next_cursor)
