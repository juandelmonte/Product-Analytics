# Analytics Solution Design Methodology

A reusable process for designing an analytics solution from scratch, for any
domain. The core principle:

> **Never move to the next layer until you understand what the previous layer
> requires.** Business first; technology last.

Each step below names the artifact it produces, and — because this repository is
the worked example of the methodology — links to the concrete file that
instantiates it here.

```text
                    ANALYTICS SOLUTION
                          │
        ┌─────────────────┼──────────────────┐
        ↓                 ↓                  ↓
     BUSINESS          SYSTEMS             DATA
        │                 │                  │
  Context            Boundaries          Requirements
  Processes          Interfaces          Models
  Questions          Ownership           Quality
  Decisions           Sources            Metrics
        │                 │                  │
        └─────────────────┼──────────────────┘
                          ↓
                    IMPLEMENTATION
                          │
             Ingestion → Transform
                          │
                    Orchestration
                          │
                          ↓
                     CONSUMPTION
                          │
                          ↓
                       BI / ML
```

---

## The 14-step flow

```
1.  Business context
2.  Business processes
3.  Business questions
4.  Metrics & semantics
5.  Source systems
6.  System boundaries & interfaces
7.  Data requirements
8.  Data architecture
9.  Transformation & modelling
10. Data quality
11. Orchestration & operations
12. BI / consumption
13. Validation
14. Iteration
```

---

## 1. Understand the business context

Establish:

- What does the company do?
- Who are its customers?
- How does it make money?
- What are the important business processes?
- Who will consume the analytics, and what decisions do they make?

**Output:** `business_context.md` — a one-page description of the business and
its operating model.

**In this repo:** [`../business/business_case.md`](../business/business_case.md).

## 2. Model the business processes

Don't think about tables yet. Ask: **what actually happens in the business?**

Identify: actors, entities, events, states, processes, lifecycle transitions.

```
Customer acquired → onboarded → uses product → pays → renews/churns
```

**Output:** `business_processes.md` — process diagrams. This is the *model of
reality*.

**In this repo:** [`../business/business_case.md`](../business/business_case.md)
(lifecycle) + [`../simulation/operational_domain.md`](../simulation/operational_domain.md)
(business rules).

## 3. Translate processes into business questions

Ask: **what would the business want to know about these processes?**

Start with *decisions*, not metrics.

| Business question | Decision supported | Priority |
|-------------------|--------------------|----------|
| Where do customers drop during onboarding? | Improve onboarding | P0 |
| How long does activation take? | Identify friction | P0 |
| Which features drive adoption? | Product prioritisation | P1 |

**Output:** `business_questions.md`.

**In this repo:** [`../business/business_questions.md`](../business/business_questions.md).

## 4. Define the semantic layer

Only now define metrics. For each question, descend:

```
Question → Concept → Metric → Definition → Grain → Dimensions → Time semantics
```

**Output:** `metric_dictionary.md` + `semantic_model.md`. The most important
artifacts in the methodology.

**In this repo:** [`../analytics/metric_dictionary.md`](../analytics/metric_dictionary.md)
+ [`../analytics/semantic_model.md`](../analytics/semantic_model.md).

## 5. Discover the source systems

Work backwards: **what data would have to exist to answer these questions?**
Then: **which system would realistically own that data?**

This prevents inventing columns because a dashboard needs them.

**Output:** `source_systems.md`.

**In this repo:** [`../simulation/operational_domain.md`](../simulation/operational_domain.md)
+ [`../simulation/event_catalogue.md`](../simulation/event_catalogue.md).

## 6. Research the actual systems

Investigate what a real system actually provides, for each source:

```
System, purpose, entities, identifiers, events, attributes,
relationships, timestamps, update semantics, incremental extraction,
API behaviour, known limitations
```

**Output:** `source_research.md` + `source_contracts.md`. Distinguishes
*realistic* from *made-up*.

**In this repo:** [`../simulation/source_research.md`](../simulation/source_research.md)
+ [`../simulation/source_contracts.md`](../simulation/source_contracts.md).

## 7. Define system boundaries

Move from business architecture to data architecture:

- Who owns this data?
- Where does it originate?
- What crosses a system boundary?
- What interface exposes it?

**Output:** `system_architecture.md` — ownership, interfaces, identifiers,
contracts, update semantics, failure modes.

**In this repo:** [`architecture.md`](architecture.md)
+ [`identity_resolution.md`](identity_resolution.md).

## 8. Derive the data requirements

For every analytical concept: `metric → required facts → required fields →
source → grain`. Build a traceability matrix:

| Metric | Required data | Source | Model |
|--------|---------------|--------|-------|
| Activation rate | signup + activation | Product | fct_activation |
| Paid conversion | activation + subscription | Product + Billing | fct_conversion |
| MRR | subscription + price | Billing | fct_mrr |

**Output:** `business_to_data_traceability.md`. One of the best portfolio
artifacts you can have.

**In this repo:** [`../analytics/business_to_data_traceability.md`](../analytics/business_to_data_traceability.md).

## 9. Design the analytical model

Design `source → staging → intermediate → core → marts`. Decide grains, facts,
dimensions, snapshots/history, identity resolution, SCDs, event and aggregate
models.

The key question: **what representation makes the business questions easy to
answer?** — not "what tables can I create?"

**Output:** `data_model.md` — ERD + model catalogue.

**In this repo:** [`../analytics/semantic_model.md`](../analytics/semantic_model.md)
+ [`warehouse_design.md`](warehouse_design.md).

## 10. Design data quality around reality

Don't add generic `NOT NULL` tests. Ask: **how can this business system
realistically produce incorrect analytical results?**

```
Operational reality → analytical consequence → engineering treatment → test
```

Data quality is *derived from system behaviour*.

**Output:** `data_quality.md`.

**In this repo:** [`../simulation/data_quality_scenarios.md`](../simulation/data_quality_scenarios.md)
+ [`data_quality_validation.md`](data_quality_validation.md).

## 11. Design the implementation architecture

Only now choose technologies. The choice should **follow** the architecture,
not precede it. Document why each component exists, its responsibility,
interface, dependencies and operational behaviour.

**Output:** `technical_architecture.md`.

**In this repo:** [`architecture.md`](architecture.md)
+ [`warehouse_design.md`](warehouse_design.md)
+ [`ingestion_design.md`](ingestion_design.md)
+ [`orchestration_design.md`](orchestration_design.md)
+ [`decisions/architecture-decisions.md`](decisions/architecture-decisions.md).

## 12. Build vertically

Don't build every layer for weeks before proving anything. Build one
**vertical analytical slice** at a time:

```
Business question → Source → Ingestion → Transformation → Metric → Validation
```

Validate continuously (e.g. Signup → Activation, then Adoption → Retention,
then Subscription → MRR).

## 13. Validate the analytical result

Three levels:

- **Technical** — tests, schemas, relationships, freshness, uniqueness.
- **Data** — duplicates, late events, missing relationships, invalid states.
- **Business** — does the metric make sense? Manually inspect a few entities
  and verify the calculation.

## 14. Consumption, then iterate

Build the BI layer last — it is a *view of the analytical model*, not the
thing driving the model. The methodology is iterative: discoveries push you
back up (e.g. "this metric sounds useful, but the source doesn't provide the
data"). That is good analytics engineering, not failure.

---

## Reusable artifacts (10)

The canonical output names, and where each lives in **this repository**:

```
01 business_context.md        → docs/business/business_case.md
02 business_processes.md      → docs/business/business_case.md + docs/simulation/operational_domain.md
03 business_questions.md      → docs/business/business_questions.md
04 metric_dictionary.md       → docs/analytics/metric_dictionary.md (+ semantic_model.md)
05 source_research.md         → docs/simulation/source_research.md (+ source_contracts.md)
06 system_architecture.md     → docs/engineering/architecture.md (+ identity_resolution.md)
07 business_to_data_traceability.md → docs/analytics/business_to_data_traceability.md
08 data_model.md              → docs/analytics/semantic_model.md + docs/engineering/warehouse_design.md
09 data_quality.md            → docs/simulation/data_quality_scenarios.md + docs/engineering/data_quality_validation.md
10 technical_architecture.md  → docs/engineering/{architecture, warehouse_design, ingestion_design, orchestration_design, decisions/}.md
```

For small projects, combine several into fewer files. The important thing is
the **sequence of reasoning**:

> **Business → Process → Question → Metric → Source → Boundary → Data → Model →
> Quality → Implementation → BI**
