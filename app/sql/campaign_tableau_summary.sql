with cmpgn_trtmnt as (select 
cr.campaign_id,
cr.campaign_name,
cr.customer_segment,
cs.customer_tier,
cs.primary_segment,
cr.treatment_grp,
cs.engagement_segment,
category_engagement_tier,
cr.start_date::date,
cr.end_date::date,
sum(cr.cmpgn_rvn) cmpgn_rvn,
sum(offer_cost + contact_cost) total_cost,
count(distinct cr.customer_id) audience,
count(*) filter (where response_flg='Y' and cnvrsn_flg='Y') conversions
from campaign_results cr join customer_segment cs
on cr.customer_id = cs.customer_id
group by 1,2,3,4,5,6,7,8,9,10
)select *, round(cmpgn_rvn/audience,2) rvn_per_customer, case when conversions=0 then 0 else round(cmpgn_rvn/conversions,2) end rvn_per_converter 
from  cmpgn_trtmnt order by 1,3,4;
