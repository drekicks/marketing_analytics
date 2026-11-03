-- One-time setup: raw campaign goals table in Neon (replaces the dbt seed
-- marketing_analytics_dbt/seeds/campaign_goals.csv).
-- campaign_generation.py writes one row here for every campaign it creates;
-- dbt model marts/campaign_goals.sql exposes it as dbt_dev_analytics.campaign_goals.

create table if not exists public.campaign_goals (
    campaign_id    varchar(20)    primary key,
    campaign_name  varchar(75)    not null,
    campaign_goal  varchar(100)   not null,
    offer          varchar(50)    not null,
    channel        varchar(15)    not null,
    duration       varchar(20)    not null,
    budget         numeric(12, 2) not null,
    target_kpi     varchar(50)    not null,
    secondary_kpi  varchar(50),
    audience       varchar(50)    not null
);

-- Rows from the former seed file.
insert into public.campaign_goals
    (campaign_id, campaign_name, campaign_goal, offer, channel, duration, budget, target_kpi, secondary_kpi, audience)
values
    ('CMP-2026-003', 'Summer Win Big Offer',   'Acquire new customers', '15% off', 'Email',      '30 days', 1000, 'Incremental Conversions', 'Marketing ROI',        'New'),
    ('CMP-2025-002', 'Summer Retention Offer', 'Retain Customers',      '20% off', 'Paid Media', '30 days', 1500, 'Absolute Lift',           'Test Conversion Rate', 'Existing Customers'),
    ('CMP-2026-004', 'Spring Reactivation TM', 'Increase Revenue',      '5% off',  'Outbound',   '60 days', 1200, 'Campaign Revenue',        'Marketing ROI',        'Existing Customers')
on conflict (campaign_id) do nothing;
