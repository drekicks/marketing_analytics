with cmpgn_trtmnt as (select 
cr.campaign_id,
cr.campaign_name,
cr.customer_segment,
cr.treatment_grp,
cr.start_date::date,
cr.end_date::date,
sum(cr.cmpgn_rvn) cmpgn_rvn,
sum(offer_cost + contact_cost) total_cost,
count(distinct customer_id) audience,
count(*) filter (where response_flg='Y' and cnvrsn_flg='Y') conversions
from campaign_results cr 
where cr.campaign_name ='Summer Win Big Offer'
group by 1,2,3,4,5,6
)
select *, round(cmpgn_rvn/audience,2) rvn_per_customer, round(cmpgn_rvn/conversions,2) rvn_per_converter from  cmpgn_trtmnt order by 3,4;