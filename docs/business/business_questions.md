# Business Questions

Prioritised questions the platform must answer, grouped by the five core areas
from the brief. Each question is marked with the metric(s) that answer it (see
`../analytics/metric_dictionary.md`) and whether it is **P0** (must be answerable from the
marts) or **P1** (should be, if supported by the simulated data).

## Activation

| ID | Question | Metric(s) | Priority |
|----|----------|-----------|----------|
| A1 | Where do users drop during onboarding? | Onboarding Funnel Conversion (per step) | P0 |
| A2 | What constitutes activation? | Activation definition (documented) | P0 |
| A3 | What is the activation rate? | Activation Rate | P0 |
| A4 | How long does activation take? | Time to Activation (median, distribution) | P0 |

## Adoption

| ID | Question | Metric(s) | Priority |
|----|----------|-----------|----------|
| D1 | Which features are adopted? | Feature Adoption Rate (per feature) | P0 |
| D2 | How does usage vary across users/accounts? | Feature Adoption, DAU/WAU by segment | P0 |
| D3 | What are common user journeys? | Journey conversion (event-sequence) | P0 |

## Conversion

| ID | Question | Metric(s) | Priority |
|----|----------|-----------|----------|
| C1 | Do activated users convert to paid? | Paid Conversion Rate (activated vs not) | P0 |
| C2 | How does product behaviour relate to conversion? | Paid Conversion Rate by engagement segment | P0 |

## Retention

| ID | Question | Metric(s) | Priority |
|----|----------|-----------|----------|
| R1 | How does retention vary by cohort? | Retention Rate (weekly cohort) | P0 |
| R2 | Are activated users more likely to remain active? | Retention Rate by activation status | P0 |

## Churn / Expansion

| ID | Question | Metric(s) | Priority |
|----|----------|-----------|----------|
| E1 | What product behaviour precedes churn? | Churn Rate by usage segment | P0 |
| E2 | Which accounts expand? | Expansion MRR (account-level) | P0 |
| E3 | How does product usage relate to MRR? | MRR by usage segment | P0 |

## Guardrail

Only implement questions whose required source data exists in the simulation.
A question is dropped (and documented) if its data cannot be traced to a source
source field or event (see `../analytics/business_to_data_traceability.md`).
