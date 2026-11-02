-- One row per campaign, from the campaign mart (previously read raw campaign_results).
select
    campaign_id,
    campaign_name,
    start_date as campaign_start_date,
    channel
from {{analytics_schema}}.campaign_performance_summary
order by campaign_start_date;
