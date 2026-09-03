---
title: Metrics reference
sidebar_position: 4
---

# Metrics reference

This page links each metric to its definition in
[`docs/analytics/metric_dictionary.md`](/docs/analytics/metric_dictionary.md).
The metric dictionary is the **single source of truth** for definitions - every
report page reads the same mart tables and references the same definitions.

| Metric | Mart source | Dictionary § |
|--------|-------------|--------------|
| New accounts / users | `fct_user_activation`, `fct_product_events` | §1, §2 |
| Activation rate | `fct_user_activation` | §3 |
| Time to activation | `fct_user_activation` | §4 |
| Onboarding funnel | `fct_user_journey` | §5 |
| DAU / WAU | `fct_user_daily_activity` | §6 |
| Feature adoption | `fct_feature_adoption` | §7 |
| Paid conversion | `fct_paid_conversion` | §8 |
| Engagement segment | `fct_product_events` | §8b |
| Retention | `fct_retention` | §9 |
| Churn | `fct_churn` | §10 |
| MRR | `fct_account_mrr` | §11 |
| Expansion MRR | `fct_account_mrr`, `fct_usage_expansion` | §12 |

## Semantic model

The relationship between entities, facts, and time semantics is documented in
[`docs/analytics/semantic_model.md`](/docs/analytics/semantic_model.md), and the
traceability chain (metric → source → process) in
[`docs/analytics/business_to_data_traceability.md`](/docs/analytics/business_to_data_traceability.md).
