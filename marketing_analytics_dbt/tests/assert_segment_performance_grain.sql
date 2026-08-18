select
    campaign_id,
    customer_segment,
    count(*) as row_count
from {{ ref('segment_performance_summary') }}
group by
    campaign_id,
    customer_segment
having count(*) > 1