# Documentation

Everything in this repository is documented in this folder. Pick your entry
point by **who you are**, then follow the pointers.

## Audience map

| You are… | You care about… | Start here |
|----------|-----------------|------------|
| **Hiring manager / reviewer** | What was built, why, and the result | `README.md` (repo root) |
| **Business user of the BI layer** | What the metrics mean, how the data is modelled | [`analytics/`](#analytics---the-analytical-model) |
| **Developer / analyst joining the project** | How to run it and how it is built | [`engineering/`](#engineering---how-it-is-built) |
| **Curious about the data source** | How the source systems were modelled | [`simulation/`](#simulation---the-source-systems) |

---

## business/ - the business context

The *why* of the project. These two documents are the foundation of the whole
solution and the first thing any reader should see after the README.

| Doc | What it explains |
|-----|------------------|
| [`business_case.md`](business/business_case.md) | The SaaS product, its lifecycle, and the locked activation definition |
| [`business_questions.md`](business/business_questions.md) | The prioritized business questions the platform answers |

These belong to the **business**, not the source-system setup - the source
systems exist only so the analytics solution has realistic data to work with.

---

## analytics/ - the analytical model

The *what the data means* layer. This is the contract between the warehouse and
the BI layer, and the reference for anyone consuming the marts or the Evidence
report.

| Doc | What it explains |
|-----|------------------|
| [`semantic_model.md`](analytics/semantic_model.md) | Entities, measures, relationships, time semantics |
| [`metric_dictionary.md`](analytics/metric_dictionary.md) | Every metric: definition, formula, grain, dimensions, source |
| [`business_to_data_traceability.md`](analytics/business_to_data_traceability.md) | Metric → source → process chain (the trust chain) |

> A business user reading the BI dashboard should be able to answer *"what does
> this number mean and where does it come from?"* using **only** this folder.

---

## engineering/ - how it is built

The *how* for developers and analysts. Architecture, design process, and the
hardened implementation details.

| Doc | What it explains |
|-----|------------------|
| [`methodology.md`](engineering/methodology.md) | The reusable 14-step solution design process |
| [`architecture.md`](engineering/architecture.md) | System diagram + layer responsibilities |
| [`getting-started.md`](engineering/getting-started.md) | How to run the full pipeline (developer quick start) |
| [`warehouse_design.md`](engineering/warehouse_design.md) | Medallion layers + source() contract |
| [`identity_resolution.md`](engineering/identity_resolution.md) | Canonical identity mapping across the 3 systems |
| [`ingestion_design.md`](engineering/ingestion_design.md) | dlt pipelines + watermarks |
| [`orchestration_design.md`](engineering/orchestration_design.md) | Airflow DAGs (orchestration-only) |
| [`data_quality_validation.md`](engineering/data_quality_validation.md) | Per-scenario verification results |
| [`hardening.md`](engineering/hardening.md) | Clean-install + idempotency verification |
| [`vps-deployment.md`](engineering/vps-deployment.md) | Deploy the full stack on a VPS (expose dbt docs + Evidence) |
| [`decisions/architecture-decisions.md`](engineering/decisions/architecture-decisions.md) | Architecture Decision Records |

---

## simulation/ - the source systems

The operational systems the analytics platform consumes. They were modelled
after **Mixpanel, HubSpot, and Stripe** - their identifiers, update semantics,
and failure modes researched first, then reproduced - so the analytics solve
**realistic** problems (late events, duplicates, three identifier namespaces)
rather than clean toy data. This is the *input* to the analytics solution, kept
deliberately separate from it.

| Doc | What it explains |
|-----|------------------|
| [`operational_domain.md`](simulation/operational_domain.md) | Operational schema + business rules |
| [`source_research.md`](simulation/source_research.md) | Mixpanel/HubSpot/Stripe concepts adopted |
| [`source_contracts.md`](simulation/source_contracts.md) | Source API contracts (the spec dlt consumes) |
| [`event_catalogue.md`](simulation/event_catalogue.md) | Product event taxonomy |
| [`simulation_model.md`](simulation/simulation_model.md) | Deterministic simulation design |
| [`data_quality_scenarios.md`](simulation/data_quality_scenarios.md) | The 9 deliberate data-quality problems |
