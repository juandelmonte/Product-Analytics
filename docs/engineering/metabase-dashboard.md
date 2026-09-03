# Metabase Dashboard - Build Guide

This guide describes the self-serve Metabase dashboard that **you** will build
by hand (Metabase configuration is click-driven and lives in its own database,
not in this repo). The Evidence report in this repo is the *curated narrative*;
Metabase is the *self-serve exploration* surface for business users.

Together they demonstrate the two halves of a real BI strategy:

| Surface | Tool | Who | Where |
|---------|------|-----|-------|
| Curated narrative report | Evidence | stakeholders, execs | this repo (`evidence/`) |
| Self-serve exploration | Metabase | business users | built following this guide |

Both read the **same mart tables** in ClickHouse `marts`, and both defer to the
**same metric definitions** in
[`docs/analytics/metric_dictionary.md`](/docs/analytics/metric_dictionary.md).

---

## 1. Connect Metabase to ClickHouse

1. Run Metabase (a local Docker one-liner is enough):

   ```powershell
   docker run -d --name metabase -p 3001:3000 metabase/metabase
   ```

   (Port 3001 is used here because Evidence already takes 3000.)

2. Open `http://localhost:3001`, create the admin account.

3. **Admin → Databases → Add database**, choose **ClickHouse**, and fill in:

   | Field | Value |
   |-------|-------|
   | Name | `Analytics Marts` |
   | Host | `clickhouse` (or `localhost` if Metabase runs on the host) |
   | Port | `8123` |
   | Database | `marts` |
   | User | `default` |
   | Password | *(empty for the local stack)* |

   > If Metabase runs in a separate Docker container, put it on the same
   > network as the stack (`docker network connect saas-analytics_default
   > metabase`) and use host `clickhouse`.

4. **Save** and verify Metabase can browse the `marts` tables.

---

## 2. Expose the mart tables to business users

Create **Models** (Metabase's governed query layer) for the tables business
users actually need, with friendly names and descriptions pulled from the
metric dictionary:

| Model | Underlying table | Description (from metric dictionary) |
|-------|------------------|---------------------------------------|
| Accounts | `fct_user_activation` | One row per account: signup, activation, time-to-activation |
| Account journey | `fct_user_journey` | One row per account: each onboarding milestone reached |
| Daily activity | `fct_user_daily_activity` | One row per user × day: events, active flag |
| Feature adoption | `fct_feature_adoption` | One row per feature × week: adoption rate |
| Paid conversion | `fct_paid_conversion` | One row per account: converted flag |
| Retention | `fct_retention` | One row per cohort × week offset: retention rate |
| Churn | `fct_churn` | One row per month: churn rate |
| MRR | `fct_account_mrr` | One row per account × month: MRR, expansion |
| Usage & expansion | `fct_usage_expansion` | One row per account × month: usage + expansion flags |
| Product events | `fct_product_events` | One row per event |

For each model, set **metadata** (description, column descriptions) from
`docs/analytics/metric_dictionary.md` so the definitions live in one place and
Metabase displays them consistently.

---

## 3. Build the dashboards

Three dashboards mirroring the three persona groups:

### 3a. Executive dashboard

- **KPI cards**: total accounts, activation rate, paid conversion, latest MRR
  (same SQL as `evidence/queries/kpis.sql`).
- **Onboarding funnel** (same SQL as `evidence/queries/onboarding_funnel.sql`).
- **MRR trend** (`mrr_overview.sql`).

### 3b. Product dashboard

- **Activation rate over time** (`activation_rate.sql`).
- **Time-to-activation distribution** (`time_to_activation_distribution.sql`).
- **Feature adoption** (`feature_adoption.sql`, `feature_adoption_trend.sql`).
- **DAU / WAU stickiness** (`dau_wau.sql`).

### 3c. Commercial dashboard

- **Paid conversion by activation / engagement** (`paid_conversion.sql`,
  `conversion_by_engagement.sql`).
- **Retention cohorts** (`retention_cohort.sql`).
- **Churn overview** (`churn_overview.sql`).
- **Expanding accounts** (`expansion_accounts.sql`).

Every card's SQL is available, ready to paste, in `evidence/queries/*.sql` -
this is deliberate: the SQL is **written once, reused in two BI surfaces**.

---

## 4. Keep definitions consistent

- The metric dictionary (`docs/analytics/metric_dictionary.md`) is the **single
  source of truth**. When adding a Metabase card, copy the metric's formula and
  grain verbatim into the card's description.
- If a metric definition changes, update the dictionary first, then the Evidence
  SQL, then the Metabase card - in that order.
- Do **not** define metrics inline in Metabase that aren't in the dictionary.

---

## 5. Documenting the result (for the portfolio)

Because Metabase configuration isn't version-controlled, capture it for the
repo with:

1. **Screenshots** of each dashboard (save under `docs/images/metabase/`).
2. A short note in this file (or a `metabase.md` update) listing what was
   built and when.
3. Optionally export a JSON snapshot of the dashboards (Metabase supports
   admin serialization) and commit it for reproducibility.

That keeps the "config is code" story intact for Evidence and dbt, while Metabase
is honestly documented as a click-driven tool over the same governed marts.
