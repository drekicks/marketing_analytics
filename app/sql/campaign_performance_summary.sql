--need to add revenue to Winback and Churn and reduce costs.
with control_aud as 
(select 
cr.campaign_id,
cr.campaign_name,
cr.customer_segment,
cr.start_date::date,
cr.end_date::date,
count(customer_id) control_audience,
sum(cr.cmpgn_rvn) control_revenue,
count(*) filter (where treatment_grp='CONTROL' and response_flg='Y' and cnvrsn_flg='Y') control_cnvrsn
from campaign_results cr
where --cr.campaign_name ='Summer Win Big Offer' and 
treatment_grp='CONTROL'
group by 1,2,3,4,5
),
control_fnl as 
(
select *, round(100*control_cnvrsn/control_audience,2)/100 control_conversion_rate, round(control_revenue/control_audience,2) control_rpc
from control_aud
),
test_aud as
(select 
cr.campaign_id,
cr.campaign_name,
cr.customer_segment,
count(customer_id) test_audience,
sum(cr.cmpgn_rvn) test_revenue,
sum(offer_cost) offer_cost,
sum(contact_cost) contact_cost,
sum(contact_cost + offer_cost) total_cmpgn_cost,
count(*) filter (where treatment_grp='TEST' and response_flg='Y' and cnvrsn_flg='Y') test_cnvrsn
from campaign_results cr
where --cr.campaign_name ='Summer Win Big Offer' and 
treatment_grp='TEST'
group by 1,2,3
),
test_fnl as
(
select *, round(100*test_cnvrsn/test_audience,2)/100 test_conversion_rate,round(test_revenue/test_audience,2) test_rpc
from test_aud
),
combined as
(select c.*, test_audience, test_revenue, test_cnvrsn, test_conversion_rate, test_rpc, total_cmpgn_cost, offer_cost, contact_cost from control_fnl c join test_fnl t
	on c.campaign_id = t.campaign_id
	and c.customer_segment = t.customer_segment
),
c2 as 
(select *, to_char((test_conversion_rate-control_conversion_rate)* 100,'FM999990.0')||' percentage points' absolute_lift, control_rpc*test_audience expct_rvn, test_revenue-(control_rpc*test_audience) incremental_rev from combined
), c3 as
(select *, round((incremental_rev - total_cmpgn_cost)/total_cmpgn_cost,2) as marketing_roi,
round((test_conversion_rate-control_conversion_rate) * test_audience,0)::integer incremental_conversions, 
test_revenue + control_revenue as campaign_revenue, 
(test_cnvrsn + control_cnvrsn)::integer as campaign_conversions
from c2) select *, round(campaign_revenue/campaign_conversions,2) campaign_rpc from c3 order by 1;


