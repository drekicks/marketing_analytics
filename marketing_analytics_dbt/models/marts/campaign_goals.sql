{#
  Planned objectives, offer, channel, budget and KPIs per campaign.
  Was a dbt seed; now read from raw public.campaign_goals, which the weekly
  campaign generator writes. Keeps the relation name the app queries
  ({{analytics_schema}}.campaign_goals).
#}
select
    campaign_id,
    campaign_name,
    campaign_goal,
    offer,
    channel,
    duration,
    budget,
    target_kpi,
    secondary_kpi,
    audience
from {{ source('dvdrental', 'campaign_goals') }}
