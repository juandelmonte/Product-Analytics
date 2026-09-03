# Operational Domain

The operational model is the source-of-truth for the simulated business. It
contains **only** the entities needed to generate the analytical data - nothing
extra. This is the schema behind the FastAPI source APIs and the target of the
simulation module.

## Entity model

| Entity | Table | Purpose | Key fields |
|--------|-------|---------|------------|
| Account | `accounts` | An organisation | account_id, name, country, industry, company_size, lead_source |
| User | `users` | A person with a login | user_id, account_id, email, role |
| Membership | `memberships` | A user's role in an account | membership_id, account_id, user_id, role, invited_at, joined_at |
| Workspace | `workspaces` | Top-level container | workspace_id, account_id, name |
| Project | `projects` | Unit of planned work | project_id, workspace_id, name |
| Task | `tasks` | Unit of execution | task_id, project_id, assignee_id, status, completed_at |
| Product event | `product_events` | Behavioural stream | event_id, event_name, distinct_id, account_id, event_at, properties |
| CRM contact | `crm_contacts` | Person in CRM | contact_id, company_id (nullable), email, lifecycle_stage |
| CRM company | `crm_companies` | Organisation in CRM | company_id, name, industry, company_size, country, lifecycle_stage |
| CRM deal | `crm_deals` | Sales opportunity | deal_id, company_id, deal_stage, amount, close_date |
| Billing customer | `billing_customers` | Billing identity | customer_id, email, name |
| Billing price | `billing_prices` | Catalog item | price_id, product_id, plan_code, unit_amount, billing_frequency |
| Billing subscription | `billing_subscriptions` | Recurring plan | subscription_id, customer_id, price_id, status, seats, effective_at |
| Billing invoice | `billing_invoices` | Charge | invoice_id, subscription_id, amount_due, status |

## Business rules

1. **Signup** - an account is created together with its first user (role
   `owner`), a CRM contact + company, and (for trials) a billing customer.
2. **Membership** - a user belongs to an account via a membership row; the
   `owner` role is the only one able to invite teammates.
3. **Activation** - an account is activated when it has, within 7 days of
   signup: a workspace, a project, a second membership, and a completed task
   (see `../business/business_case.md`).
4. **Plan lifecycle** - a subscription is `trialing` → `active` → `canceled`
   (or `past_due`). Plan/seat changes append a new subscription period with a
   future `effective_at`; they never rewrite history.
5. **Task lifecycle** - `open` → `done`; `completed_at` is set when done.
6. **CRM lifecycle** - a company moves `subscriber → lead → mql → sql →
   customer → churned`; stage changes mutate the row (SCD2 handled in dbt).

## Separation of concerns

- **Operational state** (this schema, PostgreSQL) is what the *business* writes.
- **Analytical state** (ClickHouse) is what dlt ingests and dbt transforms.
- The two schemas are deliberately different: the operational schema is
  normalised and mutable; the analytical schema is denormalised and
  append-only with explicit time semantics.

## Migration strategy

Alembic owns schema changes. The initial migration creates all tables. Future
changes (e.g. the planned `plan` → `plan_code` billing evolution in the
*source* shape) are handled at ingestion/dbt, not by migrating operational
tables.
