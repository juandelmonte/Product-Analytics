"""Deterministic SaaS business simulation.

Design:
- A generator is seeded from `SEED` and walks the business day by day.
- `generate_history(days)` runs `advance_day()` `days` times from a clean state.
- `advance_day()`:
    1. delivers any `sim_pending` rows due today (late events, late CRM
       updates, duplicate deliveries, future-effective billing changes),
    2. generates the day's organic business (new signups, product activity,
       CRM/billing changes) as a function of each account's simulated state,
    3. schedules any delayed deliveries (late-arriving events, late CRM
       updates, future-effective billing changes) into `sim_pending`.

This makes the daily and historical paths identical and append-only: history is
never regenerated, and a day only appends records.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from .. import events
from ..models import (
    Account,
    BillingCustomer,
    BillingInvoice,
    BillingPrice,
    BillingSubscription,
    CRMCompany,
    CRMContact,
    CRMDeal,
    Membership,
    ProductEvent,
    Project,
    SimAccountState,
    SimPending,
    SimState,
    Task,
    User,
    Workspace,
)
from . import catalog as cat
from .rng import choice, make_rng, weighted

# --- tunable probabilities -------------------------------------------------
# Onboarding is a progressive funnel: each step has its own small dropout, so
# the funnel shows a realistic slope instead of one binary jump. The product of
# the step-through rates ≈ the overall activation rate (~70%).
P_WORKSPACE = 0.98               # signup -> workspace created
P_PROJECT_GIVEN_WORKSPACE = 0.91  # workspace -> first project created
P_INVITE_GIVEN_PROJECT = 0.94     # project -> teammate invited
P_TASK_GIVEN_INVITE = 0.93        # invite -> first task created
P_COMPLETE_GIVEN_TASK = 0.90      # task created -> task completed (activation)
P_FREE = 0.60             # share of signups that start on the FREE plan (rest = trial)
P_CONVERT_ACTIVATED = 0.35   # trial/free -> paid for activated accounts
P_CONVERT_DORMANT = 0.06     # trial/free -> paid for NON-activated accounts (small but real)
P_EXPAND = 0.14  # per active converted account per month
P_CHURN = 0.05  # per active converted account per month
P_DORMANT = 0.04  # per active account per month: goes dormant (stops using product)
P_LATE_EVENT = 0.06
P_DUP_EVENT = 0.04
P_LATE_CRM_UPDATE = 0.10
P_FUTURE_EFFECTIVE = 0.10
P_MISSING_ASSOC = 0.12

ACTIVATION_WINDOW_DAYS = 7
HISTORY_DAYS = 24 * 30  # ~24 months

# --- segment behaviour modifiers -------------------------------------------
# Account attributes (country / industry / company size) scale the global
# probabilities above, so different segments behave DIFFERENTLY. Without this,
# every dimension slice of the marts is uniform because each account is drawn
# from the same distribution and never behaves differently by segment.
#
# Multipliers are centred on ~1.0 so the overall (global) averages stay roughly
# the same, but a 1000+ SaaS account in the US will meaningfully out-convert and
# out-expand a 1-10 person Media account in CA, which is what makes the
# dimensional analysis non-trivial.
def _clamp(p: float) -> float:
    return max(0.0, min(1.0, p))


# product-market fit per industry: scales onboarding completion + paid conversion
INDUSTRY_FIT = {
    "SaaS": 1.15,
    "E-commerce": 0.90,
    "Finance": 1.05,
    "Healthcare": 1.10,
    "Education": 0.95,
    "Media": 0.85,
}

# expansion appetite per industry (bigger teams add seats faster)
INDUSTRY_EXPAND = {
    "SaaS": 1.15,
    "E-commerce": 1.05,
    "Finance": 1.00,
    "Healthcare": 0.95,
    "Education": 0.90,
    "Media": 1.10,
}

# stickiness per industry (higher = less churn + dormancy)
INDUSTRY_STICKINESS = {
    "SaaS": 1.00,
    "E-commerce": 0.85,
    "Finance": 1.25,
    "Healthcare": 1.15,
    "Education": 1.05,
    "Media": 0.80,
}

# larger companies convert + expand more and churn less (enterprise motion)
SIZE_FIT = {
    "1-10": 0.90,
    "11-50": 1.00,
    "51-200": 1.05,
    "201-1000": 1.15,
    "1000+": 1.30,
}

SIZE_STICKINESS = {
    "1-10": 0.90,
    "11-50": 1.00,
    "51-200": 1.05,
    "201-1000": 1.15,
    "1000+": 1.25,
}

# US is the mature core market; CA/GB a touch behind on conversion
COUNTRY_FIT = {
    "US": 1.10,
    "CA": 0.95,
    "GB": 1.00,
}

COUNTRY_STICKINESS = {
    "US": 1.00,
    "CA": 1.10,
    "GB": 1.05,
}


def _segment_modifiers(country: str, industry: str, size: str) -> dict:
    """Aggregate per-account multipliers.

    fit        - scales onboarding completion + paid conversion (higher = better)
    expand     - scales monthly expansion likelihood
    stickiness - scales retention: higher = LESS dormancy and churn
    """
    return {
        "fit":        COUNTRY_FIT.get(country, 1.0) * INDUSTRY_FIT.get(industry, 1.0) * SIZE_FIT.get(size, 1.0),
        "expand":     INDUSTRY_EXPAND.get(industry, 1.0) * SIZE_FIT.get(size, 1.0),
        "stickiness": COUNTRY_STICKINESS.get(country, 1.0) * INDUSTRY_STICKINESS.get(industry, 1.0) * SIZE_STICKINESS.get(size, 1.0),
    }


class Simulator:
    def __init__(self, session: Session, seed: int):
        self.session = session
        self.seed = seed
        self.rng = make_rng(seed)
        self.start_date: date | None = None
        self.sim_date: date | None = None
        self.day_index = 0
        self._counter = 0

    # --- id helpers (deterministic) -------------------------------------------------
    def _nid(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self.seed}_{self.day_index}_{self._counter}"

    # --- state ----------------------------------------------------------------------
    def _load_state(self) -> None:
        st = self.session.get(SimState, 1)
        if st is None:
            raise RuntimeError("sim_state missing - call init_history first")
        self.start_date = st.start_date
        self.sim_date = st.sim_date
        self.day_index = st.day_index
        # Per-day deterministic RNG: a day's randomness depends only on
        # (seed, day_index), so `advance_day` is idempotent and history is
        # reproducible regardless of how many prior days ran.
        self.rng = make_rng(self.seed * 1_000_003 + self.day_index)

    def _save_state(self) -> None:
        st = self.session.get(SimState, 1)
        st.sim_date = self.sim_date
        st.day_index = self.day_index

    # --- public API -----------------------------------------------------------------
    def init_history(self, days: int = HISTORY_DAYS) -> None:
        """Initialise sim state and seed the reference catalog (plans)."""
        existing = self.session.get(SimState, 1)
        if existing is not None:
            raise RuntimeError("sim_state already initialised; use advance_day or reset")

        self.start_date = date.today() - timedelta(days=days)
        self.sim_date = self.start_date
        self.day_index = 0

        self.session.add(SimState(id=1, seed=self.seed, start_date=self.start_date, sim_date=self.sim_date, day_index=0))
        self._seed_prices()
        self.session.commit()

    def generate_history(self, days: int = HISTORY_DAYS) -> None:
        self.init_history(days)
        for _ in range(days):
            self.advance_day()
        # Close the books: accounts that signed up in the final few days can
        # still have late-arriving onboarding events (and duplicate deliveries)
        # queued beyond the horizon. Deliver them now so the journey/activation
        # marts stay internally consistent (e.g. no task_created without the
        # preceding project_created).
        self._drain_pending_events()

    def _drain_pending_events(self) -> None:
        """Deliver any still-queued product-event deliveries (late events and
        duplicate deliveries), oldest first, regardless of their scheduled date.
        """
        rows = (
            self.session.query(SimPending)
            .filter(SimPending.kind.in_(["product_event", "duplicate"]))
            .order_by(SimPending.delivery_date)
            .all()
        )
        for row in rows:
            if row.kind == "product_event":
                self._apply_product_event(row.payload)
            else:
                payload = dict(row.payload)
                payload["event_at"] = datetime.fromisoformat(payload["event_at"])
                payload["source_updated_at"] = datetime.utcnow()
                self.session.add(ProductEvent(**payload))
            self.session.delete(row)
        self.session.commit()

    def advance_day(self) -> None:
        self._load_state()

        # 1. deliver pending records due on this sim_date
        self._deliver_pending()

        # 2. today's organic business
        day = self.sim_date
        self._day_signups(day)
        self._day_existing_activity(day)

        # 3. bump date and persist
        self.sim_date = day + timedelta(days=1)
        self.day_index += 1
        self._save_state()
        self.session.commit()

    # --- reference data -------------------------------------------------------------
    def _seed_prices(self) -> None:
        # Schema evolution (DQ scenario 9): the pre-cutover catalog has ONLY
        # `plan` (messy human name); `plan_code` arrives later. dbt staging
        # coalesces plan_code = coalesce(plan_code, standardise(plan)).
        prices = [
            ("free", ["Free", "free", "FREE"], 0.0, "monthly"),
            ("trial", ["Trial", "trial", "TRIAL"], 0.0, "monthly"),
            ("pro", ["Pro", "pro", "PRO"], 20.0, "monthly"),
            ("enterprise", ["Enterprise", "enterprise", "ENT"], 50.0, "monthly"),
        ]
        for code, names, amount, freq in prices:
            plan_name = choice(self.rng, names)
            self.session.add(
                BillingPrice(
                    price_id=f"prc_{code}",
                    product_id="prod_taskflow",
                    plan=plan_name,        # messy human name (standardised in dbt)
                    plan_code=code,        # canonical code (dbt coalesce prefers this)
                    unit_amount=amount,
                    currency="usd",
                    billing_frequency=choice(self.rng, cat.FREQUENCY_VARIANTS[freq]),
                )
            )

    # --- pending delivery -----------------------------------------------------------
    def _deliver_pending(self) -> None:
        rows = self.session.query(SimPending).filter(SimPending.delivery_date == self.sim_date).all()
        for row in rows:
            if row.kind == "product_event":
                self._apply_product_event(row.payload)
            elif row.kind == "duplicate":
                # re-insert an existing event with the SAME event_id (dedup test)
                payload = dict(row.payload)
                payload["event_at"] = datetime.fromisoformat(payload["event_at"])
                payload["source_updated_at"] = datetime.utcnow()
                self.session.add(ProductEvent(**payload))
            elif row.kind == "crm_update":
                self._apply_crm_update(row.payload)
            elif row.kind == "billing_change":
                self._apply_billing_change(row.payload)
            self.session.delete(row)
        self.session.flush()

    def _apply_product_event(self, payload: dict) -> None:
        """Insert a late-arriving product event (event_at is in the past).

        `source_updated_at` is the actual write time (now), NOT the scheduled
        delivery date - so the incremental cursor stays monotonic and late
        events are never skipped.
        """
        p = dict(payload)
        p["event_at"] = datetime.fromisoformat(p["event_at"])
        p["source_updated_at"] = datetime.utcnow()
        self.session.add(ProductEvent(**p))

    def _schedule(self, kind: str, payload: dict, when: date) -> None:
        self.session.add(SimPending(delivery_date=when, kind=kind, payload=payload))

    # --- signups --------------------------------------------------------------------
    def _day_signups(self, day: date) -> None:
        # deterministic count of new accounts today (1..4)
        n_new = self.rng.randint(1, 4)
        for _ in range(n_new):
            self._new_account(day)

    def _new_account(self, day: date) -> None:
        aid = self._nid("acc")
        country = choice(self.rng, ["US", "CA", "GB"])
        industry = choice(self.rng, cat.INDUSTRIES)
        size = choice(self.rng, cat.COMPANY_SIZES)
        source = choice(self.rng, cat.LEAD_SOURCES)
        channel = choice(self.rng, cat.CHANNELS)
        mod = _segment_modifiers(country, industry, size)

        # account + owner
        acc = Account(account_id=aid, name=f"Company {aid}", country=country, industry=industry, company_size=size, lead_source=source)
        owner = User(user_id=f"{aid}_u1", account_id=aid, email=f"owner+{aid}@example.com", role="owner")
        self.session.add_all([acc, owner])
        self.session.flush()

        self.session.add(Membership(membership_id=self._nid("mem"), account_id=aid, user_id=f"{aid}_u1", role="owner", invited_at=datetime.combine(day, datetime.min.time()), joined_at=datetime.combine(day, datetime.min.time())))

        # sim state (plan = free or trial at signup; activation determined by the
        # progressive onboarding funnel below)
        plan = "free" if self.rng.random() < P_FREE else "trial"
        engagement = weighted(self.rng, [("high", 0.30), ("medium", 0.45), ("low", 0.25)])
        self.session.add(SimAccountState(account_id=aid, segment="failed_onboarding", engagement=engagement, signup_day=self.day_index, activated=False, plan=plan))

        # CRM company/contact (missing association scenario: some contacts have no company)
        company_id = self._nid("cmp")
        self.session.add(CRMCompany(company_id=company_id, account_ref=aid, name=f"Company {aid}", industry=industry, company_size=size, country=choice(self.rng, cat.COUNTRY_VARIANTS[country]), lead_source=source, lifecycle_stage="lead"))
        self.session.flush()
        contact_id = self._nid("ctc")
        contact_company = None if self.rng.random() < P_MISSING_ASSOC else company_id
        self.session.add(CRMContact(contact_id=contact_id, company_id=contact_company, email=f"owner+{aid}@example.com", first_name="Owner", last_name=str(self.day_index), lifecycle_stage="lead"))

        # missing association RESOLUTION (DQ scenario 7): a contact created
        # without a company gains one a few days later via a late CRM update.
        if contact_company is None:
            self._schedule(
                "crm_update",
                {"company_id": company_id, "contact_id": contact_id, "link_contact": True},
                day + timedelta(days=self.rng.randint(2, 6)),
            )

        # billing customer + initial subscription (free or trial)
        customer_id = self._nid("cus")
        self.session.add(BillingCustomer(customer_id=customer_id, account_ref=aid, email=f"owner+{aid}@example.com", name=f"Company {aid}"))
        self.session.flush()
        initial_price = "prc_free" if plan == "free" else "prc_trial"
        self.session.add(BillingSubscription(subscription_id=self._nid("sub"), customer_id=customer_id, price_id=initial_price, status="active" if plan == "free" else "trialing", seats=1, start_date=datetime.combine(day, datetime.min.time()), effective_at=datetime.combine(day, datetime.min.time())))

        # CRM deal (sales view of the new account)
        self.session.add(CRMDeal(deal_id=self._nid("deal"), company_id=company_id, deal_stage="trial", amount=0, close_date=None))

        # product events (signup + account_created)
        ts = datetime.combine(day, datetime.min.time()) + timedelta(hours=self.rng.randint(8, 18))
        ev1 = events.account_created(self.session, user_id=f"{aid}_u1", account_id=aid, name=f"Company {aid}", country=country, channel=channel, plan=plan, event_at=ts, event_id=self._nid("evt"))
        ev2 = events.signup(self.session, user_id=f"{aid}_u1", account_id=aid, email=f"owner+{aid}@example.com", country=country, channel=channel, event_at=ts + timedelta(seconds=5), event_id=self._nid("evt"))

        # late-arriving duplicate of the signup event (dedup test)
        if self.rng.random() < P_DUP_EVENT:
            self._schedule("duplicate", {"event_id": ev2.event_id, "event_name": "user_signup", "distinct_id": f"{aid}_u1", "account_id": aid, "event_at": ev2.event_at.isoformat(), "properties": dict(ev2.properties)}, day + timedelta(days=self.rng.randint(1, 5)))

        # walk the onboarding funnel (progressive per-step dropout), scaled by
        # the account's product-market fit so stronger segments activate more.
        self._onboarding_flow(aid, day, ts, fit_mod=mod["fit"])

        # conversion: fully activated accounts convert at a healthy rate;
        # accounts that dropped during onboarding still convert occasionally
        # (free/trial -> paid happens even without full activation, just much
        # less often). Segment fit scales both paths.
        st = self.session.get(SimAccountState, aid)
        base_conv = P_CONVERT_ACTIVATED if st.activated else P_CONVERT_DORMANT
        p_convert = _clamp(base_conv * mod["fit"])
        if self.rng.random() < p_convert:
            self._schedule_conversion(aid, day)

    def _onboarding_flow(self, aid: str, day: date, signup_ts: datetime, fit_mod: float = 1.0) -> None:
        """Activation path: workspace → project → invite → task → completed.

        Starts AFTER the signup event (signup_ts) so activation is always
        temporally ordered after signup. Each step has an independent dropout
        probability, so the funnel shows a realistic, progressive slope instead
        of a single binary jump; the account is marked activated only if it
        reaches the final step.

        `fit_mod` (>1 = better product-market fit) lowers the dropout at every
        step, so stronger segments (larger / SaaS / US) activate more.
        """
        ts0 = signup_ts + timedelta(minutes=15)
        owner = f"{aid}_u1"

        # 1. workspace (a few signups never even create a workspace)
        if self.rng.random() >= _clamp(1 - (1 - P_WORKSPACE) * fit_mod):
            return
        ws = Workspace(workspace_id=self._nid("ws"), account_id=aid, name="Workspace")
        self.session.add(ws)
        self.session.flush()
        events.workspace_created(self.session, user_id=owner, account_id=aid, workspace_id=ws.workspace_id, name="Workspace", event_at=ts0, event_id=self._nid("evt"))

        # some accounts are slow → their activation events arrive LATE
        late = self.rng.random() < P_LATE_EVENT

        # 2. project
        if self.rng.random() >= _clamp(1 - (1 - P_PROJECT_GIVEN_WORKSPACE) * fit_mod):
            return
        prj = Project(project_id=self._nid("prj"), workspace_id=ws.workspace_id, name="First project")
        self.session.add(prj)
        self.session.flush()
        pev = dict(workspace_id=ws.workspace_id, project_id=prj.project_id, name="First project")
        self._emit_or_schedule("project_created", owner, aid, pev, ts0 + timedelta(minutes=20), late, day)

        # 3. invite teammate (membership count → 2)
        if self.rng.random() >= _clamp(1 - (1 - P_INVITE_GIVEN_PROJECT) * fit_mod):
            return
        invitee = f"{aid}_u2"
        self.session.add(User(user_id=invitee, account_id=aid, email=f"member+{aid}@example.com", role="member"))
        self.session.flush()
        self.session.add(Membership(membership_id=self._nid("mem"), account_id=aid, user_id=invitee, role="member", invited_at=ts0 + timedelta(hours=1), joined_at=ts0 + timedelta(hours=2)))
        self._emit_or_schedule("membership_invited", owner, aid, {"invitee_email": f"member+{aid}@example.com", "role": "member"}, ts0 + timedelta(hours=1), late, day)

        # 4. first task created
        if self.rng.random() >= _clamp(1 - (1 - P_TASK_GIVEN_INVITE) * fit_mod):
            return
        tsk = Task(task_id=self._nid("tsk"), project_id=prj.project_id, assignee_id=owner, title="Set up", status="done", completed_at=ts0 + timedelta(hours=6))
        self.session.add(tsk)
        self._emit_or_schedule("task_created", owner, aid, {"workspace_id": ws.workspace_id, "project_id": prj.project_id, "task_id": tsk.task_id}, ts0 + timedelta(hours=3), late, day)

        # 5. task completed (the activation moment)
        if self.rng.random() >= _clamp(1 - (1 - P_COMPLETE_GIVEN_TASK) * fit_mod):
            return
        self._emit_or_schedule("task_completed", owner, aid, {"task_id": tsk.task_id, "project_id": prj.project_id, "hours_to_complete": 3}, ts0 + timedelta(hours=6), late, day)

        # mark activated
        st = self.session.get(SimAccountState, aid)
        st.activated = True
        st.segment = "activated"

    def _emit_or_schedule(self, name: str, uid: str, aid: str, props: dict, ts: datetime, late: bool, day: date) -> None:
        if late:
            delayed = day + timedelta(days=self.rng.randint(2, 6))
            self._schedule("product_event", {
                "event_id": self._nid("evt"),
                "event_name": name,
                "distinct_id": uid,
                "account_id": aid,
                "event_at": ts.isoformat(),
                "properties": props,
            }, delayed)
        else:
            getattr(events, name)(self.session, user_id=uid, account_id=aid, event_at=ts, event_id=self._nid("evt"), **props)

    # --- conversion / billing -------------------------------------------------------
    def _schedule_conversion(self, aid: str, day: date) -> None:
        """free/trial → paid conversion, possibly future-effective."""
        st = self.session.get(SimAccountState, aid)
        from_plan = st.plan if st is not None else "trial"
        when = day + timedelta(days=self.rng.randint(3, 14))
        future = self.rng.random() < P_FUTURE_EFFECTIVE
        effective = when + timedelta(days=self.rng.randint(2, 7)) if future else when
        self._schedule(
            "billing_change",
            {
                "account_id": aid,
                "from_plan": from_plan,
                "to_plan": "pro",
                "recorded_at": datetime.combine(when, datetime.min.time()).isoformat(),
                "effective_at": datetime.combine(effective, datetime.min.time()).isoformat(),
            },
            when,
        )

    def _apply_billing_change(self, payload: dict) -> None:
        aid = payload["account_id"]
        recorded = datetime.fromisoformat(payload["recorded_at"])
        effective = datetime.fromisoformat(payload["effective_at"])

        customer = self.session.query(BillingCustomer).filter(BillingCustomer.account_ref == aid).first()
        if customer is None:
            return

        # end the current subscription at the effective date (clamped to never
        # precede its own start)
        current = self.session.query(BillingSubscription).filter(BillingSubscription.customer_id == customer.customer_id).order_by(BillingSubscription.id.desc()).first()
        if current is not None:
            current.status = "canceled"
            current.ended_at = max(effective, current.start_date)

        # append a new subscription period (append-only history)
        price_id = "prc_pro" if payload["to_plan"] == "pro" else "prc_enterprise"
        self.session.add(BillingSubscription(
            subscription_id=self._nid("sub"),
            customer_id=customer.customer_id,
            price_id=price_id,
            status="active",
            seats=self.rng.randint(1, 10),
            start_date=effective,
            recorded_at=recorded,
            effective_at=effective,
        ))

        # plan_changed event
        events.plan_changed(self.session, user_id=f"{aid}_u1", account_id=aid, from_plan=payload["from_plan"], to_plan=payload["to_plan"], event_at=effective, event_id=self._nid("evt"))

        # CRM deal closes won on conversion
        company = self.session.query(CRMCompany).filter(CRMCompany.account_ref == aid).first()
        if company is not None:
            deal = self.session.query(CRMDeal).filter(CRMDeal.company_id == company.company_id).order_by(CRMDeal.deal_id).first()
            if deal is not None:
                deal.deal_stage = "closed_won"
                deal.amount = 1000.0 * self.rng.randint(1, 10)
                deal.close_date = effective.date()

        # generate the first invoice for the new subscription
        sub = self.session.query(BillingSubscription).filter(BillingSubscription.customer_id == customer.customer_id).order_by(BillingSubscription.id.desc()).first()
        if sub is not None:
            self.session.add(BillingInvoice(invoice_id=self._nid("inv"), customer_id=customer.customer_id, subscription_id=sub.subscription_id, amount_due=float(sub.seats) * 20.0, status="paid", created_at=effective))

        # update sim state plan
        st = self.session.get(SimAccountState, aid)
        if st is not None:
            st.plan = payload["to_plan"]

    # --- CRM updates ----------------------------------------------------------------
    def _apply_crm_update(self, payload: dict) -> None:
        company = self.session.query(CRMCompany).filter(CRMCompany.company_id == payload["company_id"]).first()
        if company is None:
            return
        for field in ("industry", "company_size", "country", "lifecycle_stage", "lead_source"):
            if field in payload:
                setattr(company, field, payload[field])
        # missing association resolution: link contact to company
        if payload.get("link_contact") and payload.get("contact_id"):
            contact = self.session.query(CRMContact).filter(CRMContact.contact_id == payload["contact_id"]).first()
            if contact is not None:
                contact.company_id = payload["company_id"]

    # --- daily product activity -----------------------------------------------------
    def _day_existing_activity(self, day: date) -> None:
        """Generate daily product activity for existing activated accounts.

        - Weekend activity is lower (B2B work-week pattern).
        - Engagement (high/medium/low) shapes daily event volume.
        - Monthly, a small share of accounts goes dormant (stops using the
          product), which drives realistic retention decay.
        - Monthly, paying accounts may churn or expand.
        """
        is_weekend = day.weekday() >= 5
        states = (
            self.session.query(SimAccountState)
            .filter(SimAccountState.activated.is_(True))
            .all()
        )
        for st in states:
            # dormant accounts no longer generate activity (they've stopped
            # using the product; this drives retention decay)
            if st.engagement == "dormant":
                continue

            # account attributes feed segment-specific churn/expand/dormancy
            acc = self.session.get(Account, st.account_id)
            mod = _segment_modifiers(acc.country, acc.industry, acc.company_size)

            # engagement-weighted daily event count, with a weekend dip
            base = {"high": 3, "medium": 1, "low": 0}[st.engagement]
            n_events = max(0, base - (1 if is_weekend else 0)) if self.rng.random() < 0.7 else 0
            for _ in range(n_events):
                self._random_activity_event(st.account_id, day)

            # monthly lifecycle changes (dormancy, churn, expansion)
            if self.day_index > 0 and self.day_index % 30 == 0:
                # dormancy: activated accounts occasionally stop using the product;
                # stickier segments (finance/healthcare, larger, CA) go dormant less.
                if st.engagement != "dormant" and self.rng.random() < _clamp(P_DORMANT / mod["stickiness"]):
                    st.engagement = "dormant"
                if st.engagement == "dormant":
                    continue
                if st.plan in ("pro", "enterprise"):
                    # churn: stickier segments churn less
                    if self.rng.random() < _clamp(P_CHURN / mod["stickiness"]):
                        self._churn(st.account_id, day)
                    # expansion: higher expand appetite + larger size expand more
                    elif self.rng.random() < _clamp(P_EXPAND * mod["expand"]):
                        self._expand(st.account_id, day)

    def _random_activity_event(self, aid: str, day: date) -> None:
        uid = f"{aid}_u1"
        ts = datetime.combine(day, datetime.min.time()) + timedelta(hours=self.rng.randint(8, 18))
        kind = choice(self.rng, ["task_created", "task_assigned", "task_commented", "task_completed", "integration_connected"])
        if kind == "task_created":
            events.task_created(self.session, user_id=uid, account_id=aid, workspace_id=f"ws_{aid}", project_id=f"prj_{aid}", task_id=self._nid("tsk"), event_at=ts, event_id=self._nid("evt"))
        elif kind == "task_assigned":
            events.task_assigned(self.session, user_id=uid, account_id=aid, task_id=self._nid("tsk"), assignee_id=f"{aid}_u2", event_at=ts, event_id=self._nid("evt"))
        elif kind == "task_commented":
            events.task_commented(self.session, user_id=uid, account_id=aid, task_id=self._nid("tsk"), comment_length=self.rng.randint(10, 300), event_at=ts, event_id=self._nid("evt"))
        elif kind == "task_completed":
            events.task_completed(self.session, user_id=uid, account_id=aid, task_id=self._nid("tsk"), project_id=f"prj_{aid}", hours_to_complete=self.rng.randint(1, 48), event_at=ts, event_id=self._nid("evt"))
        else:
            events.integration_connected(self.session, user_id=uid, account_id=aid, integration_type=choice(self.rng, cat.INTEGRATIONS), event_at=ts, event_id=self._nid("evt"))

    def _churn(self, aid: str, day: date) -> None:
        customer = self.session.query(BillingCustomer).filter(BillingCustomer.account_ref == aid).first()
        if customer is None:
            return
        sub = self.session.query(BillingSubscription).filter(BillingSubscription.customer_id == customer.customer_id, BillingSubscription.status == "active").order_by(BillingSubscription.id.desc()).first()
        if sub is not None:
            sub.status = "canceled"
            # clamp: ended_at must never precede the period's start
            sub.ended_at = max(datetime.combine(day, datetime.min.time()), sub.start_date)
            sub.source_updated_at = datetime.combine(day, datetime.min.time())

        # CRM lifecycle moves to churned
        company = self.session.query(CRMCompany).filter(CRMCompany.account_ref == aid).first()
        if company is not None:
            company.lifecycle_stage = "churned"
            company.source_updated_at = datetime.combine(day, datetime.min.time())

    def _expand(self, aid: str, day: date) -> None:
        customer = self.session.query(BillingCustomer).filter(BillingCustomer.account_ref == aid).first()
        if customer is None:
            return
        sub = self.session.query(BillingSubscription).filter(BillingSubscription.customer_id == customer.customer_id, BillingSubscription.status == "active").order_by(BillingSubscription.id.desc()).first()
        if sub is None:
            return
        # append a new period with more seats (expansion MRR)
        self.session.add(BillingSubscription(
            subscription_id=self._nid("sub"),
            customer_id=customer.customer_id,
            price_id=sub.price_id,
            status="active",
            seats=sub.seats + self.rng.randint(1, 5),
            start_date=datetime.combine(day, datetime.min.time()),
            recorded_at=datetime.combine(day, datetime.min.time()),
            effective_at=datetime.combine(day, datetime.min.time()),
        ))
        # mark the previous period as superseded (ended_at never before its start)
        sub.status = "superseded"
        sub.ended_at = max(datetime.combine(day, datetime.min.time()), sub.start_date)
