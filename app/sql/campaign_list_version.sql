-- One cheap row that changes when a campaign is added (checked about once a minute).
select
    count(*) as campaign_count,
    max(campaign_id) as latest_campaign_id,
    max(start_date) as latest_start_date
from {{analytics_schema}}.campaign_performance_summary;
