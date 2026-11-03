-- Campaign goals, budget and KPIs (dbt model marts/campaign_goals.sql, built from raw public.campaign_goals).
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
