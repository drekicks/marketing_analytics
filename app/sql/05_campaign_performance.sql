with rr as (select 
cr.campaign_name,
cr.customer_segment,
count(*) total_cntcts,
sum(cr.cmpgn_rvn) campaign_revenue,
sum(offer_cost) offer_cost,
sum(contact_cost) contact_cost,
count(*) filter (where response_flg='Y') total_rspns,
count(*) filter (where cnvrsn_flg='Y')total_cnvrsn,
COUNT(*) FILTER (WHERE treatment_grp='TEST') test_group,
count(*) filter (where treatment_grp='TEST' and response_flg='Y') test_rspn,
count(*) filter (where treatment_grp='TEST' and response_flg='Y' and cnvrsn_flg='Y') test_cnvrsn,
round(100 * count(*) filter (where treatment_grp='TEST' and response_flg='Y')/COUNT(*) FILTER (WHERE treatment_grp='TEST'),2)/100 test_respn_rt,
round(100 * count(*) filter (where treatment_grp='TEST' and response_flg='Y' and cnvrsn_flg='Y')/COUNT(*) FILTER (WHERE treatment_grp='TEST'),2)/100 test_cnvrsn_rt,
sum(cr.cmpgn_rvn) FILTER (WHERE treatment_grp='TEST') test_campaign_revenue,
count(*) filter (where treatment_grp='CONTROL') control_group,
count(*) filter (where treatment_grp='CONTROL' and response_flg='Y') control_rspn,
count(*) filter (where treatment_grp='CONTROL' and response_flg='Y' and cnvrsn_flg='Y') control_cnvrsn,
round(100 * count(*) filter (where treatment_grp='CONTROL' and response_flg='Y')/COUNT(*) FILTER (WHERE treatment_grp='CONTROL'),2)/100 cntrl_respn_rt,
round(100 * count(*) filter (where treatment_grp='CONTROL' and response_flg='Y' and cnvrsn_flg='Y')/COUNT(*) FILTER (WHERE treatment_grp='CONTROL'),2)/100 cntrl_cnvrsn_rt,
sum(cr.cmpgn_rvn) FILTER (WHERE treatment_grp='CONTROL') control_campaign_revenue
from campaign_results cr
group by 1,2
)
select * from rr;

select * from campaign_results cr 




