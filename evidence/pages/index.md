---
title: Business Report
sidebar_position: 1
---

# Business Report

Answers to the business case and business questions, computed live from the
marts (ClickHouse). Metric definitions: [`docs/analytics/metric_dictionary.md`](/docs/analytics/metric_dictionary.md).

## Executive summary

{% row %}
    {% big_value data="/queries/kpis" value="total_accounts" fmt="num0" title="Total accounts" /%}
    {% big_value data="/queries/kpis" value="activation_rate" fmt="pct1" title="Activation rate" /%}
    {% big_value data="/queries/kpis" value="paid_conversion_rate" fmt="pct1" title="Paid conversion" /%}
    {% big_value data="/queries/kpis" value="latest_month_mrr" fmt="usd0" title="Latest MRR" /%}
{% /row %}

The simulated B2B SaaS business has {% value data="/queries/kpis" value="total_accounts" fmt="num0" /%}
accounts and {% value data="/queries/kpis" value="total_events" fmt="num0" /%}
product events across 24 months.

Two patterns stand out:

1. **Onboarding is a progressive leak** - the steepest step is *workspace
   created* → *first project created*, with smaller drop-offs at every later
   step.
2. **Activation strongly predicts monetisation** - activated accounts convert
   at ~5× the rate of non-activated accounts, but conversion is **not** gated
   on it (see §3).

---

## 1. Activation - *where do users drop, and how fast do they activate?*

### A1. Where do users drop during onboarding?

The onboarding funnel, in journey order (definition:
`docs/analytics/metric_dictionary.md` §5). The steepest drop-off is at
**workspace → project**, but every step loses a small share of accounts - the
funnel is a *gradual* slope, not a single cliff.

{% funnel_chart
    data="/queries/onboarding_funnel"
    category="step"
    value="accounts"
    show_percent=true
    title="Onboarding funnel"
/%}

```sql funnel_table
select step, accounts from {{ "/queries/onboarding_funnel" }}
```

{% table data="funnel_table" /%}

### A2. What constitutes activation?

Activation = reaching all four milestones **within 7 days of signup**: created
a workspace, created a project, invited a teammate, completed a task. The
activation moment is the last of the four. (Definition locked in
`docs/business/business_case.md`.)

### A3. What is the activation rate?

The activation rate is {% value data="/queries/kpis" value="activation_rate" fmt="pct1" /%}
- {% value data="/queries/kpis" value="activated_accounts" fmt="num0" /%} of
{% value data="/queries/kpis" value="total_accounts" fmt="num0" /%} accounts.

{% line_chart
    data="/queries/activation_rate"
    x="cohort"
    y="activation_rate"
    y_fmt="pct"
    title="Activation rate by signup week"
/%}

### A4. How long does activation take?

{% row %}
    {% big_value data="/queries/time_to_activation" value="p50_days" fmt="num" title="Median days to activate" /%}
    {% big_value data="/queries/time_to_activation" value="p25_days" fmt="num" title="P25 (days)" /%}
    {% big_value data="/queries/time_to_activation" value="p90_days" fmt="num" title="P90 (days)" /%}
    {% big_value data="/queries/time_to_activation" value="activated_accounts" fmt="num0" title="Activated accounts" /%}
{% /row %}

Most accounts that activate do so within the first couple of days; the P90 at
~6 days confirms the 7-day window is well-calibrated.

{% bar_chart
    data="/queries/time_to_activation_distribution"
    x="time_to_activation_days"
    y="accounts"
    title="Time-to-activation distribution"
/%}

---

## 2. Adoption - *which features are used, and what do journeys look like?*

### D1. Which features are adopted?

{% bar_chart
    data="/queries/feature_adoption"
    x="feature_code"
    y="avg_adoption_rate"
    y_fmt="pct"
    order="avg_adoption_rate desc"
    title="Feature adoption rate"
/%}

The **core task loop** (`tasks`, `comments`, `integrations`) dominates
day-to-day usage; `workspace` and `projects` are one-time setup actions, which
is why their *rate* looks low.

### D2. How does usage vary across users/accounts?

Daily active users average {% value data="/queries/dau_wau" value="avg(dau)" fmt="num0" /%}
per day. **DAU/WAU stickiness** - the share of the weekly audience active on a
given day - averages {% value data="/queries/dau_wau" value="avg(stickiness)" fmt="pct" /%}.

Two charts, because the two metrics live on different scales:

{% line_chart
    data="/queries/dau_wau"
    x="activity_date"
    y=["dau", "wau"]
    title="Daily vs weekly active users"
    subtitle="The weekly rhythm is the story: DAU dips every weekend while WAU stays flat."
/%}

{% line_chart
    data="/queries/dau_wau"
    x="activity_date"
    y="stickiness"
    y_fmt="pct"
    title="DAU/WAU stickiness"
    subtitle="The repeating 7-day pattern is the work-week effect: ~65–73% on weekdays, ~28–30% on weekends."
/%}

### D3. What are common user journeys?

The canonical journey **Signup → Workspace → Project → Teammate invited →
Task created → Task completed** (see the funnel in §A1) shows a progressive,
step-by-step leak: the biggest single drop is at workspace → project, with
smaller losses at every later step.

---

## 3. Conversion - *who converts to paid, and why?*

### C1. Do activated users convert to paid?

{% bar_chart
    data="/queries/paid_conversion"
    x="is_activated"
    y="conversion_rate"
    y_fmt="pct"
    title="Paid conversion by activation status"
/%}

Accounts start on a **free or trial** plan and a share later upgrades to paid
(see `docs/analytics/metric_dictionary.md` §8 - conversion is **not**
conditional on activation). Activation is a **strong predictor** of conversion
(~5× more likely), but not a hard gate: a small but real share of accounts
upgrades even without fully activating.

### C2. How does product behaviour relate to conversion?

{% bar_chart
    data="/queries/conversion_by_engagement"
    x="engagement_segment"
    y="conversion_rate"
    y_fmt="pct"
    title="Paid conversion by engagement segment"
/%}

**Engagement segment** buckets accounts by lifetime product activity
(`docs/analytics/metric_dictionary.md` §8b): low (<10 events), medium (10–49),
high (≥50). Engagement and conversion are **positively correlated, but not
linear**: the jump from *"almost no usage"* to *"some usage"* is the meaningful
threshold.

---

## 4. Retention - *how does retention vary by cohort and activation?*

### R1. How does retention vary by cohort?

```sql recent_cohorts
select *
from {{ "/queries/retention_cohort" }}
where cohort_week >= (
    select max(cohort_week) - interval 5 week
    from {{ "/queries/retention_cohort" }}
)
```

{% line_chart
    data="recent_cohorts"
    x="week_offset"
    y="avg(retention_rate)"
    series="cohort_week"
    y_fmt="pct"
    title="Retention by signup cohort (last 6 cohorts)"
/%}

**Retention** = the share of a signup cohort still active N weeks after signup
(`docs/analytics/metric_dictionary.md` §9). Each line is one signup cohort; the
chart shows the last six cohorts so the curves stay readable.

Week 0 is, by construction, 100%. The curves show the classic SaaS decay: an
initial drop (onboarding churn + dormancy), then a flattening - accounts that
survive the first weeks tend to stick around. Recent cohorts have shorter
curves because they haven't reached later offsets yet (the mart right-censors
them rather than dropping to zero).

### R2. Are activated users more likely to remain active?

{% bar_chart
    data="/queries/activation_vs_activity"
    x="is_activated"
    y="avg(active_weeks)"
    title="Average active weeks by activation status"
/%}

Activated accounts stay active materially longer than non-activated accounts -
activation is a leading indicator of ongoing engagement, not just a one-time
milestone.

---

## 5. Churn & Expansion - *what precedes churn, and who expands?*

### E1. What product behaviour precedes churn?

{% row %}
    {% bar_chart
        data="/queries/churn_by_usage"
        x="segment"
        y="avg_events"
        title="Lifetime events per account"
    /%}
    {% bar_chart
        data="/queries/churn_by_usage"
        x="segment"
        y="avg_active_days"
        title="Lifetime active days per account"
    /%}
{% /row %}

Churned accounts had **higher** lifetime usage than retained ones. This is a
**tenure artefact**, not a contradiction: churned accounts were older and
accumulated activity *before* leaving. The actionable churn signal is therefore
**not** raw volume - it is a *decline* in usage immediately preceding
cancellation (a trend-based signal, not a static level).

### E2. Which accounts expand?

{% table data="/queries/expansion_accounts" /%}

Expansion is visible at the account level: positive expansion MRR per
account-month (see `docs/analytics/metric_dictionary.md` §12).

### E3. How does product usage relate to MRR?

{% line_chart
    data="/queries/mrr_overview"
    x="mrr_month"
    y=["total_mrr", "expansion_mrr"]
    y_fmt="usd0"
    title="Monthly MRR and expansion MRR"
/%}

MRR stands at {% value data="/queries/mrr_overview" value="max(total_mrr)" fmt="usd0" /%}
in the latest month, with expansion MRR contributing in recent months.

### E4. How does the paid base evolve over time?

{% line_chart
    data="/queries/paid_base"
    x="day_date"
    y=["cum_converted", "cum_churned", "paid_accounts"]
    title="Paid base over time (converted / churned / net paid)"
/%}

**Paid base** counts accounts on a `pro` or `enterprise` plan. The chart shows
three curves: cumulative accounts that **ever** paid (`cum_converted`),
cumulative paid accounts that **churned** (`cum_churned`), and the difference -
accounts **currently paying** (`paid_accounts`). This is a *billing* view of
"active accounts" (who is paying right now), distinct from the usage-based DAU
in §D2.

