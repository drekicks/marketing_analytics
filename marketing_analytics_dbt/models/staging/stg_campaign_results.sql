select
    customer_id,
    customer_segment,
    campaign_id,
    campaign_name,
    treatment_grp as treatment_group,
    contacted_flg as contacted_flag,
    response_flg as response_flag,
    cnvrsn_flg as conversion_flag,
    cmpgn_rvn as campaign_revenue,
    contact_cost,
    offer_cost,
    start_date,
    end_date,
    channel
from {{ source('dvdrental', 'campaign_results') }}