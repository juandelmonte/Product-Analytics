# Business → Data Traceability

Every metric in `metric_dictionary.md` must be traceable to a concrete source
field or event, and every source field/event must be traceable to an
operational process. This document pins that chain in both directions.

## Metric → source

| Metric | Source system | Source field(s) / event(s) |
|--------|---------------|-----------------------------|
| New Users | product | event `user_signup` → `user_id`, `event_at` |
| New Accounts | product / CRM | event `account_created` / company `created_at` |
| Activation Rate | product | `account_created` + `workspace_created` + `project_created` + `membership` record + `task_completed` |
| Time to Activation | product | timestamps of the four activation signals + signup |
| Funnel Conversion | product | `user_signup`, `workspace_created`, `project_created`, `membership_invited`, `task_completed` |
| DAU/WAU | product | any activity event (`event_at`, `user_id`) |
| Feature Adoption | product | activity events grouped by `feature_code` |
| Paid Conversion | billing + product | `subscription` (plan, effective dates) + activation |
| Retention | product | activity events + signup cohort |
| Churn | billing + product | `subscription` (status, ended_at) + usage |
| MRR | billing | `subscription` (seats) + `price` (seat price, frequency) |
| Expansion MRR | billing | `subscription` history (seat/plan changes) |

## Source field/event → operational process

| Source field/event | Operational process that produces it |
|--------------------|---------------------------------------|
| `user_signup` | User completes signup form |
| `account_created` | Account provisioned after signup |
| `workspace_created` | First user names and creates a workspace |
| `project_created` | User creates a project |
| `membership_invited` / membership row | Account owner invites a teammate |
| `task_completed` | A user marks a task done |
| CRM `company` / `contact` / `deal` | Sales creates/updates records (new biz, renewal) |
| CRM `lifecycle_stage` | Sales moves a company through the funnel |
| billing `customer` | Account created in billing at signup/trial start |
| billing `subscription` | A plan is activated or changed |
| billing `price` | Product catalog defines seat price + frequency |
| billing `invoice` | Billing generates a charge for a subscription |

## Traceability tests

The following checks are enforced in the warehouse (dbt tests) to keep the
chain honest:

1. Every metric mart can be joined back to a staging model, and every staging
   model to a bronze table (lineage is visible in dbt docs).
2. No mart reads bronze directly — the staging → core → marts layering is the
   enforced path.
3. Late-arriving, duplicate, mutable, and future-effective records are handled
   at staging so measures always attribute to the correct `event_at` /
   `effective_at` (see `../simulation/data_quality_scenarios.md`).

## Deliberately excluded

Metrics without a supported source are not implemented. Current exclusions:
- **Time-to-value per feature** — requires per-feature first-use timestamps the
  simulation does not currently model distinctly from adoption; noted for a
  future iteration if the event catalogue is extended.
