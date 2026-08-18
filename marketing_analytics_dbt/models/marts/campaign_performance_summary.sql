with cmpgn_prfrmnc as
(
select
    campaign_id,
    campaign_name,
    channel,
    start_date::date as start_date,
    end_date::date as end_date,
    count(customer_id) as audience_size,
    sum(campaign_revenue) as campaign_revenue,
    sum(contact_cost + offer_cost) as total_campaign_cost,
    round(
            count(*) filter (
                where treatment_group='TEST'
                and response_flag='Y'
                and conversion_flag='Y')::numeric
                /
                nullif(
                COUNT(*) FILTER (
                WHERE treatment_group='TEST'),
                0
                ),
            2
        ) as test_conversion_rate,
    round(
            count(*) filter (
                where treatment_group='CONTROL'
                and response_flag='Y'
                and conversion_flag='Y')::numeric
                /
                nullif(
                COUNT(*) FILTER (
                WHERE treatment_group='CONTROL'),
                0
                ),
            2
        ) as control_conversion_rate,
    count(*) filter (
        where response_flag='Y' and conversion_flag='Y'
        ) as conversions
from {{ ref('stg_campaign_results') }}
group by
    campaign_id,
    campaign_name,
    channel,
    start_date::date,
    end_date::date
),
full_fnl as
(
select *,
    round(conversions::numeric/nullif(audience_size, 0),2) as conversion_rate,
    round(campaign_revenue/nullif(audience_size, 0),2) as revenue_per_customer,
    round(campaign_revenue/nullif(conversions, 0),2) as revenue_per_conversion,
    (test_conversion_rate-control_conversion_rate)*100 as absolute_lift
from cmpgn_prfrmnc
) select * from full_fnl