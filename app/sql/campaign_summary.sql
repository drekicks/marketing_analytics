with cmpgn_aud as 
(select 
cr.campaign_id,
cr.campaign_name,
cr.channel,
cr.start_date::date,
cr.end_date::date,
count(cr.customer_id) audience_size,
sum(cr.cmpgn_rvn) campaign_revenue,
sum(contact_cost + offer_cost) total_campaign_cost,
round(count(*) filter (where treatment_grp='TEST' and response_flg='Y' and cnvrsn_flg='Y')::numeric/COUNT(*) FILTER (WHERE treatment_grp='TEST'),2) test_cnvrsn_rate,
round(count(*) filter (where treatment_grp='CONTROL' and response_flg='Y' and cnvrsn_flg='Y')::numeric/COUNT(*) FILTER (WHERE treatment_grp='CONTROL'),2) control_cnvrsn_rate,
count(*) filter (where response_flg='Y' and cnvrsn_flg='Y') conversions
from campaign_results cr join customer_segment cs
	on cr.customer_id = cs.customer_id
group by 1,2,3,4,5
),-- select * from control_aud;,
full_fnl as 
(
select *, round(conversions::numeric/audience_size,2) conversion_rate, round(campaign_revenue/audience_size,2) revenue_per_customer, 
round(campaign_revenue/conversions,2) revenue_per_conversion,(test_cnvrsn_rate-control_cnvrsn_rate)*100 absolute_lift
from cmpgn_aud
) select * from full_fnl;


