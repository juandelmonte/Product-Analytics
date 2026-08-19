# Identity Resolution

The three source systems use **different identifiers** for the same real-world
account. There is no universal ID. The canonical mapping is assembled in dbt
(`int_identity_mapping`), not in the source systems.

## Identifier namespaces

| System | Entity | Identifier |
|--------|--------|------------|
| Product analytics | account | `account_id` (event `account_id`, accounts table) |
| Product analytics | user | `user_id` (`distinct_id` on events) |
| CRM | company | `company_id` |
| CRM | contact | `contact_id` |
| CRM | deal | `deal_id` |
| Billing | customer | `customer_id` |
| Billing | subscription | `subscription_id` |

## Canonical mapping

The canonical key is the **product `account_id`** (the app is the first system
to see an account). Two edges connect the other systems to it:

```
billing_customer.customer_id  ──►  account.account_id   (via billing_customer.account_ref / email)
crm_company.company_id        ──►  account.account_id   (via crm_company.account_ref / email)
```

The simulation stores an explicit **`account_ref`** linkage on the billing
customer and CRM company rows (a source-specific field that mirrors how a real
integration would map accounts). The dbt model `int_identity_mapping` joins on
these references and builds one row per canonical account with all four IDs.

## Mapping ownership

- The **product** system owns the account's existence (`account_id`).
- The **CRM** system owns the sales view (`company_id`, `contact_id`, `deal_id`).
- The **billing** system owns the money view (`customer_id`, `subscription_id`).

## Edge cases handled

| Case | Behaviour | Handling |
|------|-----------|----------|
| Unknown identity | A CRM/billing row has no `account_ref` yet | Left as `null` in mapping; surfaced as `identity_missing` flag |
| Missing association | A contact has no company initially | `company_id` is nullable; filled later |
| Identity change | A user is re-identified (distinct_id change) | `user_signup` + events carry `user_id`; mapping preserves the canonical user |
| Cross-system joins | account ↔ billing ↔ CRM | Always go through `int_identity_mapping`, never direct |
