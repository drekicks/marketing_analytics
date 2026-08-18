select
    campaign_id,
    count(*) as row_count
from {{ ref('campaign_performance_summary') }}
group by campaign_id
having count(*) > 1