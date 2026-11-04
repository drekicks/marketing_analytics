{# Campaign-level incremental measures: the TEST/CONTROL split covers the whole audience,
   and incremental conversions can't exceed the TEST audience. #}
select *
from {{ ref('campaign_performance_summary') }}
where test_audience + control_audience <> audience_size
   or abs(incremental_conversions) > test_audience
