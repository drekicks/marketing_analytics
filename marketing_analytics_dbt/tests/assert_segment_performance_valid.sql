select *
from {{ ref('segment_performance_summary') }}
where test_conversions > test_audience
   or control_conversions > control_audience
   or campaign_conversions > segment_audience
   or test_revenue < 0
   or control_revenue < 0
   or campaign_revenue < 0
   or total_campaign_cost < 0