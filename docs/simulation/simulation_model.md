# Simulation Model

The simulation is the **operational engine** behind the source APIs. It generates
a deterministic, business-driven history and advances one day at a time.

## Core properties

- **Deterministic**: seeded from `SEED` (env). The same seed reproduces the
  identical 24-month history (validated: 1385 events for 30 days, 2 runs).
- **Append-only**: history is never regenerated. Each day only appends records
  or updates mutable source rows (CRM, billing), exactly as a real system would.
- **Business-driven**: events are emitted by business actions (signup, create
  project, complete task), never disconnected from a process.
- **Day-driven**: a single `advance_day()` code path is shared by history and
  daily runs, so both behave identically.

## The day loop

```
advance_day():
  1. deliver sim_pending rows due today   (late events, duplicates, CRM updates,
                                            future-effective billing changes)
  2. generate today's organic business:
     - new signups/accounts (1..4/day)
     - onboarding/activation for new activated accounts
     - daily product activity for existing activated accounts
     - monthly churn / expansion for paying accounts
  3. bump sim_date, persist
```

## Populations modelled

| Population | How it is produced |
|------------|--------------------|
| Activated users | ~70% of new accounts complete the 5-step activation flow (progressive per-step dropout: workspace 98% → project 91% → invite 94% → task 93% → completed 90%) |
| Failed onboarding | the remainder - accounts that drop at any funnel step, most commonly before the first project |
| Highly engaged | activated accounts with high daily event counts |
| Low engagement | activated accounts with few/no daily events |
| Free/trial users | ~60% of accounts start on `free`, the rest on `trial` (`P_FREE = 0.60`) |
| Converted users | ~35% of activated accounts convert to `pro`; non-activated accounts convert at ~6% |
| Retained users | converted accounts that stay active (no churn) |
| Churned users | ~5%/month of paying accounts cancel |
| Expanding accounts | ~14%/month of paying accounts add seats |
| Different account sizes | seats 1..10 on subscription; company_size varies |

## Segment behaviour

Account attributes are **not** cosmetic - they drive behaviour, so dimensional
slices of the marts are non-uniform (realistic). Each account's `country`,
`industry`, and `company_size` scale the global probabilities:

| Multiplier | Applies to | Direction |
|-----------|-----------|-----------|
| `fit` (product-market fit) | onboarding funnel completion + paid conversion | higher for SaaS / Finance / Healthcare, larger companies, US |
| `expand` (expansion appetite) | monthly expansion likelihood | higher for SaaS / E-commerce / Media, larger companies |
| `stickiness` (retention) | churn + dormancy | higher for Finance / Healthcare / Education, larger, CA/GB |

Concretely: a `1000+` SaaS account in the US converts and expands far more and
churns less than a `1-10` Media account in CA - which is what makes the
activation-by-country/industry/size and MRR-by-size analyses interesting rather
than flat.

## Determinism & the pending queue

- Each day's random draws use a **per-day seed** = `f(SEED, day_index)`, so a
  day's output depends only on `(SEED, day_index)`, not on how many prior days
  ran. This makes `advance_day` idempotent and history reproducible.
- Delayed records are stored in `sim_pending` with a `delivery_date`. Both
  history and daily advance deliver whatever is due that day. Late-arriving
  events, duplicate deliveries, late CRM updates, and future-effective billing
  changes all flow through this queue.

## Entry points

```
python -m app.sim history [--days 720]   # init + generate N days
python -m app.sim day                    # advance one day (append-only)
python -m app.sim reset                  # drop + recreate operational schema
```

## Tuning

Probabilities live at the top of `simulator.py` (e.g. `P_PROJECT_GIVEN_WORKSPACE
= 0.91`, `P_CONVERT_ACTIVATED = 0.35`). They are chosen so the metrics are
statistically visible but not uniform; each is a business-behaviour knob, not a
data generator.
