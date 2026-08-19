# Source Research

Concepts and behaviours extracted from the official docs of Mixpanel, HubSpot,
and Stripe — **only** what the simulation needs to mimic. We do not reproduce
their APIs; we model the structural ideas that make ingestion realistic.

> Sources consulted for concepts: Mixpanel Ingestion API / Identity Management /
> Export API; HubSpot CRM Objects / Properties / Associations / Webhooks;
> Stripe API (Customers, Products, Prices, Subscriptions, Invoices, Events).
> This document distils behaviour, not endpoints or payload schemas.

---

## 1. Mixpanel — product analytics

**Concepts adopted:**

| Concept | Mixpanel behaviour | What we simulate |
|---------|--------------------|------------------|
| Events | Named actions with a timestamp, `distinct_id`, and properties | `product_events` rows |
| Event properties | Free-form key/value attached to an event | JSON `properties` column |
| User identity | `distinct_id` (device-level) resolved to profiles | `user_id` + `account_id` on every event |
| Profiles | A user record with profile properties | `users` table |
| Groups / accounts | Group analytics keys (e.g. account) | `account_id` on events; `accounts` table |
| Timestamps | Client `time` (event time) vs server `received` (ingest time) | `event_at` vs `ingested_at` |
| Export | Batch/incremental export, ordered by time | Paginated, `updated_since` export API |

**Key behaviours we must preserve:**

- Events carry an event **time** and are received later → **late-arriving**.
- Events may be **delivered twice** (client retries) → **duplicates** with a
  stable `event_id`.
- `distinct_id` can change when a user is identified → **identity changes**.

## 2. HubSpot — CRM

**Concepts adopted:**

| Concept | HubSpot behaviour | What we simulate |
|---------|--------------------|------------------|
| Objects | Contacts, Companies, Deals are first-class objects | `crm_contacts`, `crm_companies`, `crm_deals` |
| Properties | Named fields per object | columns (e.g. `industry`, `company_size`, `lifecycle_stage`) |
| Associations | Objects link to each other (contact ↔ company) | `company_id` on contact (may be null) |
| Lifecycle stages | A company property (subscriber → lead → MQL → SQL → customer) | `lifecycle_stage` |
| Updates | Objects change over time, with `updated_at` | mutable records + `source_updated_at` |
| Incremental | "modified since" endpoints | `updated_since` query parameter |

**Key behaviours we must preserve:**

- CRM **properties are mutable** (e.g. `company_size`, `industry`,
  `lifecycle_stage`, `lead_source` change after creation).
- A changed record may only **become available days later** (sync lag).
- A contact may **initially have no company** association, and gain one later.

## 3. Stripe — billing

**Concepts adopted:**

| Concept | Stripe behaviour | What we simulate |
|---------|--------------------|------------------|
| Customers | Billing identity for an account | `billing_customers` |
| Products / Prices | Catalog; a price has an amount, currency, interval | `billing_prices` |
| Subscriptions | A customer's recurring plan; `status` (trialing/active/canceled) | `billing_subscriptions` |
| Subscription items | Seat/unit quantity on a subscription | `seats` on the subscription |
| Invoices | Charges produced by a subscription | `billing_invoices` |
| Lifecycle | `start_date`, `ended_at`, `canceled_at`, trial end | subscription history |
| Effective dates | Subscription changes take effect at a date (often future) | `effective_at` vs `recorded_at` |
| Incremental | `created` cursor / `updated` | `updated_since` query parameter |

**Key behaviours we must preserve:**

- Subscription **changes are future-effective** (recorded now, effective later).
- Subscriptions have a **history** (plan/seat changes append new periods).
- MRR requires **price × seats** with a billing **frequency** normalised to
  monthly.

## 4. Cross-system observations

- The three systems use **different identifiers** for the same account →
  canonical identity model (see `../analytics/identity_resolution.md`).
- All three expose **incremental extraction** by an "updated since" cursor.
- All three have distinct notions of **event time vs update time vs ingest
  time** — we preserve all three separately.
- **Standardisation** is needed where free-form source values vary
  (country, plan name, billing frequency).

## 5. What we deliberately do NOT model

- Full REST resource semantics, webhooks, OAuth, rate limits, or multi-org
  tenancy — these add no analytical value for the target questions.
- Mixpanel's full profile-merging engine — we model identity *mapping*, not
  resolution-as-a-service.
