# Business Case

## Product: TaskFlow

**TaskFlow** is a B2B SaaS project/task-management tool. Teams organise work in
workspaces, plan deliverables as projects, and execute them as tasks.

This is the smallest product that still supports every analytical question the
platform must answer: activation, adoption, journeys, conversion, retention,
churn, and MRR expansion - all of which map naturally onto the core loop
*workspace → project → task* and a seat-based subscription.

## The operational model (summary)

| Entity          | What it represents                                              |
|-----------------|-----------------------------------------------------------------|
| `account`       | A paying (or trialling) organisation                            |
| `user`          | A person with a login                                           |
| `membership`    | A user's role within an account (owner/admin/member)            |
| `workspace`     | The top-level container an account works in                     |
| `project`       | A unit of planned work inside a workspace                       |
| `task`          | A unit of execution inside a project                            |
| `plan`          | A product tier (free / trial / pro / enterprise)                |
| `subscription`  | An account's active plan and its seat count                     |
| product events  | The behavioural stream (signups, invites, project/task actions) |
| CRM records     | contacts, companies, deals - the sales/renewal view             |
| billing records | customers, prices, subscriptions, invoices - the money view     |

## Lifecycle

1. **Acquisition → Signup** - a visitor creates an account (company) and the
   first user. This produces an `account_created` + `user_signup` event, a CRM
   contact + company, and (for trials) a billing customer.
2. **Onboarding → Activation** - the account configures a workspace, creates a
   project, invites a teammate, and completes the first task. **Activation is
   defined below**; failing onboarding means the account stalls before reaching
   it.
3. **Product adoption** - teams use the features: creating tasks, assigning,
   commenting, completing, integrating.
4. **Paid conversion** - a trial/free account picks a paid plan (via a CRM deal
   → billing subscription).
5. **Retention / churn** - active usage over time; churn = subscription
   cancellation (voluntary or lapse).
6. **Expansion / MRR** - adding seats or upgrading plans increases MRR.

## Activation definition (locked)

An account is **activated** when, within **7 days** of signup, it has:

1. created at least one **workspace**,
2. created at least one **project**,
3. invited at least one **teammate** (membership count ≥ 2), and
4. completed at least one **task**.

The **activation moment** is the timestamp of the last of those four actions to
occur. `time_to_activation` is measured from account signup to activation
moment, in days.

## Personas

- **Product team** - asks activation/adoption/retention questions to steer the
  onboarding and feature roadmap.
- **Growth / marketing** - asks acquisition and funnel questions.
- **Sales / CS** - asks conversion, churn, and expansion questions.

## Why this needs an analytics platform

Each persona's questions span three *separate* source systems (product events,
CRM, billing) that use **different identifiers** for the same real-world
account. There is no single source of truth; the answers must be assembled by
joining product behaviour to CRM lifecycle to billing revenue. That joining is
exactly what the warehouse, the canonical identity model, and the semantic
layer deliver.
