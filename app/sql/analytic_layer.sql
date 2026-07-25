with analytic_layer as (select 
cr.customer_id,
cr.campaign_id,
cr.campaign_name,
cr.start_date::date,
cr.end_date::date,
cs.primary_segment,
cs.customer_tier,
cr.customer_segment,
cr.treatment_grp,
cr.cnvrsn_flg,
cr.cmpgn_rvn,
offer_cost,
contact_cost
from campaign_results cr join customer_segment cs
	on cr.customer_id = cs.customer_id
--where cr.campaign_name ='Summer Win Big Offer'
)
select *, offer_cost+contact_cost as total_cost from analytic_layer order by 1;

