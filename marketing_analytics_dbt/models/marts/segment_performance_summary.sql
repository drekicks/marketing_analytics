with control_aud as
(select
    campaign_id,
    campaign_name,
    customer_segment,
    start_date,
    end_date,
    count(customer_id) control_audience,
    sum(campaign_revenue) control_revenue,
    count(
            case
                when treatment_group = 'CONTROL' and response_flag='Y' and conversion_flag='Y'
                then 1
            end
    ) as control_conversions
{#    count(*) filter (where treatment_group='CONTROL' and response_flag='Y' and conversion_flag='Y') control_conversions#}
from {{ ref('stg_campaign_results') }}
where treatment_group='CONTROL'
group by campaign_id,campaign_name,customer_segment,start_date,end_date
),
control_fnl as
(
select *,
       round(control_conversions::numeric/nullif(control_audience,0),2) control_conversion_rate,
       round(control_revenue/nullif(control_audience,0),2) control_revenue_per_customer
from control_aud
),
test_aud as
(select
    campaign_id,
    campaign_name,
    customer_segment,
    count(customer_id) test_audience,
    sum(campaign_revenue) test_revenue,
    sum(offer_cost) offer_cost,
    sum(contact_cost) contact_cost,
    sum(contact_cost + offer_cost) total_campaign_cost,
    count(
            case
                when treatment_group = 'TEST' and response_flag='Y' and conversion_flag='Y'
                then 1
            end
    ) as test_conversions
{#    count(*) filter (where treatment_group='TEST' and response_flag='Y' and conversion_flag='Y') test_conversions#}
from {{ ref('stg_campaign_results') }}
where treatment_group='TEST'
group by campaign_id,campaign_name,customer_segment
),
test_fnl as
(
select *,
       round(test_conversions::numeric/nullif(test_audience,0),2) test_conversion_rate,
       round(test_revenue/nullif(test_audience,0),2) test_revenue_per_customer
from test_aud
),
combined as
(select c.*,
        test_audience,
        test_revenue,
        test_conversions,
        test_conversion_rate,
        test_revenue_per_customer,
        total_campaign_cost,
        offer_cost,
        contact_cost
 from control_fnl c join test_fnl t
	on c.campaign_id = t.campaign_id
	and c.customer_segment = t.customer_segment
),
c2 as
(
select *,
       (test_conversion_rate-control_conversion_rate)*100 absolute_lift,
       control_revenue_per_customer*test_audience expcted_revenue,
       test_revenue-(control_revenue_per_customer*test_audience) incremental_revenue
from combined
), c3 as
(select *,
        round((incremental_revenue - total_campaign_cost)/nullif(total_campaign_cost,0),2) as marketing_roi,
        round((test_conversion_rate-control_conversion_rate) * test_audience,0)::integer incremental_conversions,
        test_revenue + control_revenue as campaign_revenue,
        (test_conversions + control_conversions)::integer as campaign_conversions,
        (test_audience + control_audience) segment_audience
from c2
) select *,
         round(campaign_revenue/nullif(campaign_conversions,0),2) segment_revenue_per_conversion,
         round(campaign_conversions::numeric/nullif(segment_audience,0),2) segment_conversion_rate
from c3