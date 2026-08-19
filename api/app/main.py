"""FastAPI app exposing source-system-like APIs for the SaaS simulation.

Serves the Mixpanel/HubSpot/Stripe-like endpoints over the operational
PostgreSQL database.
"""
from fastapi import FastAPI
from sqlalchemy import text

from .config import settings
from .db import engine
from .routers import billing, crm, product_events

app = FastAPI(
    title="SaaS Product Analytics — Source APIs",
    description="Mixpanel/HubSpot/Stripe-like source APIs over the simulated operational database.",
    version="0.1.0",
)

app.include_router(product_events.router)
app.include_router(crm.router)
app.include_router(billing.router)


@app.get("/health")
def health() -> dict:
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unavailable", "seed": settings.seed}
