# Metric Dictionary

Every metric that appears in a mart is defined here with: **Definition**,
**Formula**, **Grain**, **Time semantics**, **Dimensions**, and **Required
source data**. No metric exists without a business purpose (mapped in
`../business/business_questions.md`) and a traceable source (mapped in
`business_to_data_traceability.md`).

---

## 1. New Users

- **Definition**: number of distinct users who signed up in a period.
- **Formula**: `count(distinct user_id)` over `user_signup` events.
- **Grain**: one row per calendar day (or week/month), per segment.
- **Time semantics**: event time (`event_at`); assigned to the day the signup
  actually happened, not the day it was ingested.
- **Dimensions**: country, plan at signup, acquisition channel (lead_source).
- **Required source data**: product events `user_signup` (user_id, account_id,
  event_at, properties).

## 2. New Accounts

- **Definition**: number of distinct accounts created in a period.
- **Formula**: `count(distinct account_id)` over `account_created` events (or
  the accounts table `created_at`).
- **Grain**: calendar day / week / month.
- **Time semantics**: event time (`event_at`).
- **Dimensions**: country, plan at creation, industry (from CRM company).
- **Required source data**: product events `account_created`; CRM `company`
  (industry, country).

## 3. Activation Rate

- **Definition**: share of new accounts that become activated.
- **Formula**: `activated_accounts / new_accounts`, per signup cohort.
- **Grain**: one row per account cohort (cohort = signup week/day).
- **Time semantics**: activation is attributed to the **signup cohort**,
  regardless of when activation completes.
- **Dimensions**: plan, country, acquisition channel.
- **Required source data**: `account_created` (cohort anchor) + the four
  activation signals (workspace created, project created, membership added,
  task completed).

## 4. Time to Activation

- **Definition**: elapsed time from account signup to the activation moment.
- **Formula**: `activation_at − signup_at`, in days; reported as median and
  distribution (p25/p50/p90).
- **Grain**: one row per activated account.
- **Time semantics**: both timestamps are event times; null if never activated.
- **Dimensions**: plan, country.
- **Required source data**: signup timestamp + the four activation event
  timestamps (the activation moment = `max` of the four).

## 5. Onboarding Funnel Conversion

- **Definition**: step-wise conversion through the onboarding funnel:
  Signup → Workspace created → Project created → Teammate invited → First task
  completed.
- **Formula**: at each step, `count(distinct accounts reaching step) /
  count(distinct accounts at first step)` (and step-to-step `N / N−1`).
- **Grain**: one row per funnel step per cohort.
- **Time semantics**: event time within the activation window (7 days from
  signup); late-arriving events are backfilled.
- **Dimensions**: plan, country, cohort.
- **Required source data**: `user_signup`, `workspace_created`,
  `project_created`, `membership_invited` (or membership record),
  `task_completed`.

## 6. DAU / WAU

- **Definition**: Daily Active Users and Weekly Active Users.
- **Formula**: `count(distinct user_id)` with a product activity event on the
  day (DAU) or any day in the trailing 7 days (WAU).
- **Grain**: one row per calendar day.
- **Time semantics**: event time; DAU/WAU ratio uses a rolling window.
- **Dimensions**: plan, role, country.
- **Required source data**: any qualifying product event (activity events only -
  see event catalogue).

## 7. Feature Adoption Rate

- **Definition**: share of accounts (or users) that used a given feature at
  least once in a period.
- **Formula**: `count(distinct accounts with feature event) / count(distinct
  active accounts)`.
- **Grain**: one row per feature per week/month.
- **Time semantics**: event time; "active accounts" = accounts with any
  activity event in the same window.
- **Dimensions**: feature, plan, account size.
- **Required source data**: product events keyed by feature (see event
  catalogue for the feature mapping).

## 8. Paid Conversion Rate

- **Definition**: share of accounts that convert to a paid plan.
- **Formula**: `count(distinct accounts with a paid subscription) /
  count(distinct accounts)`, optionally split by activation status or
  starting plan (free vs trial).
- **Grain**: one row per cohort (signup week/month) per segment.
- **Time semantics**: conversion attributed to the signup cohort; a conversion
  counts on the effective date the paid subscription starts.
- **Dimensions**: activation status, engagement segment, starting plan.
- **Required source data**: billing `subscription` (plan, effective dates) +
  activation mart.
- **Note**: conversion is **not** conditional on activation. Accounts can start
  on a free or trial plan and upgrade to paid even if they never fully
  activated - activation merely makes conversion far more likely.

## 8b. Engagement segment

Used as a dimension on conversion, retention and churn. An account's segment is
its total product activity over its lifetime, bucketed as:

| Segment | Total events (lifetime) |
|---------|-------------------------|
| low | < 10 |
| medium | 10 – 49 |
| high | ≥ 50 |

Engagement is a *behavioural* dimension (not a plan/status dimension): it
measures how much the account actually used the product, independent of
activation or billing status.

## 9. Retention Rate

- **Definition**: share of a signup cohort still active N weeks later.
- **Formula**: `count(distinct cohort members active in week N) / count(distinct
  cohort members)`.
- **Grain**: one row per cohort × week offset.
- **Time semantics**: cohort = signup week; "active in week N" = any product
  activity event in that calendar week.
- **Dimensions**: activation status, plan, country.
- **Required source data**: product activity events + signup cohort + activation.

## 10. Churn Rate

- **Definition**: share of active subscribers that cancel in a period.
- **Formula**: `count(distinct accounts whose subscription cancelled in period)
  / count(distinct accounts with an active subscription at period start)`.
- **Grain**: one row per calendar month.
- **Time semantics**: cancellation attributed to the effective date the
  subscription ended.
- **Dimensions**: plan, usage segment (pre-churn), tenure.
- **Required source data**: billing `subscription` (start/end/status) + usage.

## 11. MRR (Monthly Recurring Revenue)

- **Definition**: normalised monthly revenue from active subscriptions.
- **Formula**: `sum(seat_count × seat_price)` over active subscriptions,
  normalised to monthly units for non-monthly billing frequencies.
- **Grain**: one row per account per month (and one per month for totals).
- **Time semantics**: attributed to the effective subscription period; a change
  (seat/plan) creates a new MRR line from its effective date.
- **Dimensions**: plan, account size, country.
- **Required source data**: billing `subscription` + `price` (seat price,
  billing frequency).

## 12. Expansion MRR

- **Definition**: increase in MRR from existing accounts (upgrades + seat
  additions), excluding new business.
- **Formula**: `sum(positive month-over-month MRR change)` for accounts that
  were already paying in the prior month.
- **Grain**: one row per account per month.
- **Time semantics**: change attributed to the effective month of the plan/seat
  change.
- **Dimensions**: plan, reason (seat add vs upgrade).
- **Required source data**: billing `subscription` history + usage (to explain
  *why* accounts expand).
