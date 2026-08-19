"""Demo scenario seeder.

Populates a single account walking the full activation path, so the source APIs
have real rows to serve. This is a development aid for API validation; the
full 24-month population comes from the simulation module (`app.sim`).

Run inside the api container:
    python -m app.seed_demo
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .db import SessionLocal
from . import events
from .models import (
    Account,
    BillingCustomer,
    BillingPrice,
    BillingSubscription,
    CRMCompany,
    CRMContact,
    CRMDeal,
    Membership,
    Project,
    Task,
    User,
    Workspace,
)


def seed(session) -> None:
    now = datetime.utcnow()

    account = Account(account_id="acc_demo", name="Demo Co", country="US", industry="SaaS")
    user1 = User(user_id="usr_demo_1", account_id="acc_demo", email="owner@demo.co", role="owner")
    user2 = User(user_id="usr_demo_2", account_id="acc_demo", email="member@demo.co", role="member")
    session.add_all([account, user1, user2])
    session.flush()  # accounts + users must exist before memberships reference them

    session.add(Membership(membership_id="mem_1", account_id="acc_demo", user_id="usr_demo_1", role="owner", invited_at=now, joined_at=now))
    session.add(Membership(membership_id="mem_2", account_id="acc_demo", user_id="usr_demo_2", role="member", invited_at=now + timedelta(hours=1), joined_at=now + timedelta(hours=2)))

    ws = Workspace(workspace_id="ws_demo", account_id="acc_demo", name="Demo Workspace")
    session.add(ws)
    session.flush()  # workspace must exist before project/task reference it

    prj = Project(project_id="prj_demo", workspace_id="ws_demo", name="Launch")
    session.add(prj)
    session.flush()

    tsk = Task(task_id="tsk_demo", project_id="prj_demo", assignee_id="usr_demo_1", title="Set up", status="done", completed_at=now + timedelta(hours=6))
    session.add(tsk)

    # CRM
    company = CRMCompany(company_id="cmp_demo", account_ref="acc_demo", name="Demo Co", industry="SaaS", company_size="11-50", country="USA", lead_source="organic", lifecycle_stage="customer")
    session.add(company)
    session.flush()

    contact = CRMContact(contact_id="ctc_demo", company_id="cmp_demo", email="owner@demo.co", first_name="A", last_name="Owner", lifecycle_stage="customer")
    deal = CRMDeal(deal_id="deal_demo", company_id="cmp_demo", deal_stage="closed_won", amount=1200, close_date=(now + timedelta(days=30)).date())
    session.add_all([contact, deal])

    # Billing
    customer = BillingCustomer(customer_id="cus_demo", account_ref="acc_demo", email="owner@demo.co", name="Demo Co")
    session.add(customer)
    session.flush()

    price = BillingPrice(price_id="prc_demo_pro", product_id="prod_taskflow", plan_code="pro", unit_amount=20, currency="usd", billing_frequency="monthly")
    session.add(price)
    session.flush()

    sub = BillingSubscription(subscription_id="sub_demo", customer_id="cus_demo", price_id="prc_demo_pro", status="active", seats=5, start_date=now, effective_at=now)
    session.add(sub)

    # Product events (business actions -> events)
    events.account_created(session, user_id="usr_demo_1", account_id="acc_demo", name="Demo Co", country="US", channel="organic", plan="trial", event_at=now)
    events.signup(session, user_id="usr_demo_1", account_id="acc_demo", email="owner@demo.co", country="US", channel="organic", event_at=now)
    events.workspace_created(session, user_id="usr_demo_1", account_id="acc_demo", workspace_id="ws_demo", name="Demo Workspace", event_at=now + timedelta(minutes=10))
    events.project_created(session, user_id="usr_demo_1", account_id="acc_demo", workspace_id="ws_demo", project_id="prj_demo", name="Launch", event_at=now + timedelta(minutes=20))
    events.membership_invited(session, user_id="usr_demo_1", account_id="acc_demo", invitee_email="member@demo.co", role="member", event_at=now + timedelta(hours=1))
    events.task_created(session, user_id="usr_demo_1", account_id="acc_demo", workspace_id="ws_demo", project_id="prj_demo", task_id="tsk_demo", event_at=now + timedelta(hours=3))
    events.task_completed(session, user_id="usr_demo_1", account_id="acc_demo", task_id="tsk_demo", project_id="prj_demo", hours_to_complete=3, event_at=now + timedelta(hours=6))
    events.plan_changed(session, user_id="usr_demo_1", account_id="acc_demo", from_plan="trial", to_plan="pro", event_at=now + timedelta(hours=8))

    session.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
        print("Demo scenario seeded.")
    finally:
        session.close()
