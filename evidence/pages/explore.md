---
title: Explore the data
sidebar_position: 2
---

# Explore the data

Raw views over the marts, grouped by business-question area. Every chart reads
the same SQL files used by the report — the same SQL can be pasted into
Metabase.

## Overview KPIs

{% row %}
    {% big_value data="/queries/kpis" value="total_accounts" fmt="num0" title="Total accounts" /%}
    {% big_value data="/queries/kpis" value="activation_rate" fmt="pct1" title="Activation rate" /%}
    {% big_value data="/queries/kpis" value="paid_conversion_rate" fmt="pct1" title="Paid conversion" /%}
    {% big_value data="/queries/kpis" value="latest_month_mrr" fmt="usd0" title="Latest MRR" /%}
{% /row %}

{% table data="/queries/kpis" /%}

## Activation

{% line_chart
    data="/queries/activation_rate"
    x="cohort"
    y="activation_rate"
    y_fmt="pct"
    title="Activation rate by signup week"
/%}

{% bar_chart
    data="/queries/time_to_activation_distribution"
    x="time_to_activation_days"
    y="accounts"
    title="Time-to-activation distribution"
/%}

{% table
    data="/queries/activation_by_country_plan"
    title="Activation rate by country & plan (star-schema join demo)"
/%}

## Adoption

{% line_chart
    data="/queries/feature_adoption_trend"
    x="week"
    y="adoption_rate"
    series="feature_code"
    y_fmt="pct"
    title="Feature adoption over time"
/%}

## Conversion

{% table data="/queries/conversion_by_engagement" /%}

## Retention

{% table data="/queries/retention_cohort" /%}

## Churn & expansion

{% line_chart
    data="/queries/churn_overview"
    x="month"
    y="churn_rate"
    y_fmt="pct"
    title="Monthly churn rate"
/%}

## Usage vs MRR

{% scatter_chart
    data="/queries/usage_vs_mrr"
    x="total_events"
    y="mrr"
    series="is_expanding"
    title="Usage vs MRR (account-month)"
/%}
