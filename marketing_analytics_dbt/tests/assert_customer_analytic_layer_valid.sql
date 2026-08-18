select *
from {{ ref('customer_analytic_layer') }}
where
      (treatment_group = 'CONTROL'
       and (contact_cost <> 0 or offer_cost <> 0))

   or (treatment_group = 'TEST'
       and contact_cost <= 0)

   or (treatment_group = 'TEST'
       and conversion_flag <> 'Y'
       and offer_cost <> 0)

   or (treatment_group = 'TEST'
       and conversion_flag = 'Y'
       and offer_cost <= 0)