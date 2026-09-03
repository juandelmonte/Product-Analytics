"""Simulation constants and catalogues.

Values intentionally mirror real-world messiness (US/USA/United States,
Enterprise/ENT, Monthly/month) so the standardisation story in dbt is real.
"""
from __future__ import annotations

PLANS = ["free", "trial", "pro", "enterprise"]

# Human plan names used in billing_price.plan (schema evolution story).
PLAN_NAMES = {
    "free": "Free",
    "trial": "Trial",
    "pro": "Pro",
    "enterprise": "Enterprise",
}

# Messy variants of the same plan name seen in `plan`.
PLAN_NAME_VARIANTS = {
    "free": ["Free", "free", "FREE"],
    "trial": ["Trial", "trial", "TRIAL"],
    "pro": ["Pro", "pro", "PRO"],
    "enterprise": ["Enterprise", "enterprise", "ENT"],
}

# Messy country variants for standardisation.
COUNTRY_VARIANTS = {
    "US": ["US", "USA", "United States"],
    "CA": ["CA", "Canada", "CAN"],
    "GB": ["GB", "UK", "United Kingdom"],
}

# Messy billing frequency variants.
FREQUENCY_VARIANTS = {
    "monthly": ["monthly", "Monthly", "month"],
    "annual": ["annual", "Annual", "year"],
}

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-1000", "1000+"]

INDUSTRIES = ["SaaS", "E-commerce", "Finance", "Healthcare", "Education", "Media"]

LEAD_SOURCES = ["organic", "paid", "referral", "partner", "outbound"]

LIFECYCLE_STAGES = ["subscriber", "lead", "mql", "sql", "customer", "churned"]

DEAL_STAGES = ["new", "trial", "closed_won", "closed_lost"]

CHANNELS = ["organic", "paid", "referral"]

INTEGRATIONS = ["slack", "github", "google"]

# Feature codes (for adoption mart).
FEATURES = ["workspace", "projects", "tasks", "comments", "integrations"]

# Deterministic base ids used in event_id generation (no randomness in ids).
ID_PREFIX = {"account": "acc", "user": "usr", "workspace": "ws", "project": "prj",
             "task": "tsk", "event": "evt", "company": "cmp", "contact": "ctc",
             "deal": "deal", "customer": "cus", "price": "prc", "sub": "sub",
             "invoice": "inv", "membership": "mem"}
