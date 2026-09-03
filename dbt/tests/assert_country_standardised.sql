-- assert_country_standardised.sql
-- DQ scenario 6: standardisation (country).
-- Source countries were messy (US/USA/United States, Canada, UK...). Staging
-- must map them to ISO2. This asserts no non-ISO2 country codes remain.

select *
from {{ ref('stg_crm_companies') }}
where country not in ('US', 'CA', 'GB')
