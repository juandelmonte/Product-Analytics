---
title: Dimensions
sidebar_position: 3
---

# Dimensions

One fact, sliced many ways. Every chart below is a **star-schema join**: a fact
(`fct_*`) joined to the conformed `dim_accounts` by `account_id`. This is the
reason the dimensions exist — the same activation/conversion/MRR facts, cut by
plan, country, size, and industry.

## Activation by dimension

{% row %}
    {% bar_chart
        data="/queries/activation_by_plan"
        x="plan"
        y="activation_rate"
        y_fmt="pct"
        title="Activation rate by plan"
    /%}
    {% bar_chart
        data="/queries/activation_by_country"
        x="country"
        y="activation_rate"
        y_fmt="pct"
        title="Activation rate by country"
    /%}
{% /row %}

{% row %}
    {% bar_chart
        data="/queries/activation_by_size"
        x="company_size"
        y="activation_rate"
        y_fmt="pct"
        title="Activation rate by company size"
    /%}
    {% bar_chart
        data="/queries/activation_by_industry"
        x="industry"
        y="activation_rate"
        y_fmt="pct"
        title="Activation rate by industry"
    /%}
{% /row %}

## Conversion by dimension

{% row %}
    {% bar_chart
        data="/queries/conversion_by_country"
        x="country"
        y="conversion_rate"
        y_fmt="pct"
        title="Paid conversion by country"
    /%}
    {% bar_chart
        data="/queries/conversion_by_industry"
        x="industry"
        y="conversion_rate"
        y_fmt="pct"
        title="Paid conversion by industry"
    /%}
{% /row %}

## Revenue by dimension

{% row %}
    {% bar_chart
        data="/queries/mrr_by_country"
        x="country"
        y="mrr"
        y_fmt="usd0"
        title="Latest-month MRR by country"
    /%}
    {% bar_chart
        data="/queries/mrr_by_size"
        x="company_size"
        y="mrr"
        y_fmt="usd0"
        title="Latest-month MRR by company size"
    /%}
{% /row %}

{% table
    data="/queries/activation_by_country_plan"
    title="Activation rate by country & plan (two dimensions)"
/%}
