"""Operational domain models.

These are the *operational* entities the simulation produces and the source
APIs read. They mirror the source contracts in `docs/source_contracts.md`.

Entity grouping:
- Identity / core: accounts, users, memberships, workspaces, projects, tasks
- Product:        product_events
- CRM:            crm_contacts, crm_companies, crm_deals
- Billing:        billing_customers, billing_prices, billing_subscriptions,
                  billing_invoices

Identifiers are source-specific strings (no universal ID): the canonical
mapping is built downstream in dbt (int_identity_mapping).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _id(prefix: str) -> str:
    """Generate a stable-looking source id: <prefix>_<uuid4 hex>."""
    return f"{prefix}_{uuid.uuid4().hex}"


def _utcnow() -> datetime:
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Identity / core
# ---------------------------------------------------------------------------


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("acc"))
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(64), default="US")
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("usr"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="member")  # owner/admin/member
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Membership(Base):
    __tablename__ = "memberships"

    membership_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("mem"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    role: Mapped[str] = mapped_column(String(32), default="member")
    invited_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Workspace(Base):
    __tablename__ = "workspaces"

    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("ws"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("prj"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.workspace_id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("tsk"))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="open")  # open/done
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Product events
# ---------------------------------------------------------------------------


class ProductEvent(Base):
    __tablename__ = "product_events"

    # Surrogate physical row key: the same event_id may be delivered more than
    # once (duplicate delivery). event_id is the stable *dedup* key, used
    # downstream in dbt.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    event_name: Mapped[str] = mapped_column(String(64), index=True)
    distinct_id: Mapped[str] = mapped_column(String(64), index=True)  # user_id
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    event_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)


# ---------------------------------------------------------------------------
# CRM
# ---------------------------------------------------------------------------


class CRMContact(Base):
    __tablename__ = "crm_contacts"

    contact_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("ctc"))
    company_id: Mapped[str | None] = mapped_column(ForeignKey("crm_companies.company_id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(32), default="subscriber")
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class CRMCompany(Base):
    __tablename__ = "crm_companies"

    company_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("cmp"))
    account_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # -> accounts.account_id
    name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str] = mapped_column(String(64), default="US")
    lead_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(32), default="subscriber")
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class CRMDeal(Base):
    __tablename__ = "crm_deals"

    deal_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("deal"))
    company_id: Mapped[str] = mapped_column(ForeignKey("crm_companies.company_id"), index=True)
    deal_stage: Mapped[str] = mapped_column(String(32), default="new")  # new/trial/closed_won/closed_lost
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("cus"))
    account_ref: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # -> accounts.account_id
    email: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255))
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class BillingPrice(Base):
    __tablename__ = "billing_prices"

    price_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("prc"))
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    # Schema evolution: before a historical cutover only `plan` (human name) was
    # populated; after, both `plan` and `plan_code` exist.
    plan: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)  # free/trial/pro/enterprise
    unit_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(8), default="usd")
    billing_frequency: Mapped[str] = mapped_column(String(16), default="monthly")  # monthly/annual
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class BillingSubscription(Base):
    __tablename__ = "billing_subscriptions"

    # Append-only subscription history: the same subscription_id appears once
    # per period (plan/seat change appends a new row). Surrogate id is the row key.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[str] = mapped_column(String(64), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("billing_customers.customer_id"), index=True)
    price_id: Mapped[str] = mapped_column(ForeignKey("billing_prices.price_id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="trialing")  # trialing/active/past_due/canceled
    seats: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    effective_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class BillingInvoice(Base):
    __tablename__ = "billing_invoices"

    invoice_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: _id("inv"))
    customer_id: Mapped[str] = mapped_column(ForeignKey("billing_customers.customer_id"), index=True)
    subscription_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_due: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(16), default="open")  # paid/open/void
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# Simulation state
# ---------------------------------------------------------------------------


class SimState(Base):
    __tablename__ = "sim_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # singleton row id=1
    seed: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    sim_date: Mapped[date] = mapped_column(Date)  # last advanced day
    day_index: Mapped[int] = mapped_column(Integer, default=0)  # days advanced


class SimPending(Base):
    """Scheduled-but-undelivered source records (late events, late CRM updates,
    future-effective billing changes, duplicate deliveries)."""

    __tablename__ = "sim_pending"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_date: Mapped[date] = mapped_column(Date, index=True)
    kind: Mapped[str] = mapped_column(String(32))  # product_event / crm_update / billing_change / duplicate
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)


class SimAccountState(Base):
    """Simulation-internal per-account state (segment, engagement, lifecycle)."""

    __tablename__ = "sim_account_state"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    segment: Mapped[str] = mapped_column(String(32))  # activated / failed_onboarding / engaged / low_engagement
    engagement: Mapped[str] = mapped_column(String(16))  # high / medium / low
    signup_day: Mapped[int] = mapped_column(Integer)  # day_index of signup
    activated: Mapped[bool] = mapped_column(Boolean, default=False)
    plan: Mapped[str] = mapped_column(String(32), default="trial")
