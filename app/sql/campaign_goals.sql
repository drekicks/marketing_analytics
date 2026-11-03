-- Campaign goals, budget and KPIs (dbt seed: marketing_analytics_dbt/seeds/campaign_goals.csv).
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
from {{analytics_schema}}.campaign_goals;
