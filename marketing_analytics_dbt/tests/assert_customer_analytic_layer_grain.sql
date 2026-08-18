select
    customer_id,
    campaign_id,
    count(*) as row_count
from {{ ref('customer_analytic_layer') }}
group by
    customer_id,
    campaign_id
having count(*) > 1