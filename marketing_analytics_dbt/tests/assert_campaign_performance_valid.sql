select *
from {{ ref('campaign_performance_summary') }}
where conversions > audience_size
   or campaign_revenue < 0
   or total_campaign_cost < 0