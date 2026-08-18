select *
from {{ ref('campaign_performance_summary') }}
where test_conversion_rate < 0
   or test_conversion_rate > 1
   or control_conversion_rate < 0
   or control_conversion_rate > 1